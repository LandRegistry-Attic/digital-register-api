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
from elasticsearch_dsl import Search
from service.models import TitleRegisterData


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
        using=client, index='landregistry', doc_type='property_by_postcode')
    query = search.filter('term', postcode=postcode)
    return query.execute().hits


def format_address_records(address_records):
    result = []
    for address_record in address_records:
        if address_record.title_number:
            title = get_title_register(address_record.title_number)
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
    postcode.replace("_", " ")
    address_records = get_property_address(postcode)
    if address_records:
        result = format_address_records(address_records)
        return jsonify(result)
    else:
        return jsonify({'titles': []})
