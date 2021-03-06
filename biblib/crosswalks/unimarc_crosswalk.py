#!/usr/bin/python
# -*- coding: utf-8 -*-
# coding=utf-8

import logging
import os
import re

from pymarc import MARCReader
from pymarc import record_to_xml
import smc.bibencodings

from biblib.metajson import Brand
from biblib.metajson import Creator
from biblib.metajson import Document
from biblib.metajson import Event
from biblib.metajson import Family
from biblib.metajson import Orgunit
from biblib.metajson import Person
from biblib.metajson import Resource
from biblib.metajson import Rights
from biblib.metajson import Subject
from biblib.services import creator_service
from biblib.services import date_service
from biblib.services import language_service
from biblib.services import metajson_service
from biblib.util import console
from biblib.util import constants
from biblib.util import jsonbson

isbn_regex = re.compile(r'([0-9\-xX]+)')

charsets_dict = {
    "01": "ISO 646, version IRV (caractères latins de base)",
    "02": "Registre ISO #37 (caractères cyrilliques de base)",
    "03": "ISO 5426 (caractères latins - jeu étendu)",
    "04": "ISO 5427 (caractères cyrilliques - jeu étendu)",
    "05": "ISO 5428 (caractères grecs)",
    "06": "ISO 6438 (caractères africains codés)",
    "07": "ISO 10586 (caractères géorgiens)",
    "08": "ISO 8957 (caractères hébreux) Table 1",
    "09": "ISO 8957 (caractères hébreux) Table 2",
    "10": "[Réservé]",
    "11": "ISO 5426-2 (caractères latins utilisés dans les langues européennes minoritaires et dans une typographie obsolète)",
    "50": "ISO 10646 Niveau 3 (Unicode, UTF-8)",
}

target_audience_unimarc_to_marctarget = {
    'a': "juvenile",  # a=jeunesse (général)
    'b': "preschool",  # b=pré-scolaire, 0-5 ans
    'c': "juvenile",  # c=scolaire, 5-10 ans
    'd': "juvenile",  # d=enfant, 9-14 ans
    'e': "adolescent",  # e=jeune adulte, 14-20 ans
    'k': "specialized",  # k=adulte, haut niveau
    'm': "adult"  # m=adulte, grand public
    # u=inconnu
}

transliterations_dict = {
    "a": "iso",  # norme ISO de translittération
    "b": "other",  # autre règle
    "c": "iso_and_others",  # translittérations multiples : ISO ou autres règles
    "y": "no_transliteration"  # pas de translittération
}

def unimarc_file_path_to_metasjon_list(unimarc_file_path, source, rec_id_prefix, only_first_record):
    #logging.debug("unimarc_file_path_to_metasjon_list")
    with open(unimarc_file_path) as unimarc_file:
        return unimarc_file_to_metasjon_list(unimarc_file, source, rec_id_prefix, only_first_record)


def unimarc_file_to_metasjon_list(unimarc_file, source, rec_id_prefix, only_first_record):
    #logging.debug("unimarc_file_to_metasjon_list")
    marc_reader = MARCReader(unimarc_file, to_unicode=True, force_utf8=False, hide_utf8_warnings=False, utf8_handling='ignore')
    return unimarc_marcreader_to_metasjon_list(marc_reader, source, rec_id_prefix, only_first_record)


def unimarc_marcreader_to_metasjon_list(marc_reader, source, rec_id_prefix, only_first_record):
    #logging.debug("unimarc_marcreader_to_metasjon_list")
    count = 0
    for record in marc_reader:
        count += 1
        yield unimarc_record_to_metajson(record, source, rec_id_prefix)


