#!/usr/bin/python
# -*- coding: utf-8 -*-
# coding=utf-8

import logging
import logging.config
import os

from gspreadsheet import GSpreadsheet

from biblib.metajson import Type
from biblib.util import jsonbson


def find_config_path():
    # why not os.path.abspath(sys.modules['__main__'].__file__)
    locations = [
        os.path.abspath(os.getcwd()),
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."),
        os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."),
        os.path.abspath(os.path.join(os.getcwd(), 'biblib')),
        os.path.abspath(os.path.join(os.getcwd(), os.pardir)),
        os.path.abspath(os.path.join(os.getcwd(), os.pardir, os.pardir)),
        os.path.expanduser("~"),
        "/etc/biblib",
        os.environ.get("BIBLIB_CONF")
    ]
    for location in locations:
        logging.debug("location: {}".format(location))
        config_location = os.path.join(location, "conf", "config.json")
        if os.path.exists(config_location):
            return os.path.join(location, "conf")


def load_config_json():
    logging.info("config_service.load_config_json")
    try:
        config_location = os.path.join(config_path, "config.json")
        with open(config_location, 'r') as config_file:
            logging.info("config_location: {}".format(config_location))
            return jsonbson.load_json_file(config_file)
    except IOError as e:
        logging.error("ERROR: Can' open config.json file {}".format(e))
    except ValueError as e:
        logging.error("ERROR: Config file is not valid JSON {}".format(e))
        return False


def retrieve_google_types(app):
    spreadsheet = GSpreadsheet(key=config["google"]["conf_key"], email=config["google"]["email"], password=config["google"]["password"])
    keys = {}
    type_worksheets = get_google_types_worksheets(spreadsheet)
    for ws_id, ws_name in type_worksheets:
        logging.debug('worksheet code: {}, name: {}'.format(ws_id, ws_name))
        worksheet = GSpreadsheet(worksheet=ws_id, key=config["google"]["conf_key"], email=config["google"]["email"], password=config["google"]["password"])
        type_bundle = google_worksheet_to_type(ws_name, worksheet, app, keys)
        type_bundle_id = type_bundle["type_id"]
        type_bundle_dump = jsonbson.dumps_json(type_bundle)
        type_bundle_path = os.path.abspath(os.path.join(os.getcwd(), 'biblib', 'conf', 'types', type_bundle_id + ".json"))
        logging.debug(type_bundle_dump)
        with open(type_bundle_path, "w") as type_bundle_file:
            type_bundle_file.write(type_bundle_dump)
    logging.debug(jsonbson.jsonbson(keys))


def get_google_types_worksheets(spreadsheet):
    worksheets = spreadsheet.list_worksheets()
    for worksheet in worksheets:
        if worksheet[1].startswith("type.") and not worksheet[1].startswith("type.document_type"):
        #if worksheet[1].startswith("type.") and not worksheet[1].startswith("type.language"):
        #if worksheet[1].startswith("type.language"):
            yield worksheet


def google_worksheet_to_type(ws_name, worksheet, app, keys):
    logging.debug(type(worksheet))
    logging.debug(dir(worksheet))

    type_id_col = ""
    ws_name_key = ws_name.replace("_", "").replace(" ", "").strip().split('-', 1)[0]
    logging.debug("ws_name_key: {}".format(ws_name_key))
    type_bundle = Type()
    type_bundle["type_id"] = ws_name.replace("type.", "")
    type_bundle["bundle"] = True
    type_bundle["children"] = []

    for col in worksheet.fieldnames:
        # keys usage dict
        if col in keys:
            keys[col] = keys[col] + 1
        else:
            keys[col] = 1

        # find the type_id column
        type_id_sign = ""
        if col.startswith(ws_name_key):
            type_id_col = col
            type_id_sign = "*"

        logging.debug("col{}: {}".format(type_id_sign, col))

    if not type_id_col:
        logging.error("Fixme! Can't find the type_id_col for worksheet: {}".format(ws_name))
        return None
    else:
        logging.debug("type_id_col: {}".format(type_id_col))
        for row in worksheet:
            logging.debug(row)
            type_row = {}

            # type.code -> type_id
            # select.xxx -> deprecated
            # -> bundle
            # -> deprecated
            # -> default
            # -> preferred
            labels = {}
            type_id = None

            # type.code -> type_id
            if type_id_col in row and row[type_id_col]:
                type_id = row[type_id_col]
            if type_id:
                type_row["type_id"] = type_id
            else:
                continue

            # default -> default
            if "default" in row and row["default"] == "1":
                type_row["default"] = True

            # major -> major
            if "major" in row and row["major"] == "1":
                type_row["major"] = True

            # label.en -> labels['en']
            if "label.en" in row and row["label.en"]:
                labels['en'] = row["label.en"]
            # label.fr -> labels['fr']
            if "label.fr" in row and row["label.fr"]:
                labels['fr'] = row["label.fr"]

            if labels:
                type_row["labels"] = labels

            type_bundle["children"].append(type_row)
        return type_bundle


config_path = find_config_path()
config = load_config_json()
logging.config.dictConfig(config["logging"])
logging.info("Default corpus: {}".format(config["default_corpus"]))
#retrieve_google_types("spire")
