from flask import jsonify, Response, request  # type: ignore
import json
import logging
import logging.config                         # type: ignore
import math

from service import app, db_access, es_access

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


# TODO: remove the root route when the monitoring tools can work without it
@app.route('/', methods=['GET'])
@app.route('/health', methods=['GET'])
def health_check():
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
def get_properties_for_postcode(postcode):
    page_number = int(request.args.get('page', 0))
    normalised_postcode = postcode.replace('_', '').replace(' ', '').upper()
    address_records = es_access.get_properties_for_postcode(normalised_postcode, _get_page_size(), page_number)
    result = _paginated_address_records(address_records, page_number)
    return jsonify(result)


@app.route('/title_search_address/<address>', methods=['GET'])
def get_titles_for_address(address):
    page_number = int(request.args.get('page', 0))

    # TODO: keep pagination aspect resolving in this module and pass page size to es_access
    address_records = es_access.get_properties_for_address(address, _get_page_size(), page_number)
    result = _paginated_address_records(address_records, page_number)
    return jsonify(result)


def _hit_postgresql_with_sample_query():
    # Hitting PostgreSQL database to see if it responds properly
    db_access.get_title_register('non-existing-title')


def _paginated_address_records(address_records, page_number):
    # NOTE: our code uses the number of records reported by elasticsearch.
    # Records that have been deleted are not included in the search results list.
    nof_results = min(address_records.total, _get_max_number_search_results())
    nof_pages = math.ceil(nof_results / _get_page_size())  # 0 if no results

    if address_records:
        title_numbers = [rec.title_number for rec in address_records]
        titles = db_access.get_title_registers(title_numbers)
        ordered = sorted(titles, key=lambda t: title_numbers.index(t.title_number))
        title_dicts = [{'title_number': t.title_number, 'data': t.register_data} for t in ordered]
    else:
        title_dicts = []

    return {'titles': title_dicts, 'number_pages': nof_pages, 'page_number': page_number,
            'number_results': nof_results}


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


def _get_page_size():
    return app.config['SEARCH_RESULTS_PER_PAGE']


def _get_max_number_search_results():
    return app.config['MAX_NUMBER_SEARCH_RESULTS']
