#!/usr/bin/python
# -*- coding: utf-8 -*-
# coding=utf-8

import logging

from biblib import metajson
from biblib.metajson import Creator
from biblib.metajson import Event
from biblib.metajson import Person
from biblib.metajson import Orgunit
from biblib.metajson import Family
from biblib.util import jsonbson
from biblib.util import constants


creator_person_terms_of_address = [
    "baron",
    "captain",
    "chevalier",
    "docteur",
    "don",
    "duc",
    "professeur"
]

creator_particule = [
    #composed:
    "de la",
    "de las",
    "de les",
    "de los",
    "van den",
    "van der",
    "von der",
    #simple
    "a",
    "af",
    "am",
    "an",
    "apgl",
    "auf",
    "av",
    "d'",
    u"d’",
    "da",
    "dal",
    "dall'",
    u"dall’",
    "das",
    "de",
    "dei",
    "del",
    "della",
    "der",
    "des",
    "di",
    "dos",
    "du",
    "fra",
    "im",
    "la",
    "las",
    "le",
    "lo",
    "of",
    "ten-",
    "ter-",
    "van",
    "vom",
    "von",
    "y",
    "zu",
    "zum",
    "zur"
]

#todo : dict to role
creator_role_terms = [
    "(Eds)",
    "(eds)",
    "(eds.)",
    u"(éd.)",
    "(ed.)",
    "(dir.)",
    "(dir)",
    "(co-directeur)",
    "(rapporteur)",
    u"(membre invité)",
    "sous la direction de",
    "sous la direction d'",
    "sous la dir. de",
    "sous la dir. d'",
    "edited by",
    u"présenté par",
    " et ",
    " and ",
    " & ",
    "et al.",
    "()",
    "[]"
]

creator_event_terms = [
    "colloque",
    "conference",
    u"conférence",
    "congress",
    u"journée",
    "symposium"
]

