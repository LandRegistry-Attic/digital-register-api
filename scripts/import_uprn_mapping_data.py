#!/usr/bin/python
import argparse
import csv
import logging
from logging.config import dictConfig  # type: ignore
import os
import pg8000  # type: ignore

LOGGER = logging.getLogger(__name__)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s level=[%(levelname)s] logger=[%(name)s] thread=[%(threadName)s] message=[%(message)s] exception=[%(exc_info)s]'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}


def import_mapping_data(input_file_path, lines_to_skip, overwrite_existing, clear_data, page_size):
    """Reads the input CSV file and saves its lines in the database"""

    _log_data_import_started(input_file_path, lines_to_skip, clear_data, overwrite_existing)
    connection = None

    try:
        with open(input_file_path) as file:
            reader = csv.reader(file, delimiter=',', quotechar='"')

            connection = _connect_to_db()
            db_cursor = connection.cursor()

            if clear_data:
                _clear_mapping_table(db_cursor)
                db_cursor.connection.commit()

            overwrite_db_rows = overwrite_existing and not clear_data
            _process_input_lines(reader, db_cursor, lines_to_skip, overwrite_db_rows, page_size)

            LOGGER.info('Completed import')
    except Exception as e:
        LOGGER.error('An error occurred when importing mapping data', exc_info=e)
    finally:
        if connection:
            connection.close()


def _process_uprn_mapping(cursor, uprn, lr_uprn, overwrite, row_buffer, page_size):
    updated_buffer = row_buffer + [(uprn, lr_uprn)]

    if len(updated_buffer) >= page_size:
        _flush_to_db(cursor, overwrite, updated_buffer)
        return []

    return updated_buffer


def _flush_to_db(db_cursor, overwrite_existing, row_buffer):
    """Saves the content of the cache (row_buffer) into the database"""

    if overwrite_existing:
        uprns = [str(row[0]) for row in row_buffer]
        _delete_entries_by_uprn(db_cursor, uprns)

    _insert_mapping_data(db_cursor, row_buffer)
    db_cursor.connection.commit()


def _process_input_lines(csv_reader, db_cursor, lines_to_skip, overwrite, page_size):
    if lines_to_skip > 0:
        LOGGER.info('Skipping first {} lines'.format(lines_to_skip))

    current_line_number = 1
    row_buffer = []

    for row in csv_reader:
        if current_line_number > lines_to_skip:
            uprn = row[1].replace('"', '').strip()
            lr_uprn = row[0].strip()
            row_buffer = _process_uprn_mapping(db_cursor, uprn, lr_uprn, overwrite, row_buffer, page_size)

            if not row_buffer:
                _log_records_saved(page_size, total=current_line_number - lines_to_skip)

        current_line_number += 1

    total_records = current_line_number - lines_to_skip - 1
    _process_remaining_buffered_data(row_buffer, db_cursor, overwrite, total_records)


def _process_remaining_buffered_data(row_buffer, db_cursor, overwrite, total_records):
    nof_remaining_records = len(row_buffer)

    if nof_remaining_records > 0:
        _flush_to_db(db_cursor, overwrite, row_buffer)
        _log_records_saved(nof_remaining_records, total_records)


def _log_data_import_started(input_file_path, lines_to_skip, clear_data, overwrite_existing):
    LOGGER.info('Starting data import. From file: {}, lines to skip: {}, clear DB: {}, overwrite existing {}'.format(
        input_file_path, lines_to_skip, clear_data, overwrite_existing
    ))


def _log_records_saved(number_of_records, total):
    LOGGER.info('Saved {} records. Total saved: {}'.format(number_of_records, total))


def _setup_logging():
    try:
        dictConfig(LOGGING_CONFIG)
    except IOError as e:
        raise(Exception('Failed to load logging configuration', e))


def _connect_to_db():
    return pg8000.connect(
        host=os.environ['POSTGRES_HOST'],
        port=int(os.environ['POSTGRES_PORT']),
        database=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
    )


def _parse_command_line_args():
    parser = argparse.ArgumentParser(
        description='This script imports mapping data (from URPN to Land Registry "UPRN") from a CSV file into the database'
    )

    parser.add_argument('-f', '--file', type=str, required=True, help='Source CSV file path')
    parser.add_argument('-s', '--skip', type=int, default=0, help='Number of first records to skip')
    parser.add_argument('-o', '--overwrite', nargs='?', const=True, default=False, help='When present, existing records are overwritten')
    parser.add_argument('-c', '--clear', nargs='?', const=True, default=False, help='When present, DB data is cleared before the import')
    parser.add_argument('-p', '--page_size', default=5000, help='Page size - number of records to save into to DB at once')

    return parser.parse_args()


def _insert_mapping_data(db_cursor, rows):
    db_cursor.executemany('insert into uprn_mapping (uprn, lr_uprn) values (%s, %s)', rows)


def _delete_entries_by_uprn(db_cursor, uprns):
    # TODO: this shouldn't be done using string.format, but I couldn't get pg8000 to work with lists
    db_cursor.execute("delete from uprn_mapping where uprn in ('{}')".format("','".join(uprns)))


def _clear_mapping_table(db_cursor):
    db_cursor.execute('delete from uprn_mapping')

if __name__ == '__main__':
    args = _parse_command_line_args()

    _setup_logging()
    import_mapping_data(args.file, args.skip, args.overwrite, args.clear, args.page_size)
