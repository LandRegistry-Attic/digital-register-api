import json
from decimal import Decimal
from datetime import datetime, date, time
from service import legacy_transmission_queue

FakeReturnSearchRowFound = [datetime(2016, 1, 26, 13, 0, 30, 5449),
                            '1234',
                            'Test User',
                            datetime(2015, 12, 1, 14, 34, 14, 362556),
                            "D",
                            "drvSummaryView",
                            Decimal('2'),
                            "374f501f4567",
                            "GR12345",
                            "Search"]

FakeReturnNoSearchRowFound = None

FakeSearchTransmissionJSON = {"SEARCH_DATETIME": "2016-01-26 13:00:30.005449",
                              "LRO_TRANS_REF": "1234",
                              "USER_ID": "Test User",
                              "VIEWED_DATETIME": "2015-12-01 14:34:14.362556",
                              "SEARCH_TYPE": "D",
                              "PURCHASE_TYPE": "drvSummaryView",
                              "AMOUNT": 2,
                              "CART_ID": "374f501f4567",
                              "TITLE_NUMBER": "GR12345",
                              "EVENT_ID": "Search"
                              }

FakeEmptySearchTransmissionJSON = {}


class TestCreateSearchMessage:

    def test_message_is_created_when_db_row_is_returned(self):
        created_message = legacy_transmission_queue.create_user_search_message(FakeReturnSearchRowFound)
        created_message = json.loads(created_message)
        assert created_message['TITLE_NUMBER'] == FakeSearchTransmissionJSON['TITLE_NUMBER']

    def test_message_is_not_created_when_no_row_returned(self):
        created_message = legacy_transmission_queue.create_user_search_message(FakeReturnNoSearchRowFound)
        assert created_message == {}

    def integration_test_message_is_published_when_created_message_is_not_empty(self):
        sent_message = legacy_transmission_queue.send_legacy_transmission(FakeSearchTransmissionJSON)
        assert sent_message is True

    def integration_test_message_is_not_published_when_created_message_is_empty(self):
        sent_message = legacy_transmission_queue.send_legacy_transmission(FakeEmptySearchTransmissionJSON)
        assert sent_message is False
