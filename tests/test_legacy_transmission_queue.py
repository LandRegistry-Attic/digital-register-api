import json
from decimal import Decimal
from datetime import datetime, date, time
from service import legacy_transmission_queue

FakeReturnSearchRowFound = ['1234', 'D', '99', Decimal('2'),
                                 'CC', 'VISA ELECTRON UK DEB',
                                 'GR12345', datetime(2015, 12, 1, 14, 34, 14, 362556),
                                 date(2001, 12, 12), time(14, 34, 14, 362556),
                                 '1', datetime(2016, 1, 26, 13, 0, 30, 5449), 'D', '',
                                 '1111', 'W', 1]

FakeReturnNoSearchRowFound = None

FakeSearchTransmissionJSON = {"DOC_DLOAD_TMSTMP": "2016-01-26 13:00:30.005449",
                                   "PRTL_TRANS_IND": "",
                                   "CA_TRANS_CODE": "D",
                                   "COST_CENTRE_CODE": "99",
                                   "LRO_TRANS_REF": "1234",
                                   "UNIT_COUNT": "1",
                                   "PAYM_CARD_TYPE": "VISA ELECTRON UK DEB",
                                   "AUTH_RESULT_WARN": "W",
                                   "LRO_PTY_ENQ_CODE": "D",
                                   "METHOD_PAYM_CODE": "CC",
                                   "TRANS_START_TMSTMP": "2015-12-01 14:34:14.362556",
                                   "AVS_RESULT_CODE": "1111",
                                   "TRANS_COMPT_DATE": "2001-12-12",
                                   "TRANS_COMPT_TIME": "14:34:14.362556",
                                   "LRO_SESSION_ID": "1",
                                   "EVENT_ID": "Search",
                                   "FEE_AMT": "2",
                                   "TITLE_NO": "GR12345"}

FakeEmptySearchTransmissionJSON = {}


class TestCreateSearchMessage:

    def test_message_is_created_when_db_row_is_returned(self):
        created_message = legacy_transmission_queue.create_user_search_message(FakeReturnSearchRowFound)
        created_message = json.loads(created_message)
        assert created_message['TITLE_NO'] == FakeSearchTransmissionJSON['TITLE_NO']

    def test_message_is_not_created_when_no_row_returned(self):
        created_message = legacy_transmission_queue.create_user_search_message(FakeReturnNoSearchRowFound)
        assert created_message == {}

    def test_message_is_published_when_created_message_is_not_empty(self):
        sent_message = legacy_transmission_queue.send_legacy_transmission(FakeSearchTransmissionJSON)
        assert sent_message is True

    def test_message_is_not_published_when_created_message_is_empty(self):
        sent_message = legacy_transmission_queue.send_legacy_transmission(FakeEmptySearchTransmissionJSON)
        assert sent_message is False
