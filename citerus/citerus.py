#!/usr/bin/python3

from textual.app import App, ComposeResult
from textual.widgets import DataTable
from rich.text import Text
from rich import print
from rich.panel import Panel

import argparse
import sys
import pyperclip

from . import cryptodbreader

from . import citeruslogo


# MAX number of rows visualized
CAP_RESULTS = 70

PROG_NAME = 'citerus'

def get_tag_from_row(row_data):
    return row_data[1].plain

def col_width(colname):
    if colname == 'title':
        return cryptodbreader.max_title_size
    else:
        return None

class CitTableApp(App[str]):
    ROWS = None
    args = None

    def compose(self) -> ComposeResult:
        yield DataTable()

    def get_table_title(self):
        patternstyle = "underline"

        t_sep = '|' if self.args.or_title else '&'
        a_sep = '|' if self.args.or_author else '&'

        s = Text()
        if len(self.args.t) > 0:
            s.append('Titles containing ')
            for i, t in enumerate(self.args.t):
                s.append('"')
                s.append(t, patternstyle)
                s.append('"')
                if i < len(self.args.t)-1:
                    s.append(' %s ' % t_sep)
            if len(self.args.a) > 0:
                s.append(' - ')
        
        #s = Text.assemble('Titles containing "', (self.args.t, patternstyle), '"')
        if len(self.args.a) > 0:
            s.append('Authors containing ')
            for i, a in enumerate(self.args.a):
                s.append('"')
                s.append(a, patternstyle)
                s.append('"')
                if i < len(self.args.a)-1:
                    s.append(' %s ' % a_sep)
        return s

    def helper_text(self):
        s = Text("Use ")
        s.append("Enter", "underline")
        s.append(" to select, ")
        s.append("up", "underline")
        s.append("/")
        s.append("down", "underline")
        s.append(" to navigate, ")
        s.append("q", "underline")
        s.append(" when done.")
        
        
        return s

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.styles.height = "100%"
        table.styles.width = "100%"
        table.styles.border = ("heavy", "orange")
        table.border_title = self.get_table_title()
        table.styles.border_title_align = "center"
        table.styles.padding = 1

        table.border_subtitle = self.helper_text()
        table.styles.border_subtitle_align = "left"



        table.cursor_type = "row"
        table.zebra_stripes = True
        self.colkeys = [table.add_column(col, width=col_width(col)) for col in self.ROWS[0]]
        table.add_rows(self.ROWS[1:])

        self.saved_tags = []

    def toggle_saved_tag(self, tag):
        if tag not in self.saved_tags:
            self.saved_tags.append(tag)
        else:
            self.saved_tags.remove(tag)

    def update_row_X(self, row_key, tag):
        table = self.query_one(DataTable)

        if tag in self.saved_tags:
            table.update_cell(row_key, self.colkeys[0], "X")
            table.update_cell(row_key, self.colkeys[1], Text(tag, style = "reverse"))
        else:
            table.update_cell(row_key, self.colkeys[0], " ")
            table.update_cell(row_key, self.colkeys[1], Text(tag, style = ""))


    def on_data_table_row_selected(self) -> None:
        table = self.query_one(DataTable)

        # Get the keys for the row and column under the cursor.
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        # Supply the row key to `remove_row` to delete the row.
        row_data = table.get_row(row_key)

        tag = get_tag_from_row(row_data)

        self.toggle_saved_tag(tag)
        self.update_row_X(row_key, tag)

        #self.exit(row_data[0])

    def key_q(self) -> None:
        joined_cits = ",".join(self.saved_tags)
        self.exit('\cite{' + joined_cits + '}')



def trim_augment_rows(ROWS):
    # Trim rows
    if len(ROWS) > CAP_RESULTS+1:
        ROWS = ROWS[:CAP_RESULTS+1]
        print("Warning: not all results were shown. There were too many.")

    # Add dummy first col 
    oldrows = ROWS
    ROWS = [(' ',) + oldrows[0]]
    for row in oldrows[1:]:
        ROWS.append(('',) + row )
    
    return ROWS

def argparse_setup():

    
    example = "Examples:\n  citerus mpc round\t\t# search the string \"mpc\" in title\n  citerus SNARK -a fiore\t# search the string \"SNARK\" in titles and \"fiore\" in authors\n  citerus -a groth -y 2016\t# search for Groth16"
    description_msg = "  Citerus retrieves your citations.\n  It searches for citations in cryptobib and automatically copies the LaTeX handle into your clipboard.\n\n%s" % example
    usage_msg = 'citerus [OPTIONS] [TITLE_PATT ...] [-a AUTHOR_PATT [AUTHOR_PATT ...]]'
    parser = argparse.ArgumentParser(prog=PROG_NAME, exit_on_error=False, formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=description_msg, usage = usage_msg)


    group_std = parser.add_argument_group('Search pattern arguments')


    group_std.add_argument('t', nargs='*', default=[], metavar="TITLE_PATT", help = "Patterns to search in title field (one or more)")
    group_std.add_argument('-a', action='extend', nargs = '+', default=[], metavar="AUTHOR_PATT", help = "Patterns to search in author field")

    group_std.add_argument('-y', action='store', default='', dest='y', metavar='YEAR', help='Restrict search to YEAR')

    group_std.add_argument('-s', action='store_false', dest='case_insensitive',  help="Case-sensitive search (default: case insensitive)")

    group_std.add_argument('--or-title', action='store_true', dest='or_title',  help="OR of title patterns (default: AND)")
    group_std.add_argument('--or-author', action='store_true', dest='or_author',  help="OR of author patterns (default: AND)")



    group_adm = parser.add_argument_group('Other arguments')
    group_adm.add_argument('--cleanup', action='store_true', dest='cleanup', help="Cleanup DB files (reset cryptobib and index)")
    group_adm.add_argument('--logo', action='store_true', dest='logo_help', help="Print logo together with help")


    return parser

def main():
    parser = argparse_setup()

    if len(sys.argv) == 1: # No arguments passed
        print(Text.assemble(("\nPlease provide at least one argument as a search query.", "bold"), ("\nExample: ", "bold"), "citerus mpc optimal"))
        print()
        parser.print_usage()
        sys.exit(0)

    
    args = parser.parse_args()  
    
    if args.cleanup:
        cryptodbreader.cleanup()
        sys.exit(0)

    if args.logo_help:
        citeruslogo.print_logo()
        print()
        parser.print_help()
        sys.exit(0)


    if len(args.a)+len(args.t) == 0:
        parser.print_help()
        sys.exit(1)


    # TODO: add options to search by handle?

    ROWS = cryptodbreader.get_rows(args)

    ROWS = trim_augment_rows(ROWS)

    #print(ROWS)

    app = CitTableApp()
    app.ROWS = ROWS
    app.args = args
    
    citations = app.run()
    not_empty_list = citations != '\cite{}'

    if not_empty_list:
        pyperclip.copy(citations)
        print(Text.assemble('Copied \'', (citations, "italic magenta"), '\' in clipboard.'))

    
if __name__ == "__main__":
    main()