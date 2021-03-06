#!/usr/bin/python
# -*- coding: utf-8 -*-
# coding=utf-8

import logging
import xml.etree.ElementTree as ET

from biblib.metajson import Document
from biblib.metajson import Resource
from biblib.services import creator_service
from biblib.services import language_service
from biblib.services import metajson_service
from biblib.util import constants

endnote_import_note = False
endnote_import_research_note = False
endnote_import_keywords = False

# EndNote8 ref-type
# sources:
# https://drupal.org/node/344898
# http://www.users.muohio.edu/darcusb/files/endnote-xml.tar.gz

# 1: not used
TYPE_ARTWORK = "2"
TYPE_AUDIOVISUAL_MATERIAL = "3"
TYPE_BILL = "4"
TYPE_BOOK_SECTION = "5"
TYPE_BOOK = "6"
TYPE_CASE = "7"
# 8: not used
TYPE_COMPUTER_PROGRAM = "9"
TYPE_CONFERENCE_PROCEEDINGS = "10"
# 11: not used
TYPE_WEB_PAGE = "12"
TYPE_GENERIC = "13"
TYPE_HEARING = "14"
# 15: not used
# 16: not used
TYPE_JOURNAL_ARTICLE = "17"
# 18: not used
TYPE_MAGAZINE_ARTICLE = "19"
TYPE_MAP = "20"
TYPE_FILM_OR_BROADCAST = "21"
# 22: not used
TYPE_NEWSPAPER_ARTICLE = "23"
# 24: not used
TYPE_PATENT = "25"
TYPE_PERSONAL_COMMUNICATION = "26"
TYPE_REPORT = "27"
TYPE_EDITED_BOOK = "28"
# 29: not used
# 30: not used
TYPE_STATUTE = "31"
TYPE_THESIS = "32"
# 33: not used
TYPE_UNPUBLISHED_WORK = "34"
# 35: not used
TYPE_MANUSCRIPT = "36"
TYPE_FIGURE = "37"
TYPE_CHART_OR_TABLE = "38"
TYPE_EQUATION = "39"
# 40: not used
# 41: not used
# 42: not used
TYPE_ELECTRONIC_JOURNAL = "43"
TYPE_ELECTRONIC_BOOK = "44"
TYPE_ONLINE_DATABASE = "45"
TYPE_GOVERNMENT_REPORT_OR_DOCUMENT = "46"
TYPE_CONFERENCE_PAPER = "47"
TYPE_ONLINE_MULTIMEDIA = "48"
TYPE_CLASSICAL_WORK = "49"
TYPE_LEGAL_RULE_OR_REGULATION = "50"
# 51: not used
TYPE_DICTIONARY = "52"
TYPE_ENCYCLOPEDIA = "53"
TYPE_GRANT = "54"

