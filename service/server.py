#!/usr/bin/env python
from service import app
from flask import jsonify, Response, request
import json
import logging
import logging.config
import math

from service import db_access, es_access

MAX_NUMBER_SEARCH_RESULTS = app.config['MAX_NUMBER_SEARCH_RESULTS']
SEARCH_RESULTS_PER_PAGE = app.config['SEARCH_RESULTS_PER_PAGE']

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


@app.route('/health', methods=['GET'])
def healthcheck():
    errors = _check_elasticsearch_connection() + _check_postgresql_connection()
    status = 'error' if errors else 'ok'
    http_status = 500 if errors else 200

    response_body = {'status': status}
    if errors:
        response_body['errors'] = errors

    return Response(
        json.dumps(response_body),
        status=http_status,
        mimetype=JSON_CONTENT_TYPE,
    )


def _hit_postgresql_with_sample_query():
    # Hitting PostgreSQL database to see if it responds properly
    db_access.get_title_register('non-existing-title')


def paginated_address_records(address_records, page_number):
    if address_records:
        title_numbers = [rec.title_number for rec in address_records]
        titles = db_access.get_title_registers(title_numbers)
        ordered = sorted(titles, key=lambda t: title_numbers.index(t.title_number))
        dicts = [{'title_number': t.title_number, 'data': t.register_data} for t in ordered if t]

        nof_results = min(address_records.total, MAX_NUMBER_SEARCH_RESULTS)
        nof_pages = math.ceil(nof_results / SEARCH_RESULTS_PER_PAGE)
        page_number = min(page_number, nof_pages)
    else:
        dicts, nof_pages, page_num, nof_results = [], 0, 0, 0
    return {'titles': dicts, 'number_pages': nof_pages, 'page_number': page_number,
            'number_results': nof_results}


@app.route('/titles/<title_ref>', methods=['GET'])
def get_title(title_ref):
    data = db_access.get_title_register(title_ref)
    if data:
        result = {
            'data': data.register_data,
            'title_number': data.title_number,
            'geometry_data': data.geometry_data,
        }
        return jsonify(result)
    else:
        return TITLE_NOT_FOUND_RESPONSE


@app.route('/titles/<title_ref>/official-copy', methods=['GET'])
def get_official_copy(title_ref):
    data = db_access.get_official_copy_data(title_ref)
    if data:
        result = {
            'official_copy_data': {
                'sub_registers': data.official_copy_data['sub_registers'],
                'title_number': data.title_number,
            }
        }
        return jsonify(result)
    else:
        return TITLE_NOT_FOUND_RESPONSE


@app.route('/title_search_postcode/<postcode>', methods=['GET'])
def get_properties(postcode):
    page_number = int(request.args.get('page', 1))
    normalised_postcode = postcode.replace('_', '').replace(' ', '')
    address_records = es_access.get_properties_for_postcode(normalised_postcode, page_number)
    result = paginated_address_records(address_records, page_number)
    return jsonify(result)


@app.route('/title_search_address/<address>', methods=['GET'])
def get_titles_for_address(address):
    page_number = int(request.args.get('page', 1))
    address_records = es_access.get_properties_for_address(address, page_number)
    result = paginated_address_records(address_records, page_number)
    return jsonify(result)


def _check_postgresql_connection():
    """Checks PostgreSQL connection and returns a list of errors"""
    try:
        _hit_postgresql_with_sample_query()
        return []
    except Exception as e:
        error_message = 'Problem talking to PostgreSQL: {0}'.format(str(e))
        return [error_message]


def _check_elasticsearch_connection():
    """Checks elasticsearch connection and returns a list of errors"""
    try:
        status = es_access.get_info()['status']
        if status == 200:
            return []
        else:
            return ['Unexpected elasticsearch status: {}'.format(status)]
    except Exception as e:
        return ['Problem talking to elasticsearch: {0}'.format(str(e))]
