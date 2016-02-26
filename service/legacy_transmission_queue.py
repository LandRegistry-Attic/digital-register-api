import logging                                                  # type: ignore
import json                                                     # type: ignore
from kombu import BrokerConnection, Exchange, Queue, Producer   # type: ignore
from config import QUEUE_DICT                                   # type: ignore
from typing import Dict                                         # type: ignore

logger = logging.getLogger(__name__)


USER_SEARCH_INSERT = 2

# Loosely derived from kombu /examples/complete_send_manual.py
def create_legacy_queue_connection():

    OUTGOING_QUEUE = QUEUE_DICT['OUTGOING_QUEUE']
    OUTGOING_QUEUE_HOSTNAME = QUEUE_DICT['OUTGOING_QUEUE_HOSTNAME']

    outgoing_exchange = Exchange("legacy_transmission", type='direct')

    queue = Queue(OUTGOING_QUEUE, outgoing_exchange, routing_key="legacy_transmission")

    connection = BrokerConnection(hostname=OUTGOING_QUEUE_HOSTNAME,
                                  userid=QUEUE_DICT['OUTGOING_QUEUE_USERID'],
                                  password=QUEUE_DICT['OUTGOING_QUEUE_PASSWORD'],
                                  virtual_host="/")

    # Queue must be declared, otherwise messages are silently sent to a 'black hole'!
    bound_queue = queue(connection)
    bound_queue.declare()

    producer = Producer(connection, exchange=outgoing_exchange, routing_key="legacy_transmission")

    return producer


def send_legacy_transmission(user_search_result: Dict):
    producer = create_legacy_queue_connection()
    user_search_transmission = create_user_search_message(user_search_result)
    if user_search_transmission:
        producer.publish(user_search_transmission, serializer="json", compression="zlib")
        return True
    else:
        return False


def create_user_search_message(user_search_result: Dict):

    # Prepare for serialisation: values must be sent as strings.
    user_search_transmission = {k: str(v) for k, v in user_search_result.items()}

    # Add the relevant event id.
    if user_search_transmission:
        user_search_transmission['EVENT_ID'] = USER_SEARCH_INSERT

    return json.dumps(user_search_transmission)