endnote_record_type_to_metajson_document_type = {
    TYPE_ARTWORK: constants.DOC_TYPE_IMAGE,  #constants.DOC_TYPE_ARTWORK
    TYPE_AUDIOVISUAL_MATERIAL: constants.DOC_TYPE_AUDIORECORDING,
    TYPE_BILL: constants.DOC_TYPE_BILL,
    TYPE_BOOK: constants.DOC_TYPE_BOOK,
    TYPE_BOOK_SECTION: constants.DOC_TYPE_BOOKPART,
    TYPE_CASE: constants.DOC_TYPE_LEGALCASE,  # add field
    TYPE_CHART_OR_TABLE: constants.DOC_TYPE_CHART,  # add field
    TYPE_CLASSICAL_WORK: constants.DOC_TYPE_MUSICALSCORE,
    TYPE_COMPUTER_PROGRAM: constants.DOC_TYPE_SOFTWARE,
    TYPE_CONFERENCE_PAPER: constants.DOC_TYPE_CONFERENCEPAPER,
    TYPE_CONFERENCE_PROCEEDINGS: constants.DOC_TYPE_CONFERENCEPROCEEDINGS,
    TYPE_DICTIONARY: constants.DOC_TYPE_DICTIONARY,
    TYPE_EDITED_BOOK: constants.DOC_TYPE_BOOK,  #constants.DOC_TYPE_EDITEDBOOK
    TYPE_ENCYCLOPEDIA: constants.DOC_TYPE_ENCYCLOPEDIA,
    TYPE_ELECTRONIC_JOURNAL: constants.DOC_TYPE_EJOURNAL,
    TYPE_ELECTRONIC_BOOK: constants.DOC_TYPE_EBOOK,
    TYPE_ENCYCLOPEDIA: constants.DOC_TYPE_ENCYCLOPEDIA,
    TYPE_EQUATION: constants.DOC_TYPE_EQUATION,
    TYPE_FIGURE: constants.DOC_TYPE_IMAGE,
    TYPE_FILM_OR_BROADCAST: constants.DOC_TYPE_FILM,
    TYPE_GENERIC: constants.DOC_TYPE_UNPUBLISHEDDOCUMENT,
    TYPE_GOVERNMENT_REPORT_OR_DOCUMENT: constants.DOC_TYPE_GOVERNMENTPUBLICATION,
    TYPE_GRANT: constants.DOC_TYPE_GRANT,
    TYPE_HEARING: constants.DOC_TYPE_HEARING,
    TYPE_JOURNAL_ARTICLE: constants.DOC_TYPE_JOURNALARTICLE,
    TYPE_LEGAL_RULE_OR_REGULATION: constants.DOC_TYPE_STATUTE,
    TYPE_MAGAZINE_ARTICLE: constants.DOC_TYPE_MAGAZINEARTICLE,
    TYPE_MANUSCRIPT: constants.DOC_TYPE_MANUSCRIPT,
    TYPE_MAP: constants.DOC_TYPE_MAP,
    TYPE_NEWSPAPER_ARTICLE: constants.DOC_TYPE_NEWSPAPERARTICLE,
    TYPE_ONLINE_DATABASE: constants.DOC_TYPE_WEBSITE,
    TYPE_ONLINE_MULTIMEDIA: constants.DOC_TYPE_WEBPAGE,
    TYPE_PATENT: constants.DOC_TYPE_PATENT,
    TYPE_PERSONAL_COMMUNICATION: constants.DOC_TYPE_UNPUBLISHEDDOCUMENT,
    TYPE_REPORT: constants.DOC_TYPE_REPORT,
    TYPE_STATUTE: constants.DOC_TYPE_STATUTE,
    TYPE_THESIS: constants.DOC_TYPE_DOCTORALTHESIS,
    TYPE_UNPUBLISHED_WORK: constants.DOC_TYPE_UNPUBLISHEDDOCUMENT,
    TYPE_WEB_PAGE: constants.DOC_TYPE_WEBSITE
}

endnote_record_type_to_metajson_document_is_part_of_type = {
    TYPE_BOOK_SECTION: constants.DOC_TYPE_BOOK,
    TYPE_CONFERENCE_PAPER: constants.DOC_TYPE_CONFERENCEPROCEEDINGS,
    TYPE_JOURNAL_ARTICLE: constants.DOC_TYPE_JOURNAL,
    TYPE_MAGAZINE_ARTICLE: constants.DOC_TYPE_MAGAZINE,
    TYPE_NEWSPAPER_ARTICLE: constants.DOC_TYPE_NEWSPAPER
}

