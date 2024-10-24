venues = {
    "ACISP": "ACISP",
    "ACM CCS": "CCS",
    "ACNS": "ACNS",
    "AFRICACRYPT": "AFRICACRYPT",
    "ASIACCS": "ASIACCS",
    "ASIACRYPT": "AC",
    "CANS": "CANS",
    "CHES": "CHES",
    "COSADE": "COSADE",
    "CQRE": "CQRE",
    "CRYPTO": "C",
    "CSF": "CSF",
    "CT-RSA": "RSA",
    "DCC": "DCC",
    "EPRINT": "EPRINT",
    "ESORICS": "ESORICS",
    "EUROCRYPT": "EC",
    "FC": "FC",
    "FCW": "FCW",
    "FOCS": "FOCS",
    "FSE": "FSE",
    "ICALP": "ICALP",
    "ICICS": "ICICS",
    "ICISC": "ICISC",
    "ICITS": "ICITS",
    "IEEE SP": "SP",
    "IMA": "IMA",
    "INDOCRYPT": "INDOCRYPT",
    "ISC": "ISC",
    "ITC": "ITC",
    "ITCS": "ITCS",
    "IWSEC": "IWSEC",
    "JC": "JC",
    "JCEng": "JCEng",
    "LATIN": "LATIN",
    "LATINCRYPT": "LC",
    "NDSS": "NDSS",
    "PAIRING": "PAIRING",
    "PETS": "PETS",
    "PKC": "PKC",
    "PODC": "PODC",
    "PQCRYPTO": "PQCRYPTO",
    "PROVSEC": "PROVSEC",
    "PoPETS": "PoPETS",
    "SAC": "SAC",
    "SCN": "SCN",
    "SODA": "SODA",
    "STOC": "STOC",
    "TCC": "TCC",
    "TCHES": "TCHES",
    "TRUSTBUS": "TRUSTBUS",
    "ToSC": "ToSC",
    "USENIX": "USENIX",
    "VIETCRYPT": "VIETCRYPT",
    "WISA": "WISA",
}

# TODO: Parse list of venues from cryptobib

venue_labels = list(venues.values())


def print_venues():
    for venue, label in venues.items():
        if venue == label:
            print(label)
        else:
            print(f"{label} ({venue})")
