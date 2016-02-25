# To run (from top-level package directory):
#   'digital-register-api' (this package) needs to be running as a separate service, via 'lr-start-all' or the like.
#   'source environment.sh; python tests/integration_tests.py'

import requests

test_data = {"MC_timestamp": "2016-01-26 13:00:30.005449",
             "MC_userId": "Test User",
             "MC_titleNumber": "GR12345",
             "MC_searchType": "D",
             "MC_purchaseType": "drvSummaryView",
             "amount": 2,
             "cart_id": "374f501f4567",
             "last_changed_datestring": "12 Jul 2014",
             "last_changed_timestring": "11:04:32",
            }



REGISTER_TITLE_API_URL = 'http://172.16.42.43:8004'

response = requests.post('{}/save_search_request'.format(REGISTER_TITLE_API_URL), data=test_data)

print(response)
