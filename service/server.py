#!/usr/bin/env python
from service import app
import os
from flask import Flask, abort, jsonify, make_response, Response, request
import requests
import json
import logging
import logging.config
from sqlalchemy import Table, Column, String, create_engine
from sqlalchemy.sql.expression import false
import pg8000
from service.models import TitleRegisterData
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from service.models import TitleRegisterData

MAX_NUMBER_SEARCH_RESULTS = app.config['MAX_NUMBER_SEARCH_RESULTS']
SEARCH_RESULTS_PER_PAGE = app.config['SEARCH_RESULTS_PER_PAGE']

ELASTIC_SEARCH_ENDPOINT = app.config['ELASTIC_SEARCH_ENDPOINT']
INTERNAL_SERVER_ERROR_RESPONSE_BODY = json.dumps(
    {'error': 'Internal server error'}
)
JSON_CONTENT_TYPE = 'application/json'
LOGGER = logging.getLogger(__name__)

TITLE_NOT_FOUND_RESPONSE = Response(
    json.dumps({'error': 'Title not found'}),
    status=404,
    mimetype=JSON_CONTENT_TYPE
)


def get_title_register(title_ref):
    # Will retrieve the first matching title that is not marked as deleted
    result = TitleRegisterData.query.filter(TitleRegisterData.title_number == title_ref,
                                            TitleRegisterData.is_deleted == false()).first()
    return result


@app.errorhandler(Exception)
def handleServerError(error):
    LOGGER.error(
        'An error occurred when processing a request',
        exc_info=error
    )
    return Response(
        INTERNAL_SERVER_ERROR_RESPONSE_BODY,
        status=500,
        mimetype=JSON_CONTENT_TYPE
    )


@app.route('/', methods=['GET'])
def healthcheck():
    return "OK"


def get_property_address(postcode):
    search = create_search('property_by_postcode_2')
    query = search.filter('term', postcode=postcode)
    return query.execute().hits


def get_properties_for_address(address):
    search = create_search('property_by_address')
    query = search.query('match', address_string=address)
    return query.execute().hits


def paginated_address_records(address_records, page_number):
    start_index = (page_number-1)*int(SEARCH_RESULTS_PER_PAGE)
    end_index = max(page_number*int(SEARCH_RESULTS_PER_PAGE), len(address_records)-1)
    return format_address_records(address_records[start_index:end_index])


def paginated_and_index_address_records(address_records, page_number):
    if address_records:
        result = paginated_address_records(address_records, page_number)
        number_pages = int(len(address_records) / int(SEARCH_RESULTS_PER_PAGE))+1
        result["number_pages"] = number_pages
        result["page_number"] = page_number
        result["number_results"] = len(address_records)
    else:
        result = {'titles': []}
        result["number_pages"] = 0
        result["page_number"] = 0
        result["number_results"] = 0
    return result


def format_address_records(address_records):
    result = []
    for address_record in address_records:
        if address_record.title_number:
            title_number = address_record.title_number
            title = get_title_register(title_number)
            if title:
                result += [{
                    'title_number': title.title_number,
                    'data': title.register_data
                }]
    return {'titles': result}


def create_search(doc_type):
    client = Elasticsearch([ELASTIC_SEARCH_ENDPOINT])
    search = Search(
        using=client, index='landregistry', doc_type=doc_type)
    max_number = int(MAX_NUMBER_SEARCH_RESULTS)
    search = search[0:max_number]
    return search


@app.route('/titles/<title_ref>', methods=['GET'])
def get_title(title_ref):
    data = get_title_register(title_ref)
    if data:
        result = {
            "data": data.register_data,
            "title_number": data.title_number,
            "geometry_data": data.geometry_data,
        }
        return jsonify(result)
    else:
        # Title not found
        return TITLE_NOT_FOUND_RESPONSE


@app.route('/title_search_postcode/<postcode>', methods=['GET'])
def get_properties(postcode):
    page_number = request.args.get('page', 1)
    no_underscores = postcode.replace("_", "")
    no_spaces = no_underscores.replace(" ", "")
    address_records = get_property_address(no_spaces)
    result = paginated_and_index_address_records(address_records, page_number)
    return jsonify(result)


@app.route('/title_search_address/<address>', methods=['GET'])
def get_titles_for_address(address):
    page_number = request.args.get('page', 1)
    address_records = get_properties_for_address(address)
    result = paginated_and_index_address_records(address_records, page_number)
    return jsonify(result)
