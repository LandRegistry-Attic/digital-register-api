#!/usr/bin/env python
from service import app
import os
from flask import Flask, abort, jsonify
import requests
import json
from sqlalchemy import Table, Column, String, create_engine
import pg8000
<<<<<<< HEAD
from service.models import TitleRegisterData

=======
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from service.models import TitleRegisterData

ELASTIC_SEARCH_ENDPOINT = app.config['ELASTIC_SEARCH_ENDPOINT']
>>>>>>> adding initial elasticsearch info and endpoint

def get_title_register(title_ref):
    return TitleRegisterData.query.get(title_ref)


@app.route('/', methods=['GET'])
def healthcheck():
    return "OK"

<<<<<<< HEAD
=======
#TODO: This is going to be used to get the property with the postcode, needs
#double checking.
def get_property_address(postcode):
    client = Elasticsearch([ELASTIC_SEARCH_ENDPOINT])
    search = Search(using=client, index='landregistry')
    query = search.filter('term', postcode=postcode)

    return query.execute().hits
>>>>>>> adding initial elasticsearch info and endpoint

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

@app.route('/titles/<postcode>', methods=['GET'])
def get_properties(postcode):
    address_records = get_property_address(postcode)
    nof_results = len(address_records)
    if nof_results != 1:
        abort(404)

    result = create_json(address_records)

    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