creator_orgunit_terms = [
    ".com",
    ".edu",
    ".eu",
    ".fr",
    ".net",
    ".org",
    "2.0",
    "2007",
    "2012",
    "2014",
    "3.0",
    "24",
    "a contrario",
    u"académie",
    "acrimed",
    "act up",
    "anssi",
    "agricol",
    "alliance",
    "altermonde",
    "alternative",
    "antidote",
    "aosis",
    "archives",
    u"assemblée",
    "association",
    "associates",
    "autonome",
    "autre vie",
    "bank",
    "barnett & bridges",
    "blog",
    "business",
    "canal",
    "cap21",
    "c.n.c.c.f.p.",
    "c2rmf",
    "center",
    "centre",
    "cepii",
    "ceri",
    "cevipof",
    "cercle des",
    "cfdt",
    "cgt",
    "challenges",
    "cidem",
    "citoyen",
    "club",
    "cnam",
    "cnil",
    "cnn",
    "cnrs",
    "club",
    "cfcv",
    "citoyen",
    "civique",
    "collectif",
    "commission",
    u"commité",
    "committee",
    "communication",
    "communistes",
    "confederation",
    "confederazione",
    u"confédération",
    "conseil",
    "conservatoire",
    "constitutionnel",
    "coordination",
    "council",
    "cour",
    "crct",
    "credoc",
    u"décodeurs",
    u"démocrat",
    "dialogues",
    "direction",
    "droits",
    "ecole",
    "écologi",
    "ecologi",
    "economi",
    "économi",
    u"édition",
    u"éducat",
    "ena",
    "enb",
    u"enquête",
    "entreprise",
    "environnement",
    "enseignement",
    "espacestemps",
    "etalab",
    "euroframe",
    "europe",
    u"européen",
    u"éconoclaste",
    u"élève",
    "facebook",
    u"faculté",
    "faculty",
    "faculdade",
    u"fédération",
    u"féminin",
    u"féminisme",
    "fn",
    "fondafip",
    "fondapol",
    "fondation",
    "forum",
    "france",
    "futuribles",
    "gauche",
    "gaulliste",
    "geste",
    u"générale",
    u"génération",
    "gouvernement",
    "greenpeace",
    "groupe",
    "harmattan",
    "hopital",
    u"hôpital",
    "huffington post",
    u"humanité",
    "homme",
    "identitaire",
    u"idées",
    "inc.",
    u"indépendant",
    u"inégalités",
    "inrocks",
    "institut",
    "institute",
    "international",
    "injep",
    "iresmo",
    "ined",
    "insee",
    "iris",
    "irsn",
    "journal",
    u"l'acsé",
    "l'espoir",
    "l'express",
    u"l'hérétique",
    "laborato",
    u"laïque",
    u"le chêne",
    "le monde",
    "les cahiers",
    "les mots",
    "libertaire",
    u"liberté",
    u"libéral",
    u"libération",
    "library",
    "liens",
    "lutte",
    "maee",
    "mal-logé",
    "manifeste",
    "matra",
    "maudslay, sons and field",
    "media",
    "média",
    "melissa",
    u"mémoire",
    "meteo-france",
    u"méteo-france",
    u"ministère",
    "ministry",
    "minutes",
    "mobility",
    "modem",
    "mouvement",
    "museum",
    u"musée",
    "museo",
    "nacione",
    "national",
    "new york",
    "newsring",
    "ni putes",
    "nouvel obs",
    u"nucléaire",
    "observatoire",
    "ofce",
    "office",
    "opinion",
    "organisation",
    "orientation",
    u"ouvrière",
    "paris match",
    "parliament",
    "parti",
    u"pédagogique",
    "photo",
    "poing rouge",
    "political",
    "politique",
    u"pôle",
    "presses",
    "professionnel",
    "programa",
    "progressiste",
    "prospective",
    "portail",
    "publique",
    "radio",
    "paysan",
    "populaire",
    "portail",
    "project",
    "projet",
    "ps",
    "radicaux",
    "rassemble",
    "ratp",
    "recherche",
    u"réconciliation",
    u"règle",
    u"régions",
    u"républicain",
    u"réseau",
    u"réservés",
    "respublica",
    "retraite",
    "rfi",
    "ricerca",
    "rtl",
    "rue89",
    u"sans frontières",
    "sarl",
    "school",
    "science",
    u"sénat",
    "snesup",
    u"société",
    "society",
    u"società",
    "socialisme",
    "socialiste",
    "socio",
    "sofres",
    "souverainiste",
    u"sphère",
    "syndica",
    "télérama",
    "tf1",
    "trade",
    "travail",
    "tv",
    "twitter",
    "unesco",
    "unfccc",
    "union",
    "unis",
    "unitaire",
    "universi",
    u"vérités",
    "viavoice",
    "village",
    "wwf"
]

creator_citable_roles = [
    "aut",
    "edt",
    "pbd"
]