def unimarc_record_to_metajson(record, source, rec_id_prefix):
    #logging.debug("unimarc_record_to_metajson")
    document = Document()

    #logging.debug(record)
    #logging.debug(jsonbson.dumps_json(record.as_dict(), pretty=True))

    if source:
        document["rec_source"] = source

    # 002 -> rec_id
    rec_id = ""
    if rec_id_prefix is None:
        rec_id_prefix = ""
    if record['002'] is not None:
        rec_id = rec_id_prefix + record['002'].data
    elif record['001'] is not None:
        rec_id = rec_id_prefix + record['001'].data
    #logging.debug("rec_id: {}".format(rec_id))
    document["rec_id"] = rec_id
    

    # Debug
    #output_dir = os.path.join("data", "num", "output")
    #output_file_path = os.path.join(output_dir, rec_id + ".marc.txt")
    #with open(output_file_path, "w") as output_file:
    #    output_file.write(str(record))
    # output_filexml_path = os.path.join(output_dir, rec_id + ".marcxml.xml")
    # with open(output_filexml_path, "w") as output_filexml:
    #     output_filexml.write(record_to_xml(record))

    # leader and 1XX -> rec_type
    rec_type = None

    # leader
    leader6 = record.leader[6]
    leader7 = record.leader[7]

    # 100$a/17-19
    # 100$a/20
    field100ap1719 = None
    field100ap20 = None
    if record['100'] is not None and record['100']['a'] is not None:
        field100ap1719 = record['100']['a'][17:20]
        field100ap20 = record['100']['a'][20:21]

    # 105/4-7
    field105ap48 = None
    if record['105'] is not None and record['105']['a'] is not None:
        field105ap48 = record['105']['a'][4:8]

    # 106$a
    field106a = None
    if record['106'] is not None and record['106']['a'] is not None:
        field106a = record['106']['a']

    # 110$a/1
    field110ap0 = None
    field110ap1 = None
    if record['110'] is not None and record['110']['a'] is not None:
        field110ap0 = record['110']['a'][0:1]
        field110ap1 = record['110']['a'][1:2]

    # 115$a/0
    field115ap0 = None
    if record['115'] is not None and record['115']['a'] is not None:
        field115ap0 = record['115']['a'][0:1]

    # 116$a/0
    field116ap0 = None
    if record['116'] is not None and record['116']['a'] is not None:
        field116ap0 = record['116']['a'][0:1]
        #d = impression en gros caractères
        #e = journal
        #f = caractères Braille ou Moon
        #g = micro-impression
        #h = manuscrit
        #i = multimédia multisupport (Par exemple : un volume imprimé accompagné d’un supplément sur microfiches.)
        #j = impression en réduction
        #r = impression normale
        #s = ressource électronique
        #t = microforme
        #z = autres formes de présentation

    # 121$a/0
    field121ap0 = None
    if record['121'] is not None and record['121']['a'] is not None:
        field121ap0 = record['121']['a'][0:1]

    # 124$b
    field124b = None
    if record['124'] is not None and record['124']['b'] is not None:
        field124b = record['124']['b']

    # 126$a/0
    field126ap0 = None
    if record['126'] is not None and record['126']['a'] is not None:
        field126ap0 = record['126']['a'][0:1]

    # 135/0
    field135ap0 = None
    if record['135'] is not None and record['135']['a'] is not None:
        field135ap0 = record['135']['a'][0:1]

    # 300$a
    field300a = None
    if record['300'] is not None and record['300']['a'] is not None:
        field300a = record['300']['a']

    # logging.debug("leader6: {}".format(leader6))
    # logging.debug("leader7: {}".format(leader7))
    # logging.debug("100$a/17-19: {}".format(field100ap1719))
    # logging.debug("100$a/20: {}".format(field100ap20))
    # logging.debug("105/4-7: {}".format(field105ap48))
    # logging.debug("106$a: {}".format(field106a))
    # logging.debug("110$a/0: {}".format(field110ap0))
    # logging.debug("110$a/1: {}".format(field110ap1))
    # logging.debug("115$a/0: {}".format(field115ap0))
    # logging.debug("116/0: {}".format(field116ap0))
    # logging.debug("121$a/0: {}".format(field121ap0))
    # logging.debug("124$b: {}".format(field124b))
    # logging.debug("126$a/0: {}".format(field126ap0))
    # logging.debug("135$a/0: {}".format(field135ap0))

    if leader6 == "a":
        if leader7 == "a":
            if field300a == "Numéro spécial":
                rec_type = constants.DOC_TYPE_PERIODICALISSUE
            else:
                rec_type = constants.DOC_TYPE_JOURNALARTICLE
        elif leader7 == "c":
            rec_type = constants.DOC_TYPE_PRESSCLIPPING
        elif leader7 == "m":
            rec_type = constants.DOC_TYPE_BOOK
        elif leader7 == "s":
            # 110 : Zone de données codées : Ressources continues
            # 110$a/0 Type de ressource continue
            if field110ap0 == "a":
                # a: périodique
                rec_type = constants.DOC_TYPE_JOURNAL
            elif field110ap0 == "b":
                # b: collection de monographies
                rec_type = constants.DOC_TYPE_MULTIVOLUMEBOOK
            elif field110ap0 == "c":
                # c: journal
                rec_type = constants.DOC_TYPE_NEWSPAPER
            elif field110ap0 == "e":
                # e: publication à feuillets mobiles et à mise à jour
                rec_type = constants.DOC_TYPE_LOOSELEAFPUBLICATION
            elif field110ap0 == "f":
                # f: base de données
                rec_type = constants.DOC_TYPE_DATABASE
            elif field110ap0 == "g":
                # g: site web à mise à jour
                rec_type = constants.DOC_TYPE_WEBSITE
            elif field110ap0 == "g":
                # z: autre
                rec_type = constants.DOC_TYPE_JOURNAL
            else:
                rec_type = constants.DOC_TYPE_JOURNAL

            # 110$a/1 field110ap1 : Périodicité
            if field110ap1 in ["a", "b", "c", "n"]:
                # a: quotidienne
                # b: bihebdomadaire
                # c: hebdomadaire
                # n: trois fois par semaine
                rec_type = constants.DOC_TYPE_NEWSPAPER

        else:
            rec_type = constants.DOC_TYPE_DOCUMENT

    elif leader6 == "b":
        rec_type = constants.DOC_TYPE_MANUSCRIPT
    elif leader6 in ["c", "d"]:
        rec_type = constants.DOC_TYPE_MUSICALSCORE
    elif leader6 in ["e", "f"]:
        rec_type = constants.DOC_TYPE_MAP
    elif leader6 == "g":
        rec_type = constants.DOC_TYPE_VIDEORECORDING
    elif leader6 == "i":
        rec_type = constants.DOC_TYPE_AUDIORECORDING
    elif leader6 == "j":
        rec_type = constants.DOC_TYPE_MUSICRECORDING
    elif leader6 == "k":
        rec_type = constants.DOC_TYPE_IMAGE
    elif leader6 == "l":
        # 135$a/0 field135ap0 : Zone de données codées : ressources électroniques
        if field135ap0 == "a":
            # a: données numériques
            rec_type = constants.DOC_TYPE_DATASETQUANTI
        elif field135ap0 == "b":
            # b: programme informatique
            rec_type = constants.DOC_TYPE_SOFTWARE
            # c: illustration
        elif field135ap0 == "d":
            # d: texte
            if leader7 == "a":
                rec_type = constants.DOC_TYPE_EJOURNALARTICLE
            elif leader7 == "c":
                rec_type = constants.DOC_TYPE_PRESSCLIPPING
            elif leader7 == "m":
                rec_type = constants.DOC_TYPE_EBOOK
            elif leader7 == "s":
                rec_type = constants.DOC_TYPE_EJOURNAL
        elif field135ap0 == "e":
            # e: données bibliographiques
            rec_type = constants.DOC_TYPE_BIBLIOGRAPHY
        elif field135ap0 == "f":
            # f: polices de caractères
            rec_type = constants.DOC_TYPE_FONT
        elif field135ap0 == "g":
            # g: jeu
            rec_type = constants.DOC_TYPE_GAME
        elif field135ap0 == "h":
            # h: son
            rec_type = constants.DOC_TYPE_AUDIORECORDING
        elif field135ap0 == "i":
            # i: multimédia interactif
            rec_type = constants.DOC_TYPE_MULTIMEDIA
        elif field135ap0 == "j":
            # j: système ou service en ligne
            rec_type = constants.DOC_TYPE_WEBSITE
        elif field135ap0 == "u":
            # u: inconnu
            rec_type = constants.DOC_TYPE_ERESOURCE
        elif field135ap0 == "v":
            # v: combinaison de données
            rec_type = constants.DOC_TYPE_DATASETQUANTI
            # z: autre
        else:
            if leader7 == "a":
                if field300a == "Numéro spécial":
                    rec_type = constants.DOC_TYPE_PERIODICALISSUE
                else:
                    rec_type = constants.DOC_TYPE_EJOURNALARTICLE
            elif leader7 == "c":
                rec_type = constants.DOC_TYPE_PRESSCLIPPING
            elif leader7 == "m":
                rec_type = constants.DOC_TYPE_EBOOK
            elif leader7 == "s":
                rec_type = constants.DOC_TYPE_EJOURNAL
            else:
                rec_type = constants.DOC_TYPE_DOCUMENT
    elif leader6 == "m":
        rec_type = constants.DOC_TYPE_KIT
    elif leader6 == "r":
        rec_type = constants.DOC_TYPE_PHYSICALOBJECT
    else:
        rec_type = constants.DOC_TYPE_DOCUMENT
    document["rec_type"] = rec_type

    # 005 -> rec_modified_date
    if record['005'] is not None and record['005'].data is not None:
        tmp = record['005'].data.strip().split(".")[0]
        document["rec_modified_date"] = date_service.parse_to_iso8601(tmp)

    # 0XX and 945$b -> identifiers
    identifiers = []
    # 001 -> identifier ppn
    extract_unimarc_identifier(record, '001', 'data', 'ppn', identifiers)
    # 010 -> identifier isbn
    extract_unimarc_identifier(record, '010', 'a', 'isbn', identifiers)
    # 011 -> identifier issn
    # todo add $f
    extract_unimarc_identifier(record, '011', 'a', 'issn', identifiers)
    # 012 -> identifier imprint
    extract_unimarc_identifier(record, '012', 'a', 'imprint', identifiers)
    # 013 -> identifier ismn
    extract_unimarc_identifier(record, '013', 'a', 'ismn', identifiers)
    # 014 -> identifier sici or $2
    extract_unimarc_identifier(record, '014', 'a', 'sici', identifiers)
    # 015 -> identifier isrn
    extract_unimarc_identifier(record, '015', 'a', 'isrn', identifiers)
    # 016 -> identifier isrc
    extract_unimarc_identifier(record, '016', 'a', 'isrc', identifiers)
    # 017 -> identifier other
    extract_unimarc_identifier(record, '017', 'a', 'other', identifiers)
    # 020 -> identifier lccn
    extract_unimarc_identifier(record, '020', 'b', 'lccn', identifiers)
    # 021 -> identifier copyright
    extract_unimarc_identifier(record, '021', 'b', 'copyright', identifiers)
    # 022 -> identifier officialpub
    extract_unimarc_identifier(record, '022', 'b', 'officialpub', identifiers)
    # 029 -> identifier copyright
    extract_unimarc_identifier(record, '029', 'b', 'copyright', identifiers)
    # 035 -> identifier external
    extract_unimarc_identifier(record, '035', 'a', 'external', identifiers)
    # 036 -> identifier incipit
    extract_unimarc_identifier(record, '036', 'a', 'incipit', identifiers)
    # 040 -> identifier coden
    extract_unimarc_identifier(record, '040', 'a', 'coden', identifiers)
    # 071 -> identifier editref
    extract_unimarc_identifier(record, '071', 'a', 'editref', identifiers)
    # 072 -> identifier upc
    extract_unimarc_identifier(record, '072', 'a', 'upc', identifiers)
    # 073 -> identifier ean
    extract_unimarc_identifier(record, '073', 'a', 'ean', identifiers)
    # 945 -> identifier callnumber
    extract_unimarc_identifier(record, '945', 'b', 'callnumber', identifiers)
    if identifiers:
        document["identifiers"] = identifiers


    # 100$a stuff
    if record['100'] is not None and record['100']['a'] is not None:
        # date stuff

        # 100$a/0-7 -> rec_created_date
        rec_created_date = record['100']['a'][0:8]
        if rec_created_date.strip():
            document["rec_created_date"] = date_service.parse_to_iso8601(rec_created_date.strip())
        # 100$a/8 -> date_type
        date_type = record['100']['a'][8:9]
        # 100$a/9-12 -> date_1
        date_1 = record['100']['a'][9:13]
        if date_1 is not None:
            date_1 = date_1.strip()
        # 100$a/13-16 -> date_2
        date_2 = record['100']['a'][13:17]
        if date_2 is not None:
            date_2 = date_2.strip()

        date_copyright = None
        date_issued = None
        date_issued_begin = None
        date_issued_end = None
        date_issued_original = None
        date_issued_uncertain = None
        date_printed = None
        date_production = None

        if date_type == 'a':
            # a : ressource continue en cours
            # 1:date_issued_begin 2:None
            date_issued_begin = date_1
        elif date_type == 'b':
            # b : ressource continue morte
            # 1:date_issued_begin 2:date_issued_end
            date_issued_begin = date_1
            date_issued_end = date_2
        elif date_type == 'c':
            # c : ressource continue dont la situation est inconnue
            # 1:date_issued_begin 2:None
            date_issued_begin = date_1
        elif date_type == 'd':
            # d : monographie complète à la publication ou publiée dans une année civile
            # 1:date_issued 2:None
            date_issued = date_1
        elif date_type == 'e':
            # e : reproduction
            # 1:date_issued 2:date_issued_original
            date_issued = date_1
            date_issued_original = date_2
        elif date_type == 'f':
            # f : monographie dont la date de publication est incertaine
            # 1:date_issued 2:date_issued_uncertain
            date_issued = date_1
            date_issued_uncertain = date_2
        elif date_type == 'g':
            # g : monographie dont la publication s’étend sur plus d’une année
            # 1:date_issued 2:date_issued_end
            date_issued = date_1
            date_issued_end = date_2
        elif date_type == 'h':
            # h : monographie ayant à la fois une date de publication et une date de copyright ou de privilège
            # 1:date_issued 2:date_copyright
            date_issued = date_1
            date_copyright = date_2
        elif date_type == 'i':
            # i : monographie ayant à la fois une date d’édition ou de diffusion et une date de production
            # 1:date_issued 2:date_production
            date_issued = date_1
            date_production = date_2
        elif date_type == 'j':
            # j : monographie ayant une date de publication précise
            # 1:date_issued 2:date_issued MMJJ
            date_2_mm = date_2[0:3]
            date_2_jj = date_2[2:5]
            if date_2_mm:
                date_1 = date_1 + "-" + date_2_mm
                if date_2_jj:
                    date_1 = date_1 + "-" + date_2_jj
            date_issued = date_1
        elif date_type == 'k':
            # k : monographie ayant à la fois une date de publication et une date d’impression
            # 1:date_issued 2:date_printed
            date_issued = date_1
            date_printed = date_2
        elif date_type == 'u':
            # u : date(s) de publication inconnue(s)
            # 1:None 2:None
            pass
        else:
            date_issued = date_1

        if date_copyright:
            document["date_copyright"] = date_copyright
        if date_issued:
            document["date_issued"] = date_issued
        if date_issued_begin:
            document["date_issued_begin"] = date_issued
        if date_issued_end:
            document["date_issued_end"] = date_issued_end
        if date_issued_original:
            document["date_issued_original"] = date_issued_original
        if date_issued_uncertain:
            document["date_issued_uncertain"] = date_issued_uncertain
        if date_printed:
            document["date_printed"] = date_printed
        if date_production:
            document["date_production"] = date_production

        # 100$a/17-20 -> target_audiences
        targets = record['100']['a'][17:20]
        if targets.strip():
            target_audiences_marctarget = []
            for target in targets:
                if target in target_audience_unimarc_to_marctarget:
                    target_audiences_marctarget.append(target_audience_unimarc_to_marctarget[target])
            if target_audiences_marctarget:
                document["target_audiences"] = {"marctarget": target_audiences_marctarget}

        # 100$a/22-24 -> rec_cataloging_languages
        rec_cataloging_language = record['100']['a'][22:25]
        if rec_cataloging_language:
            rec_cataloging_language_rfc5646 = language_service.convert_iso639_2b_to_rfc5646(rec_cataloging_language)
            if rec_cataloging_language_rfc5646:
                document["rec_cataloging_languages"] = [rec_cataloging_language_rfc5646]

        # 100$a/25 -> rec_cataloging_transliteration
        rec_cataloging_transliteration = record['100']['a'][25:26]
        if rec_cataloging_transliteration.strip() and rec_cataloging_transliteration.strip() != "y":
            document["rec_cataloging_transliteration"] = transliterations_dict[rec_cataloging_transliteration.strip()]

        # 100$a/26-33 -> rec_cataloging_charactersets
        rec_cataloging_charactersets = []
        tmp_charsets = []
        tmp_charsets.append(record['100']['a'][26:28].strip())
        tmp_charsets.append(record['100']['a'][28:30].strip())
        tmp_charsets.append(record['100']['a'][30:32].strip())
        tmp_charsets.append(record['100']['a'][32:34].strip())
        for charset in tmp_charsets:
            if charset and charset in charsets_dict:
                rec_cataloging_charactersets.append({"charset_id": charset, "label": charsets_dict[charset]})
        if rec_cataloging_charactersets:
            document["rec_cataloging_charactersets"] = rec_cataloging_charactersets

    # 101$a -> languages
    # 101$b -> languages_intermediates
    # 101$c -> languages_originals
    if record.get_fields('101'):
        languages = []
        languages_intermediates = []
        languages_originals = []
        for field in record.get_fields('101'):
            for lang_iso639_2b in field.get_subfields('a'):
                lang_rfc5646 = language_service.convert_iso639_2b_to_rfc5646(lang_iso639_2b)
                if lang_rfc5646:
                    languages.append(lang_rfc5646)
            for lang_iso639_2b in field.get_subfields('b'):
                lang_rfc5646 = language_service.convert_iso639_2b_to_rfc5646(lang_iso639_2b)
                if lang_rfc5646:
                    languages_intermediates.append(lang_rfc5646)
            for lang_iso639_2b in field.get_subfields('c'):
                lang_rfc5646 = language_service.convert_iso639_2b_to_rfc5646(lang_iso639_2b)
                if lang_rfc5646:
                    languages_originals.append(lang_rfc5646)
        if languages:
            document["languages"] = languages
        if languages_intermediates:
            document["languages_intermediates"] = languages_intermediates
        if languages_originals:
            document["languages_originals"] = languages_originals

    # 102$a -> publication_countries
    if record.get_fields('102'):
        publication_countries = []
        for field in record.get_fields('102'):
            for subfield in field.get_subfields('a'):
                publication_countries.append(subfield)
        if publication_countries:
            document["publication_countries"] = publication_countries

    # 200 -> title
    if record['200'] is not None:
        #logging.debug("record['200'] = {}".format(record['200']))
        if record['200']['a'] is not None:
            ind2 = record['200'].indicator2.strip()
            if ind2:
                title_non_sort_pos = int(ind2)
            else:
                title_non_sort_pos = 0
            if title_non_sort_pos != 0:
                document["title_non_sort"] = record['200']['a'][:title_non_sort_pos]
                document["title"] = record['200']['a'][title_non_sort_pos:]
            else:
                document["title"] = record['200']['a']
        if record['200']['d'] is not None:
            document["title_alternatives"] = [{"title": record['200']['d']}]
        if record['200']['e'] is not None:
            document["title_sub"] = record['200']['e']
        if record['200']['h'] is not None:
            document["part_number"] = record['200']['h'].replace(",", "")
        if record['200']['i'] is not None:
            document["part_name"] = record['200']['i']
    if "title" not in document:
        document["title"] = ""

    # 205$a -> edition
    if record['205'] is not None and record['205']['a'] is not None:
        document["edition"] = record['205']['a'].strip()

    # 206 -> cartographics[i]
    if record['206'] is not None:
        cartographics = []
        for field in record.get_fields('206'):
            cartographic = {}
            if field['a'] is not None:
                # a : unstructured -> scale
                cartographic["scale"] = field['a']
            else:
                # b : scale
                scale = ""
                for subfield in field.get_subfields('b'):
                    scale = scale + " " + subfield
                if scale.strip():
                    cartographic["scale"] = scale.strip()
                # c : projection
                if field['c'] is not None:
                    cartographic["projection"] = field['c'].strip()
                # d : coordinates_unstructured
                if field['d'] is not None:
                    cartographic["coordinates_unstructured"] = field['d'].strip()
                # e : zone
                if field['e'] is not None:
                    cartographic["zone"] = field['e'].strip()
                # f : equinox
                if field['f'] is not None:
                    cartographic["equinox"] = field['f'].strip()
            if cartographic:
                cartographics.append(cartographic)
        if cartographics:
            document["cartographics"] = cartographics

    # 207$a -> holding_descriptions[i]
    if record['207'] is not None:
        holding_descriptions = []
        for field in record.get_fields('207'):
            for subfield in field.get_subfields('a'):
                if subfield.strip():
                    holding_descriptions.append(subfield.strip())
        if holding_descriptions:
            document["holding_descriptions"] = holding_descriptions

    # 210$a -> publication_places
    # 210$c -> publishers
    if record['210'] is not None:
        publication_places = []
        publishers = []
        for field in record.get_fields('210'):
            for subfield in field.get_subfields('a'):
                if subfield is not None and subfield not in publication_places:
                    publication_places.append(subfield)
            for subfield in field.get_subfields('c'):
                if subfield is not None and subfield not in publishers:
                    publishers.append(subfield)
        if publication_places:
            document["publication_places"] = publication_places
        if publishers:
            document["publishers"] = publishers


    # 215$a -> part_page_begin, part_page_end, extent_description, extent_duration, extent_volumes, extent_pages
    # 215$c -> physical_description_notes[i]/value
    physical_description_notes = []
    # 215$d -> extent_dimension
    # 215$e -> extent_accompanying_material
    if record['215'] is not None:
        part_volume = ""
        part_issue = ""
        part_page_begin = ""
        part_page_end = ""
        extent_accompanying_material = ""
        extent_description_final = ""
        extent_description = ""
        extent_dimension = ""
        extent_duration = ""
        extent_pages = ""
        extent_volumes = ""
        if record['215']['a'] is not None:
            extent_description_final = record['215']['a']

            # debug: insert 215$a in extent_description_original
            #document["extent_description_original"] = extent_description_final

            if rec_type in constants.DOC_TYPES_LIST_ARTICLES:
                # Articles types
                # examples :
                # 49 (3), mars 93 : p. 25-63.
                # p.29-169
                # (26), juil.-déc. 94 : p. 97-142 ; tabl., graph. ; bibliogr.
                # 27 (1-2), 1991 : p. 97-103 ; bibliogr.
                # (6446), 8 nov. 90 Numéro spécial : 106 p.
                # 11 (1), print. 92 : p. 26-39 ; tabl. ; bibliogr.
                # 27 (4), 1990 : p. 359-372 ; graph. ; bibliogr.
                # (21), janv.-mars 95 : p. 12-137 ; bibliogr.
                # (6656), 2 avr. 92 Numéro spécial : p. 8-104.
                # (1994)vol.27:n°2, p.479-532
                # (5), 1992 : p. 567-588 ; texte également en français.
                # 36 (6), juin 91 : p. 725-736 ; tabl.
                # 34 (3-4), aut.-hiv. 92 : p. 54-67 ; bibliogr.
                # part_issue, part_volume, date_issued, part_page_begin, part_page_end
                pass
                # TODO
                # part_volume
                # part_issue
                # date_issued ?
                # part_page_begin, part_page_end
            else :
                # Book et. al.
                # replace unwanted characters
                extent_description_final = extent_description_final.replace("(","").replace(")","").replace(";","").replace(":","")

                # extent_volumes : before extent_volumes_forms
                extent_volumes_forms = ["vol.",
                                        "v.",
                                        "atlas",
                                        "bobine de microfilm 35 mm positif",
                                        "classeur",
                                        u"disque optique numérique (CD-ROM)",
                                        "CD-ROM",
                                        "CDRom",
                                        "DVD",
                                        u"microfiches acétate",
                                        "microfiches",
                                        "recueil factice",
                                        u"tomes microfichés",
                                        "tomes",
                                        "tome"]
                for volumesform in extent_volumes_forms:
                    index = extent_description_final.find(volumesform.encode('utf-8'))
                    if index != -1:
                        length = len(volumesform.encode('utf-8'))
                        extent_volumes = extent_volumes + extent_description_final.encode('utf-8')[0:index+length].strip()
                        extent_description_final = extent_description_final[index+length:].strip()

                # extent_pages : before extent_pages_forms
                # examples : (431, 391 p.) ; X-266-30 p. ; (XVI-820, 762, 591, 464 p.) ; [4]f. de pl.
                extent_pages_forms = ["p. d'annexes",
                                      "p. de pl. h.-t.",
                                      "p. de pl. en coul.",
                                      "p. de pl. en noir et en coul.",
                                      "p. de pl. photogr. h.-t. en noir et en coul.",
                                      "p. de pl.",
                                      "p. de texte",
                                      "p. of plates",
                                      "p. multigr.",
                                      u"p. de supplément",
                                      "p. incl. tables",
                                      "p.",
                                      "ff. multigr.",
                                      "ff.",
                                      "f. multigr.",
                                      "f. de portr",
                                      "f. d'ill. en noir et en coul",
                                      "f.",
                                      #"cartes",
                                      #"carte",
                                      u"dépl.",
                                      "fac-sim. de presse",
                                      "fasc.",
                                      "f. de fac-sim.",
                                      "f. de pl.",
                                      u"f. de pl. dépl.",
                                      "f. de pl. en coul. en front.",
                                      "f. de pl. en coul.",
                                      "f. de pl. en front.",
                                      "f. de pl. en noir et en coul.",
                                      "f. de pl. hors-texte",
                                      "f. de pl. ill.",
                                      u"f. de pl. non reliées",
                                      u"f. de pl. plié",
                                      "leaf of plates",
                                      "leaves of plates",
                                      "microfiches",
                                      u"Non paginé multigr.",
                                      u"Non paginé",
                                      "Non pag.",
                                      u"non paginé",
                                      "planches",
                                      "p. de pl. en noir et en coul."
                                      "pl. en noir et en coul.",
                                      "pl. en coul",
                                      "pl. num.",
                                      "pl.",
                                      "pagination multiple",
                                      "Pagination multiple",
                                      "Pag. multiple",
                                      "pag. mult.",
                                      "various pagination",
                                      "loose-leaf",
                                      "images"]
                for pagesform in extent_pages_forms:
                    index = extent_description_final.find(pagesform.encode('utf-8'))
                    if index != -1:
                        length = len(pagesform.encode('utf-8'))
                        #length = len(pagesform)
                        extent_pages = extent_pages + extent_description_final.encode('utf-8')[0:index+length].strip()
                        extent_description_final = extent_description_final[index+length:].strip()

                # todo :
                # 2 h 17 min : extent_duration

                # if P. : part_page_begin and part_page_end (example : P. 166-171)
                index_part = extent_description_final.find("P.")
                if index_part != -1:
                    index_dash = extent_description_final[index_part:].find("-") + index_part
                    part_page_begin = extent_description_final[index_part+2:index_dash].strip()
                    part_page_end = extent_description_final[index_dash+1:].strip()
                    extent_description_final = extent_description_final[index_dash+1+len(part_page_end):].strip()

            # extent_description : before extent_volumes_forms
            desc_terms = ["bibliogr.",
                          "cartes",
                          "graph.",
                          "ill.",
                          u"multigraphié",
                          "port.",
                          u"résumé en anglais",
                          u"résumés en anglais",
                          u"résumés en anglais et en espagnol",
                          u"résumés en anglais et en français",
                          u"résumés en anglais et en russe",
                          u"résumés en français et en anglais",
                          "tabl"]
            for desc_term in desc_terms:
                index = extent_description_final.find(desc_term.encode('utf-8'))
                if index != -1:
                    length = len(desc_term.encode('utf-8'))
                    extent_description = extent_description + extent_description_final.encode('utf-8')[index:index+length].strip()
                    extent_description_final = extent_description_final[index+length:].strip()
            
        if record['215']['c'] is not None:
            # physical_description_notes
            physical_description_notes.append({"note_type":"material", "value":record['215']['c'].strip()})
        if record['215']['d'] is not None:
            # extent_dimension
            extent_dimension = record['215']['d'].strip()
        if record['215']['e'] is not None:
            # extent_accompanying_material
            extent_accompanying_material = record['215']['e'].strip()

        if part_volume:
            document["part_volume"] = part_volume
        if part_issue:
            document["part_issue"] = part_issue
        if part_page_begin:
            document["part_page_begin"] = part_page_begin
        if part_page_end:
            document["part_page_end"] = part_page_end
        if extent_accompanying_material:
            document["extent_accompanying_material"] = extent_accompanying_material
        if extent_description:
            document["extent_description"] = extent_description
        if extent_dimension:
            document["extent_dimension"] = extent_dimension
        if extent_duration:
            document["extent_duration"] = extent_duration
        if extent_pages:
            document["extent_pages"] = extent_pages
        if extent_volumes:
            document["extent_volumes"] = extent_volumes
        #if extent_description_final:
        #    document["extent_description_final"] = extent_description_final


    # 3XX -> notes and physical_description_notes
    notes = []
    for field in record.get_fields('300','301','302','303','304','305','306','307','308','310','311','312','313','314','316','317','318','320','322','323','324','325','328','830'):
        if field.tag == '300' and field['a']:
             # 300$a : notes : general
            notes.append({"note_type":"general", "value":field['a']})
        elif field.tag == '301' and field['a']:
            # 301$a : notes : identifier
            notes.append({"note_type":"identifier", "value":field['a']})
        elif field.tag == '302' and field['a']:
            # 302$a : notes : encoded_information
            notes.append({"note_type":"encoded_information", "value":field['a']})
        elif field.tag == '303' and field['a']:
            # 303$a : notes : description
            notes.append({"note_type":"description", "value":field['a']})
        elif field.tag == '304' and field['a']:
            # 304$a : notes : title
            notes.append({"note_type":"title", "value":field['a']})
        elif field.tag == '305' and field['a']:
            # 305$a : notes : edition
            notes.append({"note_type":"edition", "value":field['a']})
        elif field.tag == '306' and field['a']:
            # 306$a : notes : publications
            notes.append({"note_type":"publications", "value":field['a']})
        elif field.tag == '307' and field['a']:
            # 307$a : physical_description_notes : physical_description
            physical_description_notes.append({"note_type":"physical_description", "value":field['a']})
        elif field.tag == '308' and field['a']:
            # 308$a : notes : series
            notes.append({"note_type":"series", "value":field['a']})
        elif field.tag == '310' and field['a']:
            # 310$a : physical_description_notes : binding
            physical_description_notes.append({"note_type":"binding", "value":field['a']})
        elif field.tag == '311' and field['a']:
            # 311$a : notes : link_fields
            notes.append({"note_type":"link_fields", "value":field['a']})
        elif field.tag == '312' and field['a']:
            # 312$a : notes : related_titles
            notes.append({"note_type":"related_titles", "value":field['a']})
        elif field.tag == '313' and field['a']:
            # 313$a : notes : subject_completeness
            notes.append({"note_type":"subject_completeness", "value":field['a']})
        elif field.tag == '314' and field['a']:
            # 314$a : notes : authors
            notes.append({"note_type":"authors", "value":field['a']})
        elif field.tag == '316' and field['a']:
            # 316$a : notes : copy
            notes.append({"note_type":"copy", "value":field['a']})
        elif field.tag == '317' and field['a']:
            # 317$a : notes : ownership
            notes.append({"note_type":"ownership", "value":field['a']})
        elif field.tag == '318' and field['a']:
            # 318$a : notes : conservation_history
            notes.append({"note_type":"conservation_history", "value":field['a']})
        elif field.tag == '320' and field['a']:
            # 320$a : notes : bibliography
            notes.append({"note_type":"bibliography", "value":field['a']})
        elif field.tag == '321' and field['a']:
            # 321$a : notes : index
            notes.append({"note_type":"index", "value":field['a']})
        elif field.tag == '322' and field['a']:
            # 322$a : notes : credits
            notes.append({"note_type":"credits", "value":field['a']})
        elif field.tag == '323' and field['a']:
            # 323$a : notes : performers
            notes.append({"note_type":"performers", "value":field['a']})
        elif field.tag == '324' and field['a']:
            # 324$a : notes : original_version
            notes.append({"note_type":"original_version", "value":field['a']})
        elif field.tag == '325' and field['a']:
            # 325$a : notes : reproduction
            notes.append({"note_type":"reproduction", "value":field['a']})
        elif field.tag == '328' and field['a']:
            # 328$a : notes : thesis
            notes.append({"note_type":"thesis", "value":field['a']})
        elif field.tag == '830' and field['a']:
            # 830$a : notes : cataloging
            notes.append({"note_type":"cataloging", "value":field['a']})

    if notes:
        document["notes"] = notes
    if physical_description_notes:
        document["physical_description_notes"] = physical_description_notes

    # 315$a ; 328$b ; 336$a -> rec_type_description
    rec_type_description = ""
    if record['315'] is not None and record['315']['a'] is not None:
        rec_type_description = record['315']['a'].strip() + " "
    if record['328'] is not None and record['328']['b'] is not None:
        rec_type_description = rec_type_description + record['328']['b'].strip() + " "
    if record['336'] is not None and record['336']['a'] is not None:
        rec_type_description = rec_type_description + record['336']['a'].strip() + " "
    if rec_type_description.strip():
        document["rec_type_description"] = rec_type_description.strip()

    # 326$a -> frequency
    if record['326'] is not None and record['326']['a'] is not None:
        document["frequency"] = record['326']['a'].strip()

    # 327 & 359 -> table_of_contentss[i]
    table_of_contentss = []
    for field in record.get_fields('327','359'):
        for subfield in field:
            if subfield[1] is not None and subfield[1].strip() is not None:
                if subfield[0] == "a":
                    table_of_contentss.append({"content_type":"content","value":subfield[1].strip()})
                elif subfield[0] == "b":
                    table_of_contentss.append({"content_type":"h1","value":subfield[1].strip()})
                elif subfield[0] == "c":
                    table_of_contentss.append({"content_type":"h2","value":subfield[1].strip()})
                elif subfield[0] == "d":
                    table_of_contentss.append({"content_type":"h3","value":subfield[1].strip()})
                elif subfield[0] == "e":
                    table_of_contentss.append({"content_type":"h4","value":subfield[1].strip()})
                elif subfield[0] == "f":
                    table_of_contentss.append({"content_type":"h5","value":subfield[1].strip()})
                elif subfield[0] == "g":
                    table_of_contentss.append({"content_type":"h6","value":subfield[1].strip()})
                elif subfield[0] == "h":
                    table_of_contentss.append({"content_type":"h7","value":subfield[1].strip()})
                elif subfield[0] == "i":
                    table_of_contentss.append({"content_type":"h8","value":subfield[1].strip()})
                elif subfield[0] == "p":
                    table_of_contentss.append({"content_type":"part_page_begin","value":subfield[1].strip()})
                elif subfield[0] == "u":
                    table_of_contentss.append({"content_type":"url","value":subfield[1].strip()})
                elif subfield[0] == "v":
                    table_of_contentss.append({"content_type":"part_number","value":subfield[1].strip()})
                elif subfield[0] == "z":
                    table_of_contentss.append({"content_type":"author","value":subfield[1].strip()})
    if table_of_contentss:
        document["table_of_contentss"] = table_of_contentss

    # 328$d -> date_defence
    if record['328'] is not None and record['328']['d'] is not None:
        document["date_defence"] = record['328']['d'].strip()

    # 330 -> descriptions[i]/value
    if record['330'] is not None:
        descriptions = []
        for field in record.get_fields('330'):
            if field.get_subfields('a'):
                for subfield_value in field.get_subfields('a'):
                    descriptions.append({"value": subfield_value, "language": "und"})
        if descriptions:
            document["descriptions"] = descriptions

    # 332 -> citations[i]

    # 333 -> target_audiences

    # 334 -> awards

    # 337 -> requirements

    # 345 -> acquisitions[i]

    # 4XX -> Related items
    relateditems_dict = {
        '410': ("seriess", constants.DOC_TYPE_SERIES),
        '411': ("sub_series", constants.DOC_TYPE_SERIES),
        '412': ("is_offprint_ofs", "same"),
        '413': ("has_offprints", "same"),
        '421': ("has_supplements", "same"),
        '422': ("is_supplement_ofs", "same"),
        '423': ("is_published_withs", "same"),
        '424': ("is_updated_bys", "same"),
        '425': ("updates", "same"),
        '430': ("continues", "same"),
        '431': ("partially_continues", "same"),
        '432': ("replaces", "same"),
        '433': ("partially_replaces", "same"),
        '434': ("absorbs", "same"),
        '435': ("partially_absorbs", "same"),
        '436': ("is_merged_froms", "same"),
        '437': ("is_splitted_froms", "same"),
        '440': ("becomes", "same"),
        '441': ("partially_becomes", "same"),
        '442': ("is_replaced_bys", "same"),
        '443': ("is_partially_replaced_bys", "same"),
        '444': ("is_absorbed_intos", "same"),
        '445': ("is_partially_absorbed_intos", "same"),
        '446': ("is_split_intos", "same"),
        '447': ("merges_withs", "same"),
        '448': ("re_becomes", "same"),
        '451': ("has_formats", "same"),
        '452': ("has_formats", "same"),
        '453': ("has_translations", "same"),
        '454': ("is_translation_ofs", "same"),
        '455': ("is_version_ofs", "same"),
        '456': ("has_versions", "same"),
        '461': ("is_part_ofs", "is_part_ofs"),
        '462': ("has_parts", "has_parts"),
        '463': ("is_part_ofs", "is_part_ofs"),
        '464': ("has_parts", "has_parts"),
        '470': ("is_review_ofs", "is_review_ofs"),
        '481': ("is_bound_withs", "same"),
        '482': ("is_bound_afters", "same"),
        '488': ("has_relation_withs", "same")
    }
    if record.get_fields(*relateditems_dict.keys()):
        for field in record.get_fields(*relateditems_dict.keys()):
            related = Document()
            has_t = False
            if field.get_subfields('t'):
                has_t = True
            creators = []
            publication_places = []
            title_alternatives = []
            identifiers = []
            publishers = []
            seriess = []
            resources = []
            for subfield in field:
                # todo : trouble with "Technique des zones imbriquées"
                if subfield[1] is not None and subfield[1].strip() is not None:
                    if subfield[0] == "0":
                        related["rec_id"] = subfield[1].strip()
                    elif subfield[0] == "3":
                        related["rec_id"] = subfield[1].strip()
                    elif subfield[0] in ["a", "f", "g"]:
                        if not has_t and subfield[0] == "a" and "title" not in related:
                            related["title"] = subfield[1].strip()
                        else :
                            role = "aut"
                            formatted_name = subfield[1].strip().replace(",...","")
                            # toto : insert this to formatted_name_to_creator
                            if formatted_name.startswith("par "):
                                formatted_name = formatted_name[4:]
                            elif formatted_name.startswith("publ. sous la dir. de "):
                                formatted_name = formatted_name[22:]
                                role = "pbd"
                            creator = creator_service.formatted_name_to_creator(formatted_name, None, role)
                            if creator:
                                creators.append(creator)
                    elif subfield[0] == "b":
                        related["rec_type_description"] = subfield[1].strip()
                    elif subfield[0] == "c":
                        publication_places.append(subfield[1].strip())
                    elif subfield[0] == "d":
                        related["date_issued"] = subfield[1].strip()
                    elif subfield[0] == "e":
                        related["edition"] = subfield[1].strip()
                    elif subfield[0] in ["h", "v"]:
                        related["part_number"] = subfield[1].strip()
                    elif subfield[0] == "i":
                        related["part_name"] = subfield[1].strip()
                    elif subfield[0] == "l":
                        title_alternatives.append(subfield[1].strip())
                    elif subfield[0] == "m":
                        identifiers.append({"id_type": "ismn", "value": subfield[1].strip()})
                    elif subfield[0] == "n":
                        publishers.append(subfield[1].strip())
                    elif subfield[0] == "o":
                        related["title_sub"] = subfield[1].strip()
                    elif subfield[0] == "p":
                        related["extent_description"] = subfield[1].strip()
                    elif subfield[0] == "s":
                        series = Document()
                        series["rec_type"] = constants.DOC_TYPE_SERIES
                        series["title"] = subfield[1].strip()
                        seriess.append(series)
                    elif subfield[0] == "t":
                        related["title"] = subfield[1].strip()
                    elif subfield[0] == "u":
                        resource = Resource()
                        resource["rec_type"] = "ResourceRemote"
                        resource["url"] = subfield[1].strip()
                        resources.append(resource)
                    elif subfield[0] == "x":
                        identifiers.append({"id_type": "issn", "value": subfield[1].strip()})
                    elif subfield[0] == "y":
                        identifiers.append({"id_type": "isbn", "value": subfield[1].strip()})
                    elif subfield[0] == "z":
                        identifiers.append({"id_type": "coden", "value": subfield[1].strip()})
            if creators:
                related["creators"] = creators
            if publication_places:
                related["publication_places"] = publication_places
            if title_alternatives:
                related["title_alternatives"] = title_alternatives
            if identifiers:
                related["identifiers"] = identifiers
            if publishers:
                related["publishers"] = publishers
            if seriess:
                related["seriess"] = seriess
            if resources:
                related["resources"] = resources
            if related:
                # debug
                #logging.debug("document.rec_type: {}".format(document["rec_type"]))
                #logging.debug("document.title: {}".format(document["title"]))
                #logging.debug("field: {}".format(field))
                # rec_type
                if relateditems_dict[field.tag][1] == "same":
                    related["rec_type"] = document["rec_type"]
                elif relateditems_dict[field.tag][1] == constants.DOC_TYPE_SERIES:
                    related["rec_type"] = constants.DOC_TYPE_SERIES
                elif relateditems_dict[field.tag][1] == "is_part_ofs":
                    related["rec_type"] = metajson_service.get_is_part_of_rec_type_from_root_rec_type(document["rec_type"])
                elif relateditems_dict[field.tag][1] == "has_parts":
                    related["rec_type"] = metajson_service.get_has_part_rec_type_from_root_rec_type(document["rec_type"])
                elif relateditems_dict[field.tag][1] == "is_review_ofs":
                    related["rec_type"] = constants.DOC_TYPE_BOOK
                else:
                    related["rec_type"] = constants.DOC_TYPE_DOCUMENT
                if related["rec_type"] == constants.DOC_TYPE_DOCUMENT and "rec_type_description" in related:
                    if related["rec_type_description"] == "Images animées":
                        related["rec_type"] = constants.DOC_TYPE_VIDEORECORDING
                #logging.debug("related.rec_type: {}".format(related["rec_type"]))
                # title
                if "title" not in related:
                    related["title"] = ""
                #logging.debug("related.title: {}".format(related["title"]))
                #logging.debug("related property: {}".format(relateditems_dict[field.tag][0]))
                # add to document properties
                if relateditems_dict[field.tag][0] not in document:
                    document[relateditems_dict[field.tag][0]] = []
                document[relateditems_dict[field.tag][0]].append(related)


    # 500 -> title_uniforms[i]
    # 503 -> title_forms[i]
    # 510 -> title_alternatives[i]
    # 517 -> title_alternatives[i]
    # 531 -> title_abbreviateds[i]
    # 541 -> title_translateds[i]
    # $a -> title, title_non_sort
    # $e -> title_sub
    # $h -> part_number
    # $i -> part_name
    # $m -> language
    titles_dict = {
        '500': "title_uniforms",
        '503': "title_forms",
        '510': "title_alternatives",
        '517': "title_alternatives",
        '531': "title_abbreviateds",
        '541': "title_translateds"
    }
    if record.get_fields(*titles_dict.keys()):
        for field in record.get_fields(*titles_dict.keys()):
            title_info = {}
            for subfield in field:
                if subfield[1] is not None and subfield[1].strip() is not None:
                    if subfield[0] == "a":
                        title_info["title"] = subfield[1].strip()
                    elif subfield[0] == "e":
                        title_info["title_sub"] = subfield[1].strip()
                    elif subfield[0] == "h":
                        title_info["part_number"] = subfield[1].strip().replace(",", "")
                    elif subfield[0] == "i":
                        title_info["part_name"] = subfield[1].strip()
                    elif subfield[0] in ["m", "z"]:
                        lang = language_service.convert_unknown_format_to_rfc5646(subfield[1].strip())
                        if lang:
                            title_info["language"] = lang
            if title_info:
                if titles_dict[field.tag] not in document:
                    document[titles_dict[field.tag]] = []
                document[titles_dict[field.tag]].append(title_info)


    # subjects
    # 600, 601, 602 -> subject agents
    # 604, 605 -> subject documents
    # 606 -> Nom commun *
    # 607 -> Nom géographique
    # 608 -> Forme, genre ou caractéristiques matérielles
    # 610 -> keywords
    # 615 -> Catégorie sujet (provisoire)
    # 616 -> Vedette matière - Nom de marque
    # 617 -> Vedette matière - Nom géographique hiérarchisé
    # 620 -> Lieu et date de publication, de représentation ou d’enregistrement, etc.
    # 621 -> Lieu et date de provenance
    # 626 -> Accès par les données techniques (ressources électroniques) [zone obsolète]
    # 660 -> Code d’aire géographique
    # 670 -> PRECIS
    subject_types_dict = {
        '600': "agent",
        '601': "agent",
        '602': "agent",
        '606': "topic",
        '607': "geo",
        '608': "genre",
        '615': "unknown",
        '616': "agent",
        '617': "geo",
        '620': "unknown",
        '621': "unknown",
        '626': "unknown",
        '660': "geo",
        '670': "unknown"
    }
    subjects = []
    if record.get_fields(*subject_types_dict.keys()):
        for field in record.get_fields(*subject_types_dict.keys()):
            subject = {}
            if field.tag in subject_types_dict:
                subject_type = subject_types_dict[field.tag]
            else:
                subject_type = "unknown"
            agents = []
            genres = []
            geographics = []
            temporals = []
            topics = []
            do_common_part = True
            if field.tag in ['600', '601', '602', '616']:
                do_common_part = True
                creator = extract_unimarc_creator(field)
                if creator and "agent" in creator:
                    agents.append(creator["agent"])
            elif field.tag == '617':
                do_common_part = False
                if subfield[1] is not None and subfield[1].strip() is not None:
                    if subfield[0] == "a":
                        geographics.append({"geo_type": "country", "value": subfield[1].strip()})
                    elif subfield[0] == "b":
                        geographics.append({"geo_type": "state", "value": subfield[1].strip()})
                    elif subfield[0] == "c":
                        geographics.append({"geo_type": "region", "value": subfield[1].strip()})
                    elif subfield[0] == "d":
                        geographics.append({"geo_type": "city", "value": subfield[1].strip()})
                    elif subfield[0] == "e":
                        geographics.append({"geo_type": "place", "value": subfield[1].strip()})
                    elif subfield[0] == "k":
                        geographics.append({"geo_type": "city_section", "value": subfield[1].strip()})
                    elif subfield[0] == "m":
                        geographics.append({"geo_type": "area", "value": subfield[1].strip()})
                    elif subfield[0] == "n":
                        geographics.append({"geo_type": "extraterrestrial_area", "value": subfield[1].strip()})
                    elif subfield[0] == "o":
                        geographics.append({"geo_type": "continent", "value": subfield[1].strip()})
            if do_common_part:
                for subfield in field:
                    if subfield[1] is not None and subfield[1].strip() is not None:
                        if subfield[0] == "2":
                            subject["authority"] = subfield[1].strip()
                        if subfield[0] == "3":
                            subject["subject_id"] = subfield[1].strip()
                        if subfield[0] == "a":
                            if field.tag == '606':
                                topics.append({"topic_type": "main", "value": subfield[1].strip()})
                            elif field.tag == '607':
                                geographics.append({"geo_type": "main", "value": subfield[1].strip()})
                            elif field.tag == '608':
                                genres.append(subfield[1].strip())
                        if subfield[0] == "j":
                            genres.append(subfield[1].strip())
                        if subfield[0] == "x":
                            topics.append({"topic_type": "second", "value": subfield[1].strip()})
                        if subfield[0] == "y":
                            geographics.append({"geo_type": "second", "value": subfield[1].strip()})
                        if subfield[0] == "z":
                            temporals.append({"temporal_type": "second", "value": subfield[1].strip()})
            if agents:
                subject["agents"] = agents
            if genres:
                subject["genres"] = genres
            if geographics:
                subject["geographics"] = geographics
            if temporals:
                subject["temporals"] = temporals
            if topics:
                subject["topics"] = topics
            if subject:
                subject["subject_type"] = subject_type
                subjects.append(subject)
    if subjects:
        document["subjects"] = subjects


    # 328$c, 675$a, 676$a, 680$a, 686$a -> classifications
    if record.get_fields('328','675','676','680','686'):
        class_thesis = []
        class_udc = []
        class_ddc = []
        class_lcc = []
        classifications = {}
        for field in record.get_fields('328','675','676','680','686'):
            if field.tag == '328' and field['c'] is not None and field['c'].strip():
                class_thesis.append(field['c'].strip())
            if field['a'] is not None and field['a'].strip():
                if field.tag == '675':
                    class_udc.append(field['a'].strip())
                elif field.tag == '676':
                    class_ddc.append(field['a'].strip())
                elif field.tag == '680':
                    class_lcc.append(field['a'].strip())
                elif field.tag == '686':
                    if field['2']:
                        if field['2'] not in classifications:
                            classifications[field['2']] = []
                        classifications[field['2']].append(field['a'].strip())
        if class_thesis:
            classifications["thesis"] = class_thesis
        if class_udc:
            classifications["udc"] = class_udc
        if class_ddc:
            classifications["ddc"] = class_ddc
        if class_lcc:
            classifications["lcc"] = class_lcc
        if classifications:
            document["classifications"] = classifications

    # 7XX -> creators
    # 328$e -> creators dgg
    creators = []
    fields_creators = record.get_fields("700", "701", "702", "710", "711", "712", "716", "720", "721", "722", "730")
    if fields_creators:
        for field in fields_creators:
            creator = extract_unimarc_creator(field)
            if creator:
                creators.append(creator)
    if record['328'] is not None and record['328']['e'] is not None and record['328']['e'].strip():
        orgunit = Orgunit()
        orgunit["name"] = record['328']['e'].strip()
        creator = Creator()
        creator["agent"] = orgunit
        creator["roles"] = ["dgg"]
        creators.append(creator)
    if creators:
        document["creators"] = creators

    # 801 -> rec_source
    if record.get_fields('801'):
        if record['801']['a'] is not None:
            document["rec_source_country"] = record['801']['a']
        if record['801']['b'] is not None:
            document["rec_source"] = record['801']['b']
        if record['801']['c'] is not None:
            document["rec_source_date"] = date_service.parse_to_iso8601(record['801']['c'])
        if record['801']['g'] is not None:
            document["rec_source_cataloging_rule"] = record['801']['g']
        if record['801']['2'] is not None:
            document["rec_source_cataloging_rule"] = record['801']['2']
        if record['801']['h'] is not None:
            document["rec_source_rec_id"] = record['801']['h']

    # 991$d -> rights/determination_date
    # 991$n -> rights/determination_note
    if record.get_fields('991') and (record['991']['d'] is not None or record['991']['n'] is not None):
        rights = Rights()
        rights["rights_type"] = "unknown"
        if record['991']['d'] is not None:
            rights["determination_date"] = record['991']['d']
        if record['991']['n'] is not None:
            rights["determination_note"] = record['991']['n']
        document["rights"] = rights

    # resources
    # 856 : links -> resources
    resources = []
    fields_856 = record.get_fields('856')
    if fields_856:
        for field_856 in fields_856:
            resource = Resource()
            resource["rec_type"] = "ResourceRemote"
            if field_856.get_subfields('u'):
                resource["url"] = field_856.get_subfields('u')[0]
            if field_856.get_subfields('z'):
                resource["labels"] = [{"value":field_856.get_subfields('z')[0], "language":"und"}]
            if resource:
                resources.append(resource)

    # 995 : holdings / copies -> resources
    fields_995 = record.get_fields('995')
    if fields_995:
        for field_995 in fields_995:
            resource = Resource()
            resource["rec_type"] = "ResourcePhysical"
            # $b -> institution_identifiers[].value ex: 751072303
            if field_995.get_subfields('b'):
                resource["institution_identifiers"] = [{"value": field_995.get_subfields('b')[0], "id_type": "RBCCN"}]
            # $c -> location ex: BIB01
            if field_995.get_subfields('c'):
                resource["location"] = field_995.get_subfields('c')[0]
            # $d -> physical_sub_location ex: MAG1
            if field_995.get_subfields('d'):
                resource["sub_location"] = field_995.get_subfields('d')[0]
            # $e -> collection ex: cad
            if field_995.get_subfields('e'):
                resource["collection"] = field_995.get_subfields('e')[0]
            # $f -> rec_id ex: 00000000926980
            if field_995.get_subfields('f'):
                resource["rec_id"] = field_995.get_subfields('f')[0]
            # $k -> call_number ex: BR.8°0947(13)
            if field_995.get_subfields('k'):
                resource["call_number"] = field_995.get_subfields('k')[0].replace("Â°", "°")
            # $l -> part_number ex: 2
            if field_995.get_subfields('l'):
                resource["part_number"] = field_995.get_subfields('l')[0]
            # $o -> category ex: L1
            if field_995.get_subfields('o'):
                resource["category"] = field_995.get_subfields('o')[0]
            # $p -> is_periodical ex: p
            if field_995.get_subfields('p') and field_995.get_subfields('p')[0] == "p":
                resource["is_periodical"] = True
            # $r -> availability_code ex: DI
            if field_995.get_subfields('r'):
                resource["availability_code"] = field_995.get_subfields('r')[0]
            # $s -> rec_modified_date ex: YYYYMMDD
            if field_995.get_subfields('s'):
                resource["rec_modified_date"] = field_995.get_subfields('s')[0]
            # $u -> notes[i]/value ex: Ceci est une note
            if field_995.get_subfields('u'):
                resource["notes"] = [{"value":field_995.get_subfields('u')[0],"language":"und"}]
            # $v -> issue_number ex: Vol. 52, no 1>6, 2002 : vol. relié
            if field_995.get_subfields('v'):
                resource["issue_number"] = field_995.get_subfields('v')[0]
            # $w -> issue_date ex: 2002
            if field_995.get_subfields('w'):
                resource["issue_date"] = field_995.get_subfields('w')[0]
            if resource:
                resources.append(resource)
    if resources is not None:
        document["resources"] = resources

    metajson_service.pretty_print_document(document)
    return document