unpublished_types = [
    constants.DOC_TYPE_ANCIENTTEXT, 
    constants.DOC_TYPE_ARTWORK, 
    constants.DOC_TYPE_AUDIOPART, 
    constants.DOC_TYPE_AUDIORECORDING, 
    constants.DOC_TYPE_BIBLIOGRAPHY, 
    constants.DOC_TYPE_CONFERENCECONTRIBUTION, 
    constants.DOC_TYPE_CONFERENCEPOSTER, 
    constants.DOC_TYPE_DOCUMENT, 
    constants.DOC_TYPE_MANUSCRIPT, 
    constants.DOC_TYPE_MAP, 
    constants.DOC_TYPE_MUSICRECORDING, 
    constants.DOC_TYPE_PATENT, 
    constants.DOC_TYPE_PERFORMANCE, 
    constants.DOC_TYPE_PERSONALCOMMUNICATION, 
    constants.DOC_TYPE_PHYSICALOBJECT, 
    constants.DOC_TYPE_REPORT, 
    constants.DOC_TYPE_SLIDE, 
    constants.DOC_TYPE_SPEECH, 
    constants.DOC_TYPE_UNPUBLISHEDDOCUMENT, 
    constants.DOC_TYPE_VIDEOPART, 
    constants.DOC_TYPE_VIDEORECORDING, 
    constants.DOC_TYPE_WORKINGPAPER, 
    constants.DOC_TYPE_WORKSHOP
]

def endnotexml_xmletree_to_metajson_list(endnotexml_root, source, rec_id_prefix, only_first_record):
    records_elements = endnotexml_root.find("records")
    records = records_elements.findall("record")

    if records:
        for record in records:
            yield endnotexml_record_to_metajson(record, source, rec_id_prefix)