role_text_to_role_code = {
    "Actor": "act",
    "Adapter": "adp",
    "Author of afterword, colophon, etc.": "aft",
    "Annotator": "ann",
    "Bibliographic antecedent": "ant",
    "Applicant": "app",
    "Author in quotations or text extracts": "aqt",
    "Architect": "arc",
    "Arranger": "arr",
    "Artist": "art",
    "Assignee": "asg",
    "Associated name": "asn",
    "Attributed name": "att",
    "Auctioneer": "auc",
    "Author of dialog": "aud",
    "Author of introduction, etc.": "aui",
    "Author of screenplay, etc.": "aus",
    "Author": "aut",
    "Binding designer": "bdd",
    "Bookjacket designer": "bjd",
    "Book designer": "bkd",
    "Book producer": "bkp",
    "Binder": "bnd",
    "Bookplate designer": "bpd",
    "Bookseller": "bsl",
    "Conceptor": "ccp",
    "Choreographer": "chr",
    "Collaborator": "clb",
    "Client": "cli",
    "Calligrapher": "cll",
    "Collotyper": "clt",
    "Commentator": "cmm",
    "Composer": "cmp",
    "Compositor": "cmt",
    "Conductor": "cnd",
    "Censor": "cns",
    "Contestant-appellee": "coe",
    "Collector": "col",
    "Compiler": "com",
    "Contestant": "cos",
    "Contestant-appellant": "cot",
    "Copyright claimant": "cpc",
    "Complainant-appellee": "cpe",
    "Copyright holder": "cph",
    "Complainant": "cpl",
    "Complainant-appellant": "cpt",
    "Creator": "cre",
    "Correspondent": "crp",
    "Corrector": "crr",
    "Consultant": "csl",
    "Consultant to a project": "csp",
    "Costume designer": "cst",
    "Contributor": "ctb",
    "Contestee-appellee": "cte",
    "Cartographer": "ctg",
    "Contractor": "ctr",
    "Contestee": "cts",
    "Contestee-appellant": "ctt",
    "Curator of an exhibition": "cur",
    "Commentator for written text": "cwt",
    "Defendant": "dfd",
    "Defendant-appellee": "dfe",
    "Defendant-appellant": "dft",
    "Degree grantor": "dgg",
    "Dissertant": "dis",
    "Delineator": "dln",
    "Dancer": "dnc",
    "Donor": "dnr",
    "Depositor": "dpt",
    "Draftsman": "drm",
    "Director": "drt",
    "Designer": "dsr",
    "Distributor": "dst",
    "Dedicatee": "dte",
    "Dedicator": "dto",
    "Dubious author": "dub",
    "Editor": "edt",
    "Engraver": "egr",
    "Electrotyper": "elt",
    "Engineer": "eng",
    "Etcher": "etr",
    "Expert": "exp",
    "Facsimilist": "fac",
    "Film editor": "flm",
    "Former owner": "fmo",
    "Funder": "fnd",
    "Forger": "frg",
    "Graphic technician": "grt",
    "Honoree": "hnr",
    "Host": "hst",
    "Illustrator": "ill",
    "Illuminator": "ilu",
    "Illuminator": "ilu",
    "Inscriber": "ins",
    "Inventor": "inv",
    "Instrumentalist": "itr",
    "Interviewee": "ive",
    "Interviewer": "ivr",
    "Librettist": "lbt",
    "Libelee-appellee": "lee",
    "Libelee": "lel",
    "Lender": "len",
    "Libelee-appellant": "let",
    "Libelant-appellee": "lie",
    "Libelant": "lil",
    "Libelant-appellant": "lit",
    "Landscape architec": "lsa",
    "Licensee": "lse",
    "Licensor": "lso",
    "Lithographer": "ltg",
    "Lyricist": "lyr",
    "Metadata contact": "mdc",
    "Moderator": "mod",
    "Monitor": "mon",
    "Metal-engraver": "mte",
    "Musician": "mus",
    "Narrator": "nrt",
    "Opponent": "opn",
    "Originator": "org",
    "Organizer of meeting": "orm",
    "Other": "oth",
    "Owner": "own",
    "Patron": "pat",
    "Publishing director": "pbd",
    "Publisher": "pbl",
    "Proofreader": "pfr",
    "Photographer": "pht",
    "Platemaker": "plt",
    "Printer of plates": "pop",
    "Papermaker": "ppm",
    "Process contact": "prc",
    "Production personnel": "prd",
    "Performer": "prf",
    "Programmer": "prg",
    "Producer": "pro",
    "Printer": "prt",
    "Patent applicant": "pta",
    "Plaintiff-appellee": "pte",
    "Plaintiff": "ptf",
    "Patent holder": "pth",
    "Plaintiff-appellant": "ptt",
    "Rubricator": "rbr",
    "Recording engineer": "rce",
    "Recipient": "rcp",
    "Redactor": "red",
    "Renderer": "ren",
    "Researcher": "res",
    "Reviewer": "rev",
    "Respondent-appellee": "rse",
    "Respondent": "rsp",
    "Respondent-appellant": "rst",
    "Research team head": "rth",
    "Research team member": "rtm",
    "Scientific advisor": "sad",
    "Scenarist": "sce",
    "Sculptor": "scl",
    "Scribe": "scr",
    "Secretary": "sec",
    "Signer": "sgn",
    "Singer": "sng",
    "Speaker": "spk",
    "Sponsor": "spn",
    "Surveyor": "srv",
    "Standards body": "stn",
    "Stereotyper": "str",
    "Thesis advisor": "ths",
    "Transcriber": "trc",
    "Translator": "trl",
    "Type designer": "tyd",
    "Typographer": "tyg",
    "Vocalist": "voc",
    "Writer of accompanying material": "wam",
    "Woodcutter": "wdc",
    "Wood-engraver": "wde",
    "Witness": "wit"
}

