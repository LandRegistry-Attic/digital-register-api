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
import math

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
    if title_ref:
        # Will retrieve the first matching title that is not marked as deleted
        result = TitleRegisterData.query.filter(TitleRegisterData.title_number == title_ref,
                                                TitleRegisterData.is_deleted == false()).first()
        return result
    else:
        raise TypeError('Title number must not be None.')


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
    search = create_search('property_by_postcode_3')
    query = search.filter('term', postcode=postcode).sort(
        {'street_name': {'missing': '_last'}},
        {'house_no': {'missing': '_last'}},
        {'house_alpha': {'missing': '_last'}},
        {'street_name_2': {'missing': '_last'}},
        {'secondary_house_no': {'missing': '_last'}},
        {'secondary_house_alpha': {'missing': '_last'}},
        {'sub_building_no': {'missing': '_last'}},
        {'sub_building_description': {'missing': '_last'}},
        {'first_number_in_address_string': {'missing': '_last'}},
        {'address_string': {'missing': '_last'}}
    )
    return query.execute().hits


def get_properties_for_address(address):
    search = create_search('property_by_address')
    query = search.query('match', address_string=address)
    return query.execute().hits


def paginated_address_records(address_records, page_number):
    titles = [get_title_register(rec.title_number) for rec in address_records]
    title_dicts = [{'title_number': t.title_number, 'data': t.register_data} for t in titles if t]

    nof_results = len(title_dicts)
    number_pages = math.ceil(nof_results / SEARCH_RESULTS_PER_PAGE)
    page_number = min(page_number, number_pages)

    start_index = (page_number - 1) * SEARCH_RESULTS_PER_PAGE
    end_index = page_number * SEARCH_RESULTS_PER_PAGE

    title_dicts_on_page = title_dicts[start_index:end_index]

    return {
        'titles': title_dicts_on_page,
        'number_pages': number_pages,
        'page_number': page_number,
        'number_results': nof_results,
    }


def paginated_and_index_address_records(address_records, page_number):
    if address_records:
        result = paginated_address_records(address_records, page_number)
    else:
        result = {'titles': [], 'number_pages': 0, 'page_number': 0, 'number_results': 0}
    return result


def create_search(doc_type):
    client = Elasticsearch([ELASTIC_SEARCH_ENDPOINT])
    search = Search(using=client, index='landregistry', doc_type=doc_type)
    search = search[0:MAX_NUMBER_SEARCH_RESULTS]
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
    page_number = int(request.args.get('page', 1))
    no_underscores = postcode.replace("_", "")
    no_spaces = no_underscores.replace(" ", "")
    address_records = get_property_address(no_spaces)
    result = paginated_and_index_address_records(address_records, page_number)
    return jsonify(result)


@app.route('/title_search_address/<address>', methods=['GET'])
def get_titles_for_address(address):
    page_number = int(request.args.get('page', 1))
    address_records = get_properties_for_address(address)
    result = paginated_and_index_address_records(address_records, page_number)
    return jsonify(result)
