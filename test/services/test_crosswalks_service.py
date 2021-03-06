#!/usr/bin/python
# -*- coding: utf-8 -*-
# coding=utf-8

import logging
import os

from biblib.services import crosswalks_service
from biblib.services import io_service
from biblib.util import constants
from biblib.util import console


def test_crosswalk(input_format, output_format=constants.FORMAT_METAJSON, all_in_one_file=True):
    logging.info("*** Test crosswalk : {0}".format(input_format))
    base_dir = os.path.join(os.getcwd(), "data")
    input_dir = os.path.join(base_dir, input_format)
    output_file_extension = io_service.guess_file_extension_from_format(output_format)

    input_file_list = io_service.get_relevant_file_list_by_format(input_dir, input_format)
    if input_file_list:
        results = crosswalks_service.parse_and_convert_file_list(input_file_list, input_format, output_format, "test", "", False, all_in_one_file)
        col_id = "".join(["test_", input_format, "_to_", output_format])
        col_title = "".join(["Test ", input_format, " to ", output_format])
        if all_in_one_file:
            output_file_path = os.path.join(base_dir, "result", "result_" + input_format + "_" + output_format + "." + output_file_extension)
            io_service.write_items_in_one_file(col_id, col_title, results, output_file_path, output_format)
        else:
            #for idx, result in enumerate(results):
            output_dir_path = os.path.join(base_dir, "result", "result_" + input_format + "_" + output_format)
            io_service.write_items(col_id, col_title, results, output_dir_path, output_format)


def test():
    # input_format to MetaJSON
    test_crosswalk(constants.FORMAT_BIBTEX)
    #test_crosswalk(constants.FORMAT_CSV_SITPOL)
    test_crosswalk(constants.FORMAT_DIDL)
    test_crosswalk(constants.FORMAT_DDI)
    test_crosswalk(constants.FORMAT_ENDNOTEXML)
    test_crosswalk(constants.FORMAT_METS)
    test_crosswalk(constants.FORMAT_MODS)
    test_crosswalk(constants.FORMAT_OPENURL)
    test_crosswalk(constants.FORMAT_RESEARCHERML)
    test_crosswalk(constants.FORMAT_RIS)
    test_crosswalk(constants.FORMAT_SUMMONJSON)
    test_crosswalk(constants.FORMAT_TEI)
    test_crosswalk(constants.FORMAT_UNIMARC)
    test_crosswalk(constants.FORMAT_UNIMARC, constants.FORMAT_MODS, True)
    test_crosswalk(constants.FORMAT_UNIMARC, constants.FORMAT_OAI_DC, False)
    test_crosswalk(constants.FORMAT_UNIXREF)

    # MetaJSON to output_format
    test_crosswalk(constants.FORMAT_METAJSON, constants.FORMAT_MODS)


console.setup_console()
test()
