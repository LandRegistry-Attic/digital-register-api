import requests  # type: ignore
import logging
from service import app

ADDRESS_SEARCH_API_URL = app.config['ADDRESS_SEARCH_API']
logger = logging.getLogger(__name__)


def get_titles_by_postcode(postcode, page_number, page_size):
    logger.debug('Start get_titles_by_postcode. Postcode: {}'.format(postcode))
    logger.info('Sending to address-search-api')
    response = requests.get(
        '{}search'.format(ADDRESS_SEARCH_API_URL),
        params={'page_number': page_number,
                'postcode': postcode,
                'page_size': page_size
                }
    )
    logger.info('Returned from address-search-api')
    if response:
        logger.debug('End get_titles_by_postcode. Response: {}'.format(response.content))
    return _to_json(response)


def _to_json(response):
    try:
        return response.json()
    except Exception as e:
        raise Exception('API response body is not JSON', e)
