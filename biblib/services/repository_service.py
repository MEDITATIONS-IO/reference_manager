#!/usr/bin/python
# -*- coding: utf-8 -*-
# coding=utf-8

# mongod --dbpath /Users/jrault/Documents/SciencesPo/Projets/biblib/mongodb

import uuid
import pymongo
from bson.objectid import ObjectId
from biblib.metajson import SearchResponse
from biblib.services import config_service
from biblib.services import metajson_service

DOCUMENTS = "documents"
AGENTS = "agents"
TYPES = "types"
DATAFIELDS = "datafields"
UIFIELDS = "uifields"

ERROR_0 = {
    "code": 0,
    "error_type": "error",
    "labels": {
        "en": "Empty request",
        "fr": "Requête vide"
    }
}

ERROR_40 = {
    "code": 40,
    "error_type": "error",
    "labels": {
        "en": "Stupid request",
        "fr": "Requête stupide"
    }
}

ERROR_100 = {
    "code": 100,
    "error_type": "error",
    "labels": {
        "en": "Invalid request",
        "fr": "Requête invalide"
    }
}


config = config_service.config["mongodb"]
default_corpus = config["default_corpus"]

mongodb = pymongo.MongoClient(config['host'], config['port'])

# examples:
# resdb = mongodb[config['mongo-scrapy']['jobListCol']].update({'_id': {'$in': update_ids}}, {'$set': {'crawling_status': crawling_statuses.RUNNING}}, multi=True, safe=True)
# update_ids = [job['_id'] for job in mongodb[config['mongo-scrapy']['jobListCol']].find({'_id': {'$in': finished_ids}, 'crawling_status': {'$nin': [crawling_statuses.CANCELED, crawling_statuses.FINISHED]}}, fields=['_id'])]
# resdb = mongodb[config['mongo-scrapy']['jobListCol']].update({'_id': res['jobid']}, {'$set': {'webentity_id': webentity_id, 'nb_pages': 0, 'nb_links': 0, 'crawl_arguments': args, 'crawling_status': crawling_statuses.PENDING, 'indexing_status': indexing_statuses.PENDING, 'timestamp': ts}}, upsert=True, safe=True)
# return db[config['mongo-scrapy']['jobLogsCol']].insert([{'_job': _id, 'timestamp': timestamp, 'log': msg} for _id in jobid])


def create_corpus(corpus):
    mongodb[corpus]


def empty_corpus(corpus):
    mongodb[corpus][DOCUMENTS].drop()
    mongodb[corpus][AGENTS].drop()
    mongodb[corpus][TYPES].drop()
    mongodb[corpus][DATAFIELDS].drop()
    mongodb[corpus][UIFIELDS].drop()


def init_corpus_indexes(corpus):
    index_id = ('_id', pymongo.ASCENDING)
    index_rec_id = ('rec_id', pymongo.ASCENDING)
    index_title = ('title', pymongo.ASCENDING)
    index_name = ('name', pymongo.ASCENDING)
    index_name_family = ('name_family', pymongo.ASCENDING)
    index_name_family = ('name_given', pymongo.ASCENDING)

    mongodb[corpus][DOCUMENTS].ensure_index([index_id, index_rec_id, index_title], safe=True)
    mongodb[corpus][AGENTS].ensure_index([index_id, index_rec_id, index_name, index_name_family], safe=True)
    mongodb[corpus][TYPES].ensure_index([index_id], safe=True)
    mongodb[corpus][DATAFIELDS].ensure_index([index_id], safe=True)
    mongodb[corpus][UIFIELDS].ensure_index([index_id], safe=True)


def get_document_by_mongo_id(corpus, mongo_id):
    if not corpus:
        corpus = default_corpus
    return metajson_service.load_dict(mongodb[corpus][DOCUMENTS].find_one({'_id': ObjectId(mongo_id)}))


def get_documents_by_mongo_ids(corpus, mongo_ids):
    if not corpus:
        corpus = default_corpus
    mongo_object_ids = []
    for mongo_id in mongo_ids:
        mongo_object_ids.append(ObjectId(mongo_id))
    return metajson_service.load_dict_list(mongodb[corpus][DOCUMENTS].find({"_id": {"$in": mongo_object_ids}}))


def get_document_by_rec_id(corpus, rec_id):
    if not corpus:
        corpus = default_corpus
    return metajson_service.load_dict(mongodb[corpus][DOCUMENTS].find_one({"rec_id": rec_id}))


def get_documents_by_rec_ids(corpus, rec_ids):
    if not corpus:
        corpus = default_corpus
    return metajson_service.load_dict_list(mongodb[corpus][DOCUMENTS].find({"rec_id": {"$in": rec_ids}}))


def get_documents(corpus):
    if not corpus:
        corpus = default_corpus
    return metajson_service.load_dict_list(mongodb[corpus][DOCUMENTS].find())


def get_documents_count(corpus):
    if not corpus:
        corpus = default_corpus
    return mongodb[corpus][DOCUMENTS].count()


