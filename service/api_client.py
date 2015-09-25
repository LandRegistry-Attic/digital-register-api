import requests  # type: ignore
from service import app

ADDRESS_SEARCH_API_URL = app.config['ADDRESS_SEARCH_API']

def get_titles_by_postcode(postcode, page_number, page_size):
    response = requests.get(
        '{}search'.format(ADDRESS_SEARCH_API_URL),
        params={'page_number': page_number,
                'postcode': postcode,
                'page_size': page_size
                }
    )

    return _to_json(response)

def _to_json(response):
    try:
        return response.json()
    except Exception as e:
        raise Exception('API response body is not JSON', e)