role_unimarc_to_role_code = {
    "005": "act",
    "010": "adp",
    "020": "ann",
    "030": "arr",
    "040": "art",
    "050": "asg",
    "060": "asn",
    "065": "auc",
    "070": "aut",
    "072": "aqt",
    "075": "aft",
    "080": "aui",
    "090": "aud",
    "100": "ant",
    "110": "bnd",
    "120": "bdd",
    "130": "bkd",
    "130": "dsr",
    "130": "plt",
    "140": "bjd",
    "150": "bpd",
    "160": "bsl",
    "170": "cll",
    "180": "ctg",
    "190": "cns",
    "200": "chr",
    "205": "clb",
    "205": "ctb",
    "205": "prd",
    "210": "cmm",
    "212": "cwt",
    "220": "com",
    "230": "cmp",
    "240": "cmt",
    "245": "ccp",
    "250": "cnd",
    "255": "csl",
    "255": "csp",
    "260": "cph",
    "273": "cur",
    "275": "dnc",
    "280": "dte",
    "290": "dto",
    "295": "dgg",
    "300": "drt",
    "305": "app",
    "305": "dis",
    "310": "dst",
    "320": "dnr",
    "330": "att",
    "330": "dub",
    "340": "edt",
    "340": "trc",
    "350": "egr",
    "350": "ins",
    "360": "etr",
    "365": "exp",
    "370": "flm",
    "380": "frg",
    "390": "fmo",
    "390": "own",
    "400": "fnd",
    "410": "grt",
    "420": "hnr",
    "430": "ilu",
    "440": "drm",
    "440": "ill",
    "460": "ive",
    "470": "ivr",
    "480": "lbt",
    "500": "lso",
    "510": "ltg",
    "520": "lyr",
    "530": "mte",
    "530": "wdc",
    "540": "col",
    "540": "mon",
    "540": "srv",
    "545": "itr",
    "545": "mus",
    "550": "nrt",
    "557": "orm",
    "560": "cre",
    "560": "org",
    "570": "oth",
    "580": "ppm",
    "582": "pta",
    "584": "inv",
    "587": "pth",
    "590": "prf",
    "600": "pht",
    "605": "spk",
    "610": "prt",
    "610": "str",
    "620": "pop",
    "630": "pro",
    "632": "cst",
    "632": "ilu",
    "635": "prg",
    "640": "crr",
    "640": "pfr",
    "650": "bkp",
    "650": "pbl",
    "651": "pbd",
    "660": "rcp",
    "670": "rce",
    "673": "rth",
    "675": "rev",
    "677": "res",
    "677": "rtm",
    "680": "rbr",
    "690": "aus",
    "690": "sce",
    "695": "sad",
    "700": "scr",
    "705": "scl",
    "710": "red",
    "710": "sec",
    "720": "sgn",
    "721": "voc",
    "723": "spn",
    "725": "stn",
    "727": "ths",
    "730": "trl",
    "740": "tyd",
    "750": "tyg",
    "753": "ren",
    "755": "sng",
    "760": "wde",
    "770": "wam"
}

role_type_contributor = "contributor"
role_type_creator = "creator"