def endnotexml_record_to_metajson(record, source, rec_id_prefix):
    document = Document()

    # TODO
    # translated_creators: /contributors/translated-authors/author/style
    # auth_address: /auth-address/style
    # label: /label/style
    # custom1

    # Extract endnote properties

    rec_id = record.find("rec-number").text
    endnote_type = record.find("ref-type").text
    rec_type = endnote_record_type_to_metajson_document_type[endnote_type]

    primary_creators = extract_creators(None, "aut", record, "./contributors/authors/author/style")
    secondary_creators = extract_creators(None, "pbd", record, "./contributors/secondary-authors/author/style")
    if endnote_type in [TYPE_BOOK, TYPE_BOOK_SECTION]:
        tertiary_creators = extract_creators(None, "pbd", record, "./contributors/tertiary-authors/author/style")
    elif endnote_type == TYPE_THESIS:
        tertiary_creators = extract_creators(None, "ths", record, "./contributors/tertiary-authors/author/style")
    elif endnote_type == TYPE_FILM_OR_BROADCAST:
        tertiary_creators = extract_creators(None, "pro", record, "./contributors/tertiary-authors/author/style")
    if endnote_type in [TYPE_BOOK, TYPE_BOOK_SECTION]:
        subsidiary_creators = extract_creators(None, "trl", record, "./contributors/subsidiary-authors/author/style")
    elif endnote_type == TYPE_FILM_OR_BROADCAST:
        subsidiary_creators = extract_creators(None, "act", record, "./contributors/subsidiary-authors/author/style")
    translated_creators = extract_creators(None, "trl", record, "./contributors/translated-authors/author/style")
    auth_address = extract_text(record, "./auth-address/style")

    title = extract_text(record, "./titles/title/style")
    title_secondary = extract_text(record, "./titles/secondary-title/style")
    title_tertiary = extract_text(record, "./titles/tertiary-title/style")
    title_alternative = extract_text(record, "./titles/alt-title/style")
    title_abbreviated = extract_text(record, "./titles/short-title/style")
    title_translated = extract_text(record, "./titles/translated-title/style")

    pages = extract_text(record, "./pages/style")
    part_volume = extract_text(record, "./volume/style")
    part_number = extract_text(record, "./number/style")
    extent_volumes = extract_text(record, "./num-vols/style")
    edition = extract_text(record, "./edition/style")
    part_section = extract_text(record, "./section/style")
    reprint_edition = extract_text(record, "./reprint-edition/style")
    keywords = extract_text(record, "./keywords/keyword/style")
    date_year = extract_text(record, "./dates/year/style")
    date_pub = extract_text(record, "./dates/pub-dates/date/style")
    publication_places_formatted = extract_text(record, "./pub-location/style")
    publishers_formatted = extract_text(record, "./publisher/style")
    orig_pub = extract_text(record, "./orig-pub/style")
    isbn_or_issn = extract_text(record, "./isbn/style")
    accessionnumber = extract_text(record, "./accession-num/style")
    callnumber = extract_text(record, "./call-num/style")
    if endnote_type == TYPE_WEB_PAGE:
        abstract = extract_text(record, "./pages/style")
    else:
        abstract = extract_text(record, "./abstract/style")
    label = extract_text(record, "./label/style")
    caption = extract_text(record, "./caption/style")
    note = extract_text(record, "./notes/style")
    reviewed_item = extract_text(record, "./reviewed-item/style")
    rec_type_description = extract_text(record, "./work-type/style")
    url = extract_text(record, "./urls/related-urls/url/style")
    custom1 = extract_text(record, "./custom1/style")
    custom2 = extract_text(record, "./custom2/style")
    custom3 = extract_text(record, "./custom3/style")
    custom4 = extract_text(record, "./custom4/style")
    custom5 = extract_text(record, "./custom5/style")
    custom6 = extract_text(record, "./custom6/style")
    custom7 = extract_text(record, "./custom7/style")
    doi = extract_text(record, "./electronic-resource-num/style")
    remote_database_name = extract_text(record, "./remote-database-name/style")
    remote_database_provider = extract_text(record, "./remote-database-provider/style")
    research_notes = extract_text(record, "./research-notes/style")
    language = extract_text(record, "./language/style")
    access_date = extract_text(record, "./access-date/style")

    # rec_id, rec_source
    document["rec_id"] = rec_id
    if source:
        document["rec_source"] = source

    # publishers_formatted, publication_places_formatted
    publishers = None
    publication_places = None
    if publishers_formatted:
        publishers = publishers_formatted.split("\r")
    if publication_places_formatted:
        publication_places = publication_places_formatted.split("\r")

    # type, is_part_of.type, is_part_of.is_part_of.type
    try:
        is_part_of_type = endnote_record_type_to_metajson_document_is_part_of_type[endnote_type]
    except:
        is_part_of_type = None

    is_part_of_is_part_of_type = None
    if title_secondary is not None:
        if endnote_type == TYPE_FIGURE:
            # how to determine the is_part_of type ?
            # if there is a volume or an issue number, it's a JournalArticle, else it's a Book or BookPart
            if part_volume is not None or part_number is not None:
                is_part_of_type = constants.DOC_TYPE_JOURNALARTICLE
                is_part_of_is_part_of_type = constants.DOC_TYPE_JOURNAL
            else:
                if title_translated is not None:
                    is_part_of_type = constants.DOC_TYPE_BOOKPART
                    is_part_of_is_part_of_type = constants.DOC_TYPE_BOOK
                else:
                    is_part_of_type = constants.DOC_TYPE_BOOK
        elif endnote_type == TYPE_FILM_OR_BROADCAST:
            rec_type = constants.DOC_TYPE_VIDEOPART
            is_part_of_type = constants.DOC_TYPE_VIDEORECORDING

    document["rec_type"] = rec_type
    document.set_key_if_not_none("rec_type_description", rec_type_description)

    # issn or isbn ?
    if is_part_of_type in [constants.DOC_TYPE_JOURNAL, constants.DOC_TYPE_NEWSPAPER, constants.DOC_TYPE_MAGAZINE]:
        isbn_or_issn_type = "issn"
    else:
        isbn_or_issn_type = "isbn"

    # is_part_of, is_part_of.is_part_of
    if is_part_of_type is not None and title_secondary:
        is_part_of = Document()
        is_part_of.set_key_if_not_none("rec_type", is_part_of_type)
        is_part_of.set_key_if_not_none("title", title_secondary)

        if is_part_of_is_part_of_type is not None:
            # is_part_of in case of is_part_of.is_part_of
            # creators with role aut
            is_part_of.add_creators(creator_service.change_contibutors_role(secondary_creators, "aut"))

            # is_part_of.is_part_of
            is_part_of_is_part_of = Document()
            is_part_of_is_part_of.set_key_if_not_none("rec_type", is_part_of_is_part_of_type)
            is_part_of_is_part_of.set_key_if_not_none("title", title_translated)
            # creators with role pbd
            is_part_of_is_part_of.add_creators(creator_service.change_contibutors_role(translated_creators, "pbd"))
            #is_part_of_is_part_of.set_key_if_not_none("date_issued",date_year)
            is_part_of_is_part_of.set_key_if_not_none("publishers", publishers)
            is_part_of_is_part_of.set_key_if_not_none("publication_places", publication_places)
            if isbn_or_issn:
                is_part_of["identifiers"] = [metajson_service.create_identifier(isbn_or_issn_type, isbn_or_issn)]

            is_part_of.add_items_to_key([is_part_of_is_part_of], "is_part_ofs")

        else:
            # is_part_of in case of no is_part_of.is_part_of
            # creators with role edt
            is_part_of.add_creators(secondary_creators)
            #is_part_of.set_key_if_not_none("date_issued",date_year)
            is_part_of.set_key_if_not_none("publishers", publishers)
            is_part_of.set_key_if_not_none("publication_places", publication_places)
            if isbn_or_issn:
                is_part_of["identifiers"] = [metajson_service.create_identifier(isbn_or_issn_type, isbn_or_issn)]

        if "title" in is_part_of and is_part_of["title"]:
            document.add_items_to_key([is_part_of], "is_part_ofs")

    else:
        if isbn_or_issn:
            document["identifiers"] = [metajson_service.create_identifier(isbn_or_issn_type, isbn_or_issn)]
        if publishers:
            if endnote_type == TYPE_THESIS:
                document.add_creators([creator_service.formatted_name_to_creator(publishers[0], "orgunit", "dgg")])
            elif endnote_type == TYPE_FILM_OR_BROADCAST:
                document.add_creators([creator_service.formatted_name_to_creator(publishers[0], "orgunit", "dst")])
            else:
                document.set_key_if_not_none("publishers", publishers)
        document.set_key_if_not_none("publication_places", publication_places)

    # seriess[]
    if endnote_type in [TYPE_BOOK, TYPE_BOOK_SECTION]:
        series = Document()
        series["rec_type"] = constants.DOC_TYPE_SERIES
        if endnote_type == TYPE_BOOK and title_secondary:
            series.set_key_if_not_none("title", title_secondary)
            series.add_creators(secondary_creators)
            series.set_key_if_not_none("part_volume", part_number)
        if endnote_type == TYPE_BOOK_SECTION and title_tertiary:
            series.set_key_if_not_none("title", title_tertiary)
            series.add_creators(tertiary_creators)
            series.set_key_if_not_none("part_volume", part_number)
        if "title" in series and len(series) > 2:
            document.add_items_to_key([series], "seriess")

    # originals[]
    if (reprint_edition or title_translated or orig_pub) and endnote_type in [TYPE_BOOK, TYPE_BOOK_SECTION, TYPE_JOURNAL_ARTICLE, TYPE_FILM_OR_BROADCAST]:
        original_title = None
        original_is_part_of = None        
        if reprint_edition:
            original_title = reprint_edition
        if title_translated and is_part_of_is_part_of_type is None:
            original_title = title_translated
        if orig_pub:
            if is_part_of_type is not None:
                original_is_part_of = Document()
                original_is_part_of["rec_type"] = is_part_of_type
                original_is_part_of["title"] = orig_pub
            else:
                original_title = orig_pub
        if original_title:
            original = Document()
            original["rec_type"] = rec_type
            original.set_key_if_not_none("title", original_title)
            original.add_item_to_key(original_is_part_of, "is_part_ofs")
            document.add_item_to_key(original, "originals")

    # is_review_ofs[]
    if reviewed_item and endnote_type in [TYPE_BOOK_SECTION, TYPE_JOURNAL_ARTICLE]:
        is_review_ofs = Document()
        is_review_ofs.set_key_if_not_none("title", reviewed_item)
        is_review_ofs.set_key_if_not_none("rec_type", "Book")
        document.add_items_to_key([is_review_ofs], "is_review_ofs")

    # descriptions[0].value
    if abstract:
        document["descriptions"] = [{"value": abstract, "language": "und"}]

    # archive
    if endnote_type == TYPE_FIGURE and remote_database_provider:
        archive = Document()
        archive["title"] = remote_database_provider
        document.add_items_to_key([archive], "archive")

    # caption
    document.set_key_if_not_none("caption", caption)

    # creators[]
    document.add_creators(primary_creators)
    if endnote_type in [TYPE_BOOK, TYPE_THESIS, TYPE_FILM_OR_BROADCAST]:
        document.add_creators(tertiary_creators)
    if endnote_type in [TYPE_BOOK, TYPE_BOOK_SECTION, TYPE_FILM_OR_BROADCAST]:
        document.add_creators(subsidiary_creators)
    if custom4:
        document.add_creators(endnote_authors_to_creators(custom4, "person", "rev"))
    if endnote_type == TYPE_FIGURE and remote_database_name:
        document.add_creators(endnote_authors_to_creators(remote_database_name, None, "cph"))

    # edition
    if endnote_type in [TYPE_BOOK, TYPE_BOOK_SECTION, TYPE_FILM_OR_BROADCAST, TYPE_WEB_PAGE] and edition:
        document["edition"] = edition

    # extent_pages, extent_volumes
    if endnote_type in [TYPE_BOOK, TYPE_THESIS] and pages:
        document["extent_pages"] = pages.replace("p.", "").strip()
    if endnote_type in [TYPE_BOOK, TYPE_BOOK_SECTION] and extent_volumes:
        document["extent_volumes"] = extent_volumes

    # date_issued, date_issued_first
    if date_year:
        date_issued = ""
        date_issued_first = ""
        orig_index_begin = date_year.find("[")
        orig_index_end = date_year.find("]")
        if orig_index_begin != -1 and orig_index_end != -1:
            date_issued_first = date_year[orig_index_begin + 1: orig_index_end]
            date_issued = date_year.replace("[" + date_issued_first + "]", "").strip()
        else:
            date_issued = date_year.strip()

        if "is_part_ofs" in document:
            if document["is_part_ofs"][0]["rec_type"] == constants.DOC_TYPE_BOOK:
                document["is_part_ofs"][0].set_key_if_not_none("date_issued", date_issued)
                document["is_part_ofs"][0].set_key_if_not_none("date_issued_first", date_issued_first)
            elif "is_part_ofs" in document["is_part_ofs"][0] and document["is_part_ofs"][0]["is_part_ofs"][0]["rec_type"] == constants.DOC_TYPE_BOOK:
                document["is_part_ofs"][0]["is_part_ofs"][0].set_key_if_not_none("date_issued", date_issued)
                document["is_part_ofs"][0]["is_part_ofs"][0].set_key_if_not_none("date_issued_first", date_issued_first)
            else:
                document.set_key_if_not_none("date_issued_first", date_issued_first)
                if rec_type in unpublished_types:
                    document.set_key_if_not_none("date_created", date_issued)
                else:
                    document.set_key_if_not_none("date_issued", date_issued)
        else:
            document.set_key_if_not_none("date_issued_first", date_issued_first)
            if rec_type in unpublished_types:
                document.set_key_if_not_none("date_created", date_issued)
            else:
                document.set_key_if_not_none("date_issued", date_issued)

    # identifiers[]
    identifiers = []
    if accessionnumber:
        identifiers.append(metajson_service.create_identifier("accessionnumber", accessionnumber))
    if callnumber:
        identifiers.append(metajson_service.create_identifier("callnumber", callnumber))
    if doi:
        identifiers.append(metajson_service.create_identifier("doi", doi))
    if identifiers:
        document["identifiers"] = identifiers

    # language
    if language:
        rfc5646 = language_service.convert_unknown_format_to_rfc5646(language)
        if rfc5646:
            document["languages"] = [rfc5646]

    # note
    if endnote_import_note and note:
        document.set_key_with_value_type_in_list("notes", note, "general")
    if endnote_import_research_note and research_notes:
        document.set_key_with_value_type_in_list("notes", research_notes, "user")

    # part_page_begin & part_page_end
    if endnote_type in [TYPE_BOOK_SECTION, TYPE_FIGURE, TYPE_JOURNAL_ARTICLE] and pages:
        hyphen_index = pages.find("-")
        if hyphen_index == -1:
            document["part_page_begin"] = pages.replace("p.", "").strip()
        else:
            document["part_page_begin"] = pages[:hyphen_index].replace("p.", "").strip()
            document["part_page_end"] = pages[hyphen_index+1:].replace("p.", "").strip()

    if endnote_type in [TYPE_JOURNAL_ARTICLE]:
        document.set_key_if_not_none("part_issue", part_number)
    elif endnote_type in [TYPE_FIGURE]:
        document.set_key_if_not_none("part_number", part_number)
    document.set_key_if_not_none("part_section", part_section)
    document.set_key_if_not_none("part_volume", part_volume)

    # resources[0]
    if url is not None:
        resource = Resource()
        resource["rec_type"] = "ResourceRemote"
        resource.set_key_if_not_none("url", url)
        if endnote_type == TYPE_WEB_PAGE:
            resource.set_key_if_not_none("date_last_accessed", part_number)
        else:
            resource.set_key_if_not_none("date_last_accessed", access_date)
        document["resources"] = [resource]

    # subjects[]
    if endnote_import_keywords and keywords:
        for keyword in keywords.split():
            document.set_key_with_value_type_in_list("subjects", keyword, "topic")

    # title, title_alternative, title_abbreviated, title_translated
    document["title"] = title
    if title_alternative:
        document["title_alternatives"] = [{"title": title_alternative}]
    if title_abbreviated:
        document["title_abbreviateds"] = [{"title": title_abbreviated}]

    #logging.debug("# endnote_type: {}".format(endnote_type))
    metajson_service.pretty_print_document(document)
    return document