def search(corpus, search_query):
    if not corpus:
        corpus = default_corpus
    search_response = SearchResponse()

    # empty search_query
    if search_query is None:
        search_response["errors"] = [ERROR_0]
        return search_response

    # filter_class -> collection
    collection = None
    if "filter_class" not in search_query or search_query["filter_class"] not in ["Document", "Agent", "Person", "OrgUnit", "Event", "Family"]:
        search_response["errors"] = [ERROR_100]
        return search_response
    elif search_query["filter_class"] == "Document":
        collection = DOCUMENTS
    elif search_query["filter_class"] in ["Agent", "Person", "OrgUnit", "Event", "Family"]:
        collection = AGENTS

    # other filters
    filter_query = []
    if "filter_date_end" in search_query:
        filter_query.append({"date_issued": {"$lte": search_query["filter_date_end"]}})
    if "filter_date_start" in search_query:
        filter_query.append({"date_issued": {"$gte": search_query["filter_date_start"]}})
    if "filter_languages" in search_query:
        filter_query.append({"languages": {"$in": search_query["filter_languages"]}})
    if "filter_types" in search_query:
        filter_query.append({"rec_type": {"$in": search_query["filter_types"]}})

    # search_terms
    search_indexes = []
    if "search_terms" in search_query:
        for search_term in search_query["search_terms"]:
            # index
            if "index" not in search_term:
                search_response["errors"] = [ERROR_100]
            elif search_term["index"] == "all":
                pass
            elif search_term["index"] == "identifier":
                pass
            elif search_term["index"] == "title":
                search_indexes.append({"title": {"$in": search_query["filter_types"]}})
                pass
            elif search_term["index"] == "is_part_of":
                pass
            elif search_term["index"] == "creator":
                pass
            elif search_term["index"] == "creator_id":
                pass
            elif search_term["index"] == "affiliation":
                pass
            elif search_term["index"] == "affiliation_id":
                pass
            elif search_term["index"] == "publisher":
                pass
            elif search_term["index"] == "keyword":
                pass
            elif search_term["index"] == "classification":
                pass
            elif search_term["index"] == "research_area":
                pass
            elif search_term["index"] == "subject":
                pass
            elif search_term["index"] == "set":
                pass
            # operator
            if "operator" in search_term:
                if search_term["operator"] == "or":
                    pass
                elif search_term["operator"] == "and":
                    pass
                elif search_term["operator"] == "not":
                    pass

    # result_sorts

    mongo_query = {"rec_metajson": 1}

    records = metajson_service.load_dict_list(mongodb[corpus][collection].find(mongo_query))
    records_total_count = len(records)

    search_response["records"] = records
    search_response["records_total_count"] = records_total_count
    search_response["result_batch_size"] = records_total_count
    search_response["result_offset"] = 0
    search_response["search_query"] = search_query
    return search_response


def search_mongo(corpus, mongo_query):
    if not corpus:
        corpus = default_corpus
    # {"_id": {"$in": mongo_object_ids}}
    # {"rec_id": {"$in": rec_ids}}
    # {"rec_type": "Book"}
    # {"is_part_ofs.rec_type":"Book"}
    # {"is_part_ofs.rec_type":"Journal"}
    # {"is_part_ofs.rec_type":"VideoRecording"}
    # {"is_part_ofs.is_part_ofs.rec_type":"Book"}
    # {"creators.agent.name_family":"Latour"}
    # {"is_part_ofs.creators.agent.name_family":"Latour"}
    # {"is_part_ofs.creators.agent.name_family":"Latour", "is_part_of.creators.agent.name_given":"Bruno"}
    return metajson_service.load_dict_list(mongodb[corpus][DOCUMENTS].find(mongo_query))


def save_document(corpus, document):
    if not corpus:
        corpus = default_corpus
    if "rec_id" not in document:
        document["rec_id"] = str(uuid.uuid1())
    return mongodb[corpus][DOCUMENTS].insert(document)


def delete_document(corpus, rec_id):
    if not corpus:
        corpus = default_corpus
    result = mongodb[corpus][DOCUMENTS].remove({"rec_id": rec_id})
    # todo clarify the response
    # result example :
    #{
    #   "connectionId": 20,
    #   "err": null,
    #   "n": 1,
    #   "ok": 1.0
    #}
    return result


def get_datafield(corpus, prop):
    if not corpus:
        corpus = default_corpus
    return metajson_service.load_dict(mongodb[corpus][DATAFIELDS].find_one({"property": prop}))


def save_datafield(corpus, datafield):
    if not corpus:
        corpus = default_corpus
    return mongodb[corpus][DATAFIELDS].insert(datafield)


def get_uifield(corpus, rec_type):
    if not corpus:
        corpus = default_corpus
    return metajson_service.load_dict(mongodb[corpus][UIFIELDS].find_one({"rec_type": rec_type}))


def save_uifield(corpus, uifield):
    if not corpus:
        corpus = default_corpus
    return mongodb[corpus][UIFIELDS].insert(uifield)


def get_type(corpus, type_id):
    if not corpus:
        corpus = default_corpus
    return metajson_service.load_dict(mongodb[corpus][TYPES].find_one({"type_id": type_id}))


def save_type(corpus, metatype):
    if not corpus:
        corpus = default_corpus
    return mongodb[corpus][TYPES].insert(metatype)
