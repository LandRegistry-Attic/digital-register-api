#!/usr/bin/env python
from service import app
import os
from flask import Flask, abort, jsonify, make_response
import requests
import json
from sqlalchemy import Table, Column, String, create_engine
import pg8000
from service.models import TitleRegisterData
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from service.models import TitleRegisterData, TitleNumbersUprns


ELASTIC_SEARCH_ENDPOINT = app.config['ELASTIC_SEARCH_ENDPOINT']
ADDRESS_KEY_FIELDS = ['organisation_name', 'sub_building_name', 'building_name',
                      'building_number', 'dependent_thoroughfare_name',
                      'thoroughfare_name', 'double_dependent_locality',
                      'dependent_locality', 'post_town', 'postcode']


def get_title_register(title_ref):
    return TitleRegisterData.query.get(title_ref)


@app.route('/', methods=['GET'])
def healthcheck():
    return "OK"


def get_property_address(postcode):
    client = Elasticsearch([ELASTIC_SEARCH_ENDPOINT])
    search = Search(
        using=client, index='landregistry', doc_type='property_by_postcode')
    query = search.filter('term', postcode=postcode)
    return query.execute().hits


def format_address_into_single_string(address_record):
    address = [
        address_record.buildingNumber,
        address_record.thoroughfareName,
        address_record.postTown,
        address_record.postCode
    ]
    formatted_address = ", ".join(address)
    return formatted_address


def get_titles_for_uprns(uprns):
    title_number_uprns = TitleNumbersUprns.query.filter(
        TitleNumbersUprns.uprn.in_(uprns)).all()
    title_numbers = map(lambda x: x.title_number, title_number_uprns)
    return TitleRegisterData.query.filter(TitleRegisterData.title_number.in_(title_numbers)).all()


def format_address_records(address_records):
    result = []
    for address_record in address_records:
        if address_record.uprns:
            titles = get_titles_for_uprns(address_record.uprns)
            formatted_titles = []
            for title in titles:
                formatted_titles += [{
                    'title_number': title.title_number,
                    'data': title.register_data
                }]
            result += formatted_titles
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
        abort(404)


@app.route('/title_search_postcode/<postcode>', methods=['GET'])
def get_properties(postcode):
    postcode.replace("_", " ")
    address_records = get_property_address(postcode)
    if address_records:
        result = format_address_records(address_records)
        return jsonify(result)
    else:
        return jsonify({'titles': []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
