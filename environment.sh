#!/bin/sh
export SETTINGS='dev'
export POSTGRES_USER='postgres'
export POSTGRES_PASSWORD='password'
export POSTGRES_HOST='172.16.42.43'
export POSTGRES_PORT=5432
export POSTGRES_DB='register_data'
export LOGGING_CONFIG_FILE_PATH='logging_config.json'
export FAULT_LOG_FILE_PATH='/var/log/applications/digital-register-api-fault.log'
export ELASTIC_SEARCH_ENDPOINT='http://localhost:9200'
export MAX_NUMBER_SEARCH_RESULTS=50
export PYTHONPATH=.
export SEARCH_RESULTS_PER_PAGE=20
