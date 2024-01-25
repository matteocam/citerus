import re
import sys
import os
import pickle
import time
import pathlib
import git  
from git import RemoteProgress

import shutil

from rich.text import Text
from rich import print

from . import citeruslogo


max_title_size = 75

core_fields_db = ("tag", "howpublished", "publisher", "year", "title", "author")
core_fields_table = ("tag", "where", "year", "title", "author")

CITERUS_ROOT = os.path.expanduser('~') + "/.citerus"
CRYPTOBIB_ROOT = CITERUS_ROOT + '/cryptobib'
cryptobibdir = CRYPTOBIB_ROOT + "/crypto.bib"
path_citme_db = CITERUS_ROOT + "/citerusdb"


def cleanup():
    try:
        shutil.rmtree(CITERUS_ROOT)
    except OSError as e:
        #print("Error: %s - %s." % (e.filename, e.strerror))
        pass # Silent (redundant cleanups do not need to be announced)

def search_bib(db, args):
    titles = args.t
    authors = args.a

    fix_case = lambda x: x.lower() if args.case_insensitive else x

    titles = [fix_case(t) for t in titles]
    authors = [fix_case(a) for a in authors]

    aggr_t = any if args.or_title else all
    aggr_a = any if args.or_author else all

    t_lambda = lambda o: aggr_t(t in fix_case(o["title"]) for t in titles) 
    a_lambda = lambda o: aggr_a(a in fix_case(o.get("author", "")) for a in authors)
    y_lambda = lambda o: args.y in o.get("year", "")

    is_match = lambda o: t_lambda(o) and a_lambda(o) and y_lambda(o) # search title pattern and author pattern and year

    #is_match = lambda o: t in o["title"].lower() and a in o.get("author", "").lower()
    return filter(is_match, db)

def replace_multiple_spaces(text):
    pattern = '\s+'
    new_text = re.sub(pattern, ' ', text)
    return new_text

def stripKey(item):
    cnt = item
    cnt = cnt.lstrip()
    if len(cnt) == 0 or '=' not in cnt:
        return None, None
    
    i = 0
    while cnt[i] != ' ':
        i +=1
    keyword = cnt[:i]
    cnt = cnt[i:]

    cnt = cnt.lstrip()
    cnt = cnt[len('='):] # strips '='
    cnt.strip()
    cnt = replace_multiple_spaces(cnt)
    
    return keyword, cnt.strip()


class CloneProgress(RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        if cur_count % 8 == 0: # reduces number of messages
            if message:
                print(message)

def ensure_cryptodb_exists(file_path):
    there_is_bib_file = os.path.isfile(file_path)

    if there_is_bib_file:
        return
    
    # Make sure root directory exists
    pathlib.Path(CITERUS_ROOT).mkdir(parents=True, exist_ok=True)

    print("First time that citerus is running! Just some quick one-time housekeeping:")
    print('Cloning cryptobib (this may take a few seconds)...')
    git.Repo.clone_from('https://github.com/cryptobib/export.git', CRYPTOBIB_ROOT, branch='master', progress=CloneProgress())
    print()


def parse_cryptodb(file_path):
    citeruslogo.print_logo()

    ensure_cryptodb_exists(file_path)
    # Regular expression to match the objects
    
    pattern = r"@(\w+)\{(.+),([\s\S]*?\n)\}"

    print("Building index...")

    # Read the file content
    with open(file_path, 'r') as file:
        content = file.read()

    # Find all matches
    matches = re.findall(pattern, content)

    # Process matches
    objects = []
    for obj_type, obj_tag, obj_content in matches:
        obj = {
            'type': obj_type,
            'tag' :obj_tag
        }

        content_items = obj_content.split(',\n')
        for item in content_items:
            k,v = stripKey(item)
            if k in core_fields_db: # Keep only fields we are using
                obj[k] = v
        
        if "title" in obj.keys():
            objects.append(obj)
            
    print("Done.")
    return objects

def cache_parsed_db(db):
    with open(path_citme_db, 'wb') as outp:
        pickle.dump(db, outp, pickle.HIGHEST_PROTOCOL)

def load_from_cache():
    with open(path_citme_db, 'rb') as inp:
        db = pickle.load(inp)
        return db

def load_parsed_cryptodb(cryptobibdir):
    there_is_cache_file = os.path.isfile(path_citme_db)
    if not there_is_cache_file:
        parsed_db = parse_cryptodb(cryptobibdir)
        cache_parsed_db(parsed_db)
        return parsed_db
    else:
        return load_from_cache()


def make_bold(s, w):
    pattern = re.compile(r'\b%s\b' % re.escape(w), re.IGNORECASE)
    return re.sub(pattern, lambda m: f'[bold]{m.group(0)}[/bold]', s)

def remove_clutter_title_author(s):
    # remove quotation marks
    if s[0] == '"':
        s = s[1:]
    if s[-1] == '"':
        s = s[:-1]
    
    s = s.replace('{', '')
    s = s.replace('}', '')
    return s

def prettify_title_author(s, patterns):
    text_s = Text(s)
    text_s.highlight_words(patterns, style="bold green", case_sensitive=False)
    return text_s

def initial_whole_surname(full_name):
    names = full_name.split(' ')
    firstnames, surname = names[:-1], names[-1]
    # Each name becomes an initial (e.g, 'Karl' -> 'K.')
    initials = [fn[0] + '.' for fn in firstnames]
    names = initials + [surname]
    return ' '.join(names)


def shorten_author_list(author):
    author_list = author.split(' and ')
    author_list = map(initial_whole_surname, author_list)
    return ', '.join(author_list)

def shorten_title_if_too_long(title):
    if len(title) > max_title_size:
        return title[:max_title_size-5]+'[...]'
    else:
        return title
    
def process_results_for_table(res, args):
    fields = core_fields_table
    ROWS = [ fields ]

    titlepatterns = args.t
    authorpatterns = args.a

    for r in res: 
        l = []
        for f in fields:
            if f == "title":
                title = shorten_title_if_too_long(remove_clutter_title_author(r[f]))
                l.append(prettify_title_author(title, titlepatterns))
            elif f == "author":
                author = "N/A" # Default case
                if 'author' in r.keys():
                    author = shorten_author_list(remove_clutter_title_author(r[f]))
                l.append(prettify_title_author(author, authorpatterns))
            elif f == "where":
                if "howpublished" in r.keys():
                    l.append(Text("eprint"))
                elif "publisher" in r.keys():
                    l.append(Text(r["publisher"][:9])) # trimmed publisher
                else: # tech report
                    l.append(Text("techrep"))
            elif f == "year":
                yr = r.get("year", "N/A")
                l.append(Text(yr))
            else:
                l.append(Text(r[f]))
        t = tuple(l)
        ROWS.append(t)

    return ROWS

def get_rows(args):
    # Parse the file
    bibdb = load_parsed_cryptodb(cryptobibdir)

    
    res = search_bib(bibdb, args)

    return process_results_for_table(res, args)
