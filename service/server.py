#!/usr/bin/env python
from service import app
import os
from flask import Flask, abort, jsonify, make_response, Response
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
    client = Elasticsearch([ELASTIC_SEARCH_ENDPOINT])
    search = Search(
        using=client, index='landregistry', doc_type='property_by_postcode_2')
    max_number = int(MAX_NUMBER_SEARCH_RESULTS)
    search = search[0:max_number]
    query = search.filter('term', postcode=postcode)
    return query.execute().hits


def get_properties_for_address(address):
    client = Elasticsearch([ELASTIC_SEARCH_ENDPOINT])
    search = Search(
        using=client, index='landregistry', doc_type='property_by_address')
    max_number = int(MAX_NUMBER_SEARCH_RESULTS)
    search = search[0:max_number]
    address_parts = address.split()
    # In the future we might start weighting some words higher than others
    # eg "Street" be low, if it is a structured address the house number should be high etc
    word_queries = [~Q('match', address_string=address_part) for address_part in address_parts]
    bool_address_query = Q('bool', should=word_queries)
    query = search.query(bool_address_query)
    return query.execute().hits


def format_address_records(address_records):
    result = []
    # Only one address record per title number
    result_title_nums = []
    for address_record in address_records:
        if address_record.title_number:
            title_number = address_record.title_number
            if title_number not in result_title_nums:
                result_title_nums.append(title_number)
                title = get_title_register(title_number)
                if title:
                    result += [{
                        'title_number': title.title_number,
                        'data': title.register_data
                    }]
    return {'titles': result}


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
    postcode = postcode.replace("_", "")
    address_records = get_property_address(postcode)
    if address_records:
        result = format_address_records(address_records)
        return jsonify(result)
    else:
        return jsonify({'titles': []})


@app.route('/title_search_address/<address>', methods=['GET'])
def get_titles_for_address(address):
    address_records = get_properties_for_address(address)
    if address_records:
        result = format_address_records(address_records)
        return jsonify(result)
    else:
        return jsonify({'titles': []})