def extract_list(element, xpath):
    styles_xml_element = element.findall(xpath)
    if len(styles_xml_element) != 0:
        try:
            return [style.text for style in styles_xml_element if style is not None and style.text is not None]
        except:
            return "error extract_list %s" % (ET.tostring(element))


def extract_text(element, xpath):
    styles = extract_list(element, xpath)
    if styles is not None and len(styles) != 0:
        try:
            result = "".join(styles).strip()
            if result == "":
                return None
            else:
                return result
        except:
            return "error extract_text %s" % (ET.tostring(element))


def extract_text_and_set_key(common_dict, key, element, xpath):
    common_dict.set_key_if_not_none(key, extract_text(element, xpath))


def extract_text_and_set_key_with_type_in_list(common_dict, key, my_type, element, xpath):
    common_dict.set_key_with_value_type_in_list(key, extract_text(element, xpath), my_type)


def extract_creators(creator_type, role, element, xpath):
    authors_list = extract_list(element, xpath)
    if authors_list is not None and len(authors_list) != 0:
        creators = []
        for author_item in authors_list:
            creators.extend(endnote_authors_to_creators(author_item, creator_type, role))
        return creators


def extract_and_set_creators(common_dict, creator_type, role, element, xpath):
    common_dict.add_creators(extract_creators(creator_type, role, element, xpath))


def endnote_authors_to_creators(authors, creator_type="person", role="aut"):
    creators = []
    for author in authors.splitlines():
        creator = creator_service.formatted_name_to_creator(author, creator_type, role)
        if creator:
            creators.append(creator)
    return creators
