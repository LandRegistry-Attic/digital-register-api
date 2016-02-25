import json
from decimal import Decimal
from datetime import datetime
from service import legacy_transmission_queue


FakeReturnSearchRowFound = {"search_datetime": datetime(2016, 1, 26, 13, 0, 30, 5449),
                            "user_id": "Test User",
                            "title_number": "GR12345",
                            "search_type": "D",
                            "purchase_type": "drvSummaryView",
                            "amount": Decimal('2'),
                            "cart_id": "374f501f4567",
                            "lro_trans_ref": None,
                            "viewed_datetime": None,
                           }

FakeReturnNoSearchRowFound = {}

FakeSearchTransmissionDict = {"SEARCH_DATETIME": "2016-01-26 13:00:30.005449",
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

FakeEmptySearchTransmissionDict = {}


class TestCreateSearchMessage:

    def test_message_is_created_when_db_row_is_returned(self):
        created_message = legacy_transmission_queue.create_user_search_message(FakeReturnSearchRowFound)
        created_message = json.loads(created_message)
        assert created_message['TITLE_NUMBER'] == FakeSearchTransmissionDict['TITLE_NUMBER']

    def test_message_is_not_created_when_no_row_returned(self):
        created_message = legacy_transmission_queue.create_user_search_message(FakeReturnNoSearchRowFound)
        created_message = json.loads(created_message)
        assert created_message == {}

    def integration_test_message_is_published_when_created_message_is_not_empty(self):
        sent_message = legacy_transmission_queue.send_legacy_transmission(FakeSearchTransmissionDict)
        assert sent_message is True

    def integration_test_message_is_not_published_when_created_message_is_empty(self):
        sent_message = legacy_transmission_queue.send_legacy_transmission(FakeEmptySearchTransmissionDict)
        assert sent_message is False


if __name__ == '__main__':

    test = TestCreateSearchMessage()
    # import pdb; pdb.set_trace()

    test.integration_test_message_is_published_when_created_message_is_not_empty()