role_type = {
    "act": role_type_contributor,
    "adp": role_type_contributor,
    "aft": role_type_contributor,
    "ann": role_type_contributor,
    "ant": role_type_creator,
    "app": role_type_creator,
    "aqt": role_type_contributor,
    "arc": role_type_creator,
    "arr": role_type_contributor,
    "art": role_type_contributor,
    "asg": role_type_contributor,
    "asn": role_type_contributor,
    "att": role_type_creator,
    "auc": role_type_creator,
    "aud": role_type_creator,
    "aui": role_type_contributor,
    "aus": role_type_creator,
    "aut": role_type_creator,
    "bdd": role_type_contributor,
    "bjd": role_type_contributor,
    "bkd": role_type_contributor,
    "bkp": role_type_creator,
    "bnd": role_type_creator,
    "bpd": role_type_contributor,
    "bsl": role_type_contributor,
    "ccp": role_type_creator,
    "chr": role_type_creator,
    "clb": role_type_contributor,
    "cli": role_type_contributor,
    "cll": role_type_creator,
    "clt": role_type_contributor,
    "cmm": role_type_contributor,
    "cmp": role_type_creator,
    "cmt": role_type_contributor,
    "cnd": role_type_creator,
    "cns": role_type_contributor,
    "coe": role_type_creator,
    "col": role_type_contributor,
    "com": role_type_contributor,
    "cos": role_type_creator,
    "cot": role_type_creator,
    "cpc": role_type_contributor,
    "cpe": role_type_creator,
    "cph": role_type_contributor,
    "cpl": role_type_creator,
    "cpt": role_type_creator,
    "cre": role_type_creator,
    "crp": role_type_contributor,
    "crr": role_type_contributor,
    "csl": role_type_contributor,
    "csp": role_type_contributor,
    "cst": role_type_creator,
    "ctb": role_type_contributor,
    "cte": role_type_contributor,
    "ctg": role_type_creator,
    "ctr": role_type_creator,
    "cts": role_type_contributor,
    "ctt": role_type_contributor,
    "cur": role_type_creator,
    "cwt": role_type_contributor,
    "dfd": role_type_creator,
    "dfe": role_type_creator,
    "dft": role_type_creator,
    "dgg": role_type_contributor,
    "dis": role_type_creator,
    "dln": role_type_contributor,
    "dnc": role_type_contributor,
    "dnr": role_type_contributor,
    "dpt": role_type_contributor,
    "drm": role_type_contributor,
    "drt": role_type_creator,
    "dsr": role_type_contributor,
    "dst": role_type_contributor,
    "dte": role_type_contributor,
    "dto": role_type_contributor,
    "dub": role_type_creator,
    "edt": role_type_contributor,
    "egr": role_type_creator,
    "elt": role_type_contributor,
    "eng": role_type_contributor,
    "etr": role_type_contributor,
    "exp": role_type_contributor,
    "fac": role_type_contributor,
    "flm": role_type_contributor,
    "fmo": role_type_contributor,
    "fnd": role_type_contributor,
    "frg": role_type_contributor,
    "grt": role_type_contributor,
    "hnr": role_type_contributor,
    "hst": role_type_contributor,
    "ill": role_type_creator,
    "ilu": role_type_creator,
    "ilu": role_type_contributor,
    "ins": role_type_creator,
    "inv": role_type_creator,
    "itr": role_type_contributor,
    "ive": role_type_creator,
    "ivr": role_type_contributor,
    "lbt": role_type_creator,
    "lee": role_type_creator,
    "lel": role_type_creator,
    "len": role_type_contributor,
    "let": role_type_creator,
    "lie": role_type_creator,
    "lil": role_type_creator,
    "lit": role_type_creator,
    "lsa": role_type_contributor,
    "lse": role_type_contributor,
    "lso": role_type_contributor,
    "ltg": role_type_creator,
    "lyr": role_type_creator,
    "mdc": role_type_contributor,
    "mod": role_type_contributor,
    "mon": role_type_contributor,
    "mte": role_type_contributor,
    "mus": role_type_contributor,
    "nrt": role_type_contributor,
    "opn": role_type_creator,
    "org": role_type_creator,
    "orm": role_type_creator,
    "oth": role_type_contributor,
    "own": role_type_contributor,
    "pat": role_type_contributor,
    "pbd": role_type_contributor,
    "pbl": role_type_contributor,
    "pfr": role_type_contributor,
    "pht": role_type_creator,
    "plt": role_type_contributor,
    "pop": role_type_contributor,
    "ppm": role_type_contributor,
    "prc": role_type_contributor,
    "prd": role_type_contributor,
    "prf": role_type_contributor,
    "prg": role_type_contributor,
    "pro": role_type_contributor,
    "prt": role_type_creator,
    "pta": role_type_creator,
    "pte": role_type_creator,
    "ptf": role_type_creator,
    "pth": role_type_creator,
    "ptt": role_type_creator,
    "rbr": role_type_contributor,
    "rce": role_type_contributor,
    "rcp": role_type_contributor,
    "red": role_type_contributor,
    "ren": role_type_contributor,
    "res": role_type_contributor,
    "rev": role_type_contributor,
    "rse": role_type_creator,
    "rsp": role_type_creator,
    "rst": role_type_creator,
    "rth": role_type_contributor,
    "rtm": role_type_contributor,
    "sad": role_type_contributor,
    "sce": role_type_creator,
    "scl": role_type_creator,
    "scr": role_type_contributor,
    "sec": role_type_contributor,
    "sgn": role_type_contributor,
    "sng": role_type_contributor,
    "spk": role_type_creator,
    "spn": role_type_contributor,
    "srv": role_type_contributor,
    "stn": role_type_contributor,
    "str": role_type_contributor,
    "ths": role_type_contributor,
    "trc": role_type_contributor,
    "trl": role_type_contributor,
    "tyd": role_type_contributor,
    "tyg": role_type_contributor,
    "voc": role_type_contributor,
    "wam": role_type_contributor,
    "wdc": role_type_creator,
    "wde": role_type_creator,
    "wit": role_type_contributor
}