def extract_unimarc_identifier(record, field, subfield, id_type, identifiers):
    identifier = None
    if record is not None and field is not None and record[field] is not None:
        if subfield == "data" and record[field].data is not None:
            identifier = {"id_type": id_type, "value": record[field].data}
        elif subfield is not None and record[field][subfield] is not None:
            if field == '014' and record[field]['2'] is not None:
                # case : id_type other than sici
                id_type = record[field]['2']
            identifier = {"id_type": id_type, "value": record[field][subfield]}
    if identifier:
        identifiers.append(identifier)


def extract_unimarc_creator(field):
    if field:
        creator = Creator()
        # $4 -> role
        if field['4'] and field['4'] in creator_service.role_unimarc_to_role_code:
            creator["roles"] = [creator_service.role_unimarc_to_role_code[field['4']]]
        elif field.tag in ["700", "701", "710", "711", "720", "721", "740", "741"]:
            creator["roles"] = ["aut"]
        else:
            creator["roles"] = ["ctb"]

        # 600, 700, 701, 702 -> Person
        if field.tag in ["600", "700", "701", "702"]:
            # Person
            person = Person()
            if field.subfields:
                if field.get_subfields('a'):
                    # name_family
                    person["name_family"] = "".join(field.get_subfields('a'))
                if field.get_subfields('b'):
                    # name_given
                    person["name_given"] = "".join(field.get_subfields('b'))
                if field.get_subfields('f'):
                    dates = format_dates_as_list(field.get_subfields('f'))
                    if dates:
                        person["date_birth"] = dates[0]
                        if len(dates) > 1:
                            person["date_death"] = dates[1]
                if person:
                    creator["agent"] = person

        # 601, 710, 711, 712 -> Orgunit, Event
        elif field.tag in ["601", "710", "711", "712"]:
            if field.subfields:
                if field.indicator1 == "1":
                    # Event
                    event = Event()
                    if field.get_subfields('a'):
                        event["title"] = "".join(field.get_subfields('a'))
                    if field.get_subfields('d'):
                        event["number"] = "".join(field.get_subfields('d'))
                    if field.get_subfields('e'):
                        event["place"] = "".join(field.get_subfields('e'))
                    if field.get_subfields('f'):
                        event["date_begin"] = "".join(field.get_subfields('f'))
                    if event:
                        creator["agent"] = event
                else:
                    # Orgunit
                    orgunit = Orgunit()
                    name = []
                    if field.get_subfields('3'):
                        orgunit["identifiers"] = field.get_subfields('3')[0]
                    if field.get_subfields('a'):
                        name.extend(field.get_subfields('a'))
                    if field.get_subfields('b'):
                        # todo division
                        name.append(". ")
                        name.extend(field.get_subfields('b'))
                    if name:
                        orgunit["name"] = "".join(name)
                    if field.get_subfields('c'):
                        addresses = []
                        for locality in field.get_subfields('c'):
                            address = {"locality_city_town" : locality.replace("(","").replace(")","").strip()}
                            addresses.append(address)
                        if addresses:
                            orgunit["addresses"] = addresses
                    dates = format_dates_as_list(field.get_subfields('f'))
                    if dates:
                        orgunit["date_foundation"] = dates[0]
                        if len(dates) > 1:
                            orgunit["date_dissolution"] = dates[1]
                    if orgunit:
                        creator["agent"] = orgunit

        # 616, 716 -> Brand (Nom de marque)
        elif field.tag in ["616", "716"]:
            if field.subfields:
                brand = Brand()
                if field.get_subfields('a'):
                    brand["name"] = "".join(field.get_subfields('a'))
                if field.get_subfields('f'):
                    dates = format_dates_as_list(field.get_subfields('f'))
                    if dates:
                        brand["date_foundation"] = dates[0]
                        if len(dates) > 1:
                            brand["date_dissolution"] = dates[1]
                if brand:
                    creator["agent"] = brand

        # 602, 720, 721, 722 -> Family
        elif field.tag in ["602", "720", "721", "722"]:
            if field.subfields:
                # Family
                family = Family()
                if field.get_subfields('a'):
                    # name_family
                    family["name_family"] = "".join(field.get_subfields('a'))
                if field.get_subfields('f'):
                    dates = format_dates_as_list(field.get_subfields('f'))
                    if dates:
                        family["date_birth"] = dates[0]
                        if len(dates) > 1:
                            family["date_death"] = dates[1]
                if family:
                    creator["agent"] = family


        elif field.tag == "730":
            # todo Intellectual responsability
            pass

        if creator:
            return creator
    

def format_dates_as_list(dates):
    if dates:
        # (1811-1882)
        # todo : pb with 710$c that can be another think than a date..
        return dates[0].replace("(","").replace(")","").replace("-....","").split("-")
