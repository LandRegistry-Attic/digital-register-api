from flask import jsonify, Response, request  # type: ignore
import json
import logging
import logging.config                         # type: ignore
import math

from service import app, db_access, es_access, api_client

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
    normalised_postcode = postcode.replace('_', '').strip().upper()
    # call Address_search_api to obtain list of AddressBase addresses
    address_records = api_client.get_titles_by_postcode(normalised_postcode, page_number, _get_page_size())
    # Iterate over dict collecting the AddressBase uprns to obtain the mapped LR_Uprns from PG
    if address_records:
        for address in address_records.get('data').get('addresses'):
            address['title_number'] = 'not found'
            address['tenure'] = ''
            address_base_uprn = address.get('uprn')
            if address_base_uprn:
                # using AB uprn get Land Registry's version
                lr_uprn_mapping = db_access.get_mapped_lruprn(address_base_uprn)
                # Now using LR_uprn obtain some title details (currently title details and tenure)
                if lr_uprn_mapping:
                    title_details = db_access.get_title_number_and_register_data(lr_uprn_mapping.lr_uprn)
                    if title_details:
                        address['title_number'] = title_details.title_number
                        address['tenure'] = title_details.register_data.get('tenure')
                        address['register_data'] = title_details.register_data

    result = _paginated_address_records_v2(address_records, page_number)
    return jsonify(result)


@app.route('/title_search_address/<address>', methods=['GET'])
def get_titles_for_address(address):
    page_number = int(request.args.get('page', 0))

    # TODO: keep pagination aspect resolving in this module and pass page size to es_access
    address_records = es_access.get_properties_for_address(address, _get_page_size(), page_number)
    result = _paginated_address_records(address_records, page_number)
    return jsonify(result)


@app.route('/save_search_request', methods=['POST'])
def save_search_request():
    # N.B.: "request.form" is a 'multidict', so need to flatten it first; assume single value per key.
    form_dict = request.form.to_dict()
    cart_id = db_access.save_user_search_details(form_dict)

    return cart_id, 200


@app.route('/user_can_view/<username>/<title_number>', methods=['GET'])
def user_can_view(username, title_number):
    result = db_access.user_can_view(username, title_number)

    return result, 200 if result is True else result, 403


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


def _paginated_address_records_v2(address_records, page_number):
    # NOTE: our code uses the number of records reported by elasticsearch.
    # Records that have been deleted are not included in the search results list.
    nof_results = min(address_records['data'].get('total'), _get_max_number_search_results())
    nof_pages = math.ceil(nof_results / _get_page_size())  # 0 if no results
    if address_records:
        title_dicts = [{'title_number': address.get('title_number'), 'data': address.get('register_data'), 'address': address.get('joined_fields')} for address in address_records['data']['addresses']]
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