def formatted_name_list_to_creator_list(formatted_name_list, rec_class="person", role="aut"):
    if formatted_name_list:
        creator_list = []
        for formatted_name in formatted_name_list:
            creator = formatted_name_to_creator(formatted_name, rec_class, role)
            if creator:
                creator_list.append(creator)
        return creator_list


def formatted_name_to_creator(formatted_name, rec_class, role):
    #logging.debug("formatted_name_to_creator formatted_name: {}".format(formatted_name))
    if formatted_name:
        formatted_name = formatted_name.strip()
        event = None
        family = None
        orgunit = None
        person = None

        #logging.debug("formatted_name: {}".format(formatted_name))
        # rec_class determination
        if rec_class is None or rec_class not in [constants.REC_CLASS_EVENT, constants.REC_CLASS_FAMILY, constants.REC_CLASS_ORGUNIT, constants.REC_CLASS_PERSON]:
            for event_term in creator_event_terms:
                if event_term in formatted_name.lower():
                    rec_class = constants.REC_CLASS_EVENT
                    break
            for orgunit_term in creator_orgunit_terms:
                if orgunit_term in formatted_name.lower():
                    rec_class = constants.REC_CLASS_ORGUNIT
                    break
            if rec_class is None:
                rec_class = constants.REC_CLASS_PERSON

        creator = Creator()
        if role:
            creator["roles"] = [role]

        if rec_class == constants.REC_CLASS_EVENT:
            event = Event()
            event["title"] = formatted_name
            creator["agent"] = event

        elif rec_class == constants.REC_CLASS_ORGUNIT:
            orgunit = Orgunit()
            orgunit["name"] = formatted_name
            creator["agent"] = orgunit

        elif rec_class == constants.REC_CLASS_PERSON or rec_class == constants.REC_CLASS_FAMILY:
            # class is "Person" or "Family"

            name_given = ""
            name_middle = ""
            name_family = ""
            name_prefix = ""
            name_terms_of_address = ""
            date_birth = ""
            date_death = ""

            parenthesis_index = formatted_name.rfind("(")
            if parenthesis_index != -1:
                #may be like: name (date_birth-date_death)
                dates_part = formatted_name[parenthesis_index + 1:-1].strip()
                date_birth = dates_part[:4]
                date_death = dates_part[5:]
                if date_death == "....":
                    date_death = ""
                formatted_name = formatted_name[:parenthesis_index].strip()

            slash_index = formatted_name.find("/")
            if slash_index != -1:
                #like: name/affiliation
                affiliation_name = formatted_name[slash_index + 1:].strip()
                formatted_name = formatted_name[:slash_index].strip()

            commaspacejrdot_index = formatted_name.rfind(", Jr.")
            if (commaspacejrdot_index != -1):
                #like "Paul B. Harvey, Jr."
                formatted_name = formatted_name[:commaspacejrdot_index].strip()
                name_middle = "Jr."

            #Is it formatted like "Family, Given" or "Given Family" ?
            comma_index = formatted_name.find(",")
            if comma_index == -1:
                space_index = formatted_name.rfind(" ")
                #logging.debug(formatted_name)
                #logging.debug(space_index)
                if space_index != -1:
                    #like Given Family
                    name_given = formatted_name[:space_index].strip()
                    name_family = formatted_name[space_index+1:].strip()
                else:
                    #like Family
                    name_family = formatted_name.strip()

            else:
                #like Family, Given
                name_family = formatted_name[:comma_index].strip()
                name_given = formatted_name[comma_index+1:].strip()

            # manage the terms_of_address and particule
            for term_of_address in creator_person_terms_of_address:
                if name_family and name_family.lower().startswith(term_of_address+" "):
                    name_terms_of_address = name_family[:len(term_of_address)]
                    name_family = name_family[len(term_of_address):].strip()
                if name_given:
                    if name_given.lower().endswith(" "+term_of_address):
                        name_terms_of_address = name_given[-len(term_of_address):]
                        name_given = name_given[:-len(term_of_address)].strip()
                    if name_given.lower().startswith(term_of_address+" "):
                        name_terms_of_address = name_given[:len(term_of_address)]
                        name_given = name_given[len(term_of_address):].strip()
                    if name_given.lower() == term_of_address:
                        name_terms_of_address = name_given
                        name_given = None

            # Be careful with a particule inside the name like: Viveiros de Castro, Eduardo
            for particule in creator_particule:
                if name_family and name_family.lower().startswith(particule+" "):
                    name_prefix = name_family[0:len(particule)]
                    name_family = name_family[len(particule):].strip()
                if name_given:
                    if name_given.lower().endswith(" "+particule):
                        name_prefix = name_given[-len(particule):]
                        name_given = name_given[:-len(particule)].strip()
                    if name_given.lower().startswith(particule+" "):
                        name_prefix = name_given[:len(particule)]
                        name_given = name_given[len(particule):].strip()
                    if name_given.lower() == particule:
                        name_prefix = name_given
                        name_given = None

            if rec_class == constants.REC_CLASS_PERSON:
                person = Person()
                person.set_key_if_not_none("name_family", name_family)
                person.set_key_if_not_none("name_given", name_given)
                person.set_key_if_not_none("name_middle", name_middle)
                person.set_key_if_not_none("name_terms_of_address", name_terms_of_address)
                person.set_key_if_not_none("name_prefix", name_prefix)
                person.set_key_if_not_none("date_birth", date_birth)
                person.set_key_if_not_none("date_death", date_death)

                creator["agent"] = person

                if 'affiliation_name' in vars() and affiliation_name:
                    #todo manage as an object
                    affiliation = Orgunit()
                    affiliation["name"] = affiliation_name
                    creator["affiliation"] = affiliation

            elif rec_class == constants.REC_CLASS_FAMILY:
                family = Family()
                family.set_key_if_not_none("name_family", name_family)
                creator["agent"] = family

        #logging.debug(jsonbson.dumps_json(creator, True))
        return creator


def formatted_name(creator, style=metajson.STYLE_FAMILY_COMMA_GIVEN):
    if creator:
        return creator.formatted_name(style)


def change_contibutors_role(creators, role):
    if creators:
        for creator in creators:
            creator.set_key_if_not_none("roles", [role])
    return creators
