from logging.config import dictConfig  # type: ignore
import json
import logging

from config import CONFIG_DICT

done_setup = False


def setup_logging():
    global done_setup

    if not done_setup and CONFIG_DICT['LOGGING']:
        try:
            logging_config_file_path = CONFIG_DICT['LOGGING_CONFIG_FILE_PATH']
            with open(logging_config_file_path, 'rt') as file:
                config = json.load(file)
            dictConfig(config)
            service_logger = logging.getLogger('service')
            if CONFIG_DICT['LOGGING_LEVEL'] == "DEBUG":
                service_logger.setLevel(logging.DEBUG)
            elif CONFIG_DICT['LOGGING_LEVEL'] == "WARN":
                service_logger.setLevel(logging.WARN)
            else:
                service_logger.setLevel(logging.INFO)
            done_setup = True
        except IOError as e:
            raise(Exception('Failed to load logging configuration', e))
