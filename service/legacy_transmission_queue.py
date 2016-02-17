import logging                                                  # type: ignore
import json                                                     # type: ignore
from kombu import BrokerConnection, Exchange, Queue, Producer   # type: ignore
from config import QUEUE_DICT                                   # type: ignore
from typing import List                                         # type: ignore

logger = logging.getLogger(__name__)

user_search_data_columns = ['SEARCH_DATETIME',
                            'USER_ID',
                            'TITLE_NUMBER',
                            'SEARCH_TYPE',
                            'PURCHASE_TYPE',
                            'AMOUNT',
                            'CART_ID',
                            'LRO_TRANS_REF',
                            'VIEWED_DATETIME']

OUTGOING_QUEUE = QUEUE_DICT['OUTGOING_QUEUE']
OUTGOING_QUEUE_HOSTNAME = QUEUE_DICT['OUTGOING_QUEUE_HOSTNAME']

outgoing_exchange = Exchange("legacy_transmission", type='direct')

queue = Queue(OUTGOING_QUEUE, outgoing_exchange, routing_key="legacy_transmission")

connection = BrokerConnection(hostname=OUTGOING_QUEUE_HOSTNAME,
                              userid=QUEUE_DICT['OUTGOING_QUEUE_USERID'],
                              password=QUEUE_DICT['OUTGOING_QUEUE_PASSWORD'],
                              virtual_host="/")
channel = connection.channel()

producer = Producer(channel, exchange=outgoing_exchange, routing_key="legacy_transmission")


# Publishes the user_search on the legacy_transmission_queue
def send_legacy_transmission(user_search_result: List[str]):
    user_search_transmission = create_user_search_message(user_search_result)
    if user_search_transmission:
        producer.publish(user_search_transmission, serializer="json", compression="zlib")
        return True
    else:
        return False


def create_user_search_message(user_search_result):
    if user_search_result:
        user_search_result = [str(i) for i in user_search_result]
        # This creates a new list by zipping the results and the column names together
        user_search_result = list(zip(user_search_data_columns, user_search_result))
        # This adds the event id for user_search
        user_search_result.append(('EVENT_ID', 'user_search'))
        # Convert into json format for the use as the message
        user_search_transmission = json.dumps(dict(user_search_result))
    else:
        user_search_transmission = {}

    return user_search_transmission