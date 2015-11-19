from datetime import datetime
import json
import pg8000
import re
from config import CONFIG_DICT
from service import db_access

INSERT_TITLE_QUERY_FORMAT = (
    'insert into title_register_data('
    'title_number, register_data, geometry_data, is_deleted, last_modified, official_copy_data, lr_uprns'
    ')'
    'values('
    "%s, %s, %s, %s, %s, %s, '{{ {} }}'"
    ')'
)

DELETE_ALL_TITLES_QUERY = 'delete from title_register_data;'


def _get_db_connection_params():
    connection_string_regex = (
        r'^.*?//(?P<user>.+?):(?P<password>.+?)@(?P<host>.+?):(?P<port>\d+)/(?P<database>.+)$'
    )

    db_connection_string = CONFIG_DICT['SQLALCHEMY_DATABASE_URI']
    matches = re.match(connection_string_regex, db_connection_string)

    return {
        'user': matches.group('user'),
        'password': matches.group('password'),
        'host': matches.group('host'),
        'port': int(matches.group('port')),
        'database': matches.group('database'),
    }


DB_CONNECTION_PARAMS = _get_db_connection_params()


class TestDbAccess:

    def setup_method(self, method):
        self.connection = self._connect_to_db()
        self._delete_all_titles()

    def teardown_method(self, method):
        try:
            self.connection.close()
        except (pg8000.InterfaceError):
            pass

    def test_get_title_register_returns_none_when_title_not_in_the_db(self):
        assert db_access.get_title_register('non-existing') is None

    def test_get_title_register_returns_none_when_title_marked_as_deleted(self):
        title_number = 'title123'
        self._create_title(title_number, is_deleted=True)

        title = db_access.get_title_register(title_number)
        assert title is None

    def test_get_title_register_returns_title_data_when_title_not_marked_as_deleted(self):
        title_number = 'title123'
        register_data = {'register': 'data1'}
        geometry_data = {'geometry': 'data2'}
        is_deleted = False
        last_modified = datetime(2015, 9, 10, 12, 34, 56, 123)
        official_copy_data = {'official': 'copy'}
        lr_uprns = ['123', '456']

        self._create_title(title_number, register_data, geometry_data, is_deleted, last_modified, official_copy_data, lr_uprns)

        title = db_access.get_title_register(title_number)
        assert title is not None
        assert title.title_number == title_number
        assert title.register_data == register_data
        assert title.geometry_data == geometry_data
        assert title.is_deleted == is_deleted
        assert title.last_modified.timestamp() == last_modified.timestamp()
        assert title.official_copy_data == official_copy_data
        assert title.lr_uprns == lr_uprns

    def test_get_title_registers_returns_titles_with_right_content(self):
        title_number = 'title123'
        register_data = {'register': 'data1'}
        geometry_data = {'geometry': 'data2'}
        is_deleted = False
        last_modified = datetime(2015, 9, 10, 12, 34, 56, 123)
        official_copy_data = {'official': 'copy'}
        lr_uprns = ['123', '456']

        self._create_title(title_number, register_data, geometry_data, is_deleted, last_modified, official_copy_data, lr_uprns)

        titles = db_access.get_title_registers([title_number])

        assert len(titles) == 1
        title = titles[0]

        assert title is not None
        assert title.title_number == title_number
        assert title.register_data == register_data
        assert title.geometry_data == geometry_data
        assert title.is_deleted == is_deleted
        assert title.last_modified.timestamp() == last_modified.timestamp()
        assert title.official_copy_data == official_copy_data
        assert title.lr_uprns == lr_uprns

    def test_get_title_registers_returns_list_with_all_existing_titles(self):
        existing_title_numbers = {'title1', 'title2', 'title3'}

        for title_number in existing_title_numbers:
            self._create_title(title_number)

        titles = db_access.get_title_registers(existing_title_numbers | {'non-existing-1'})

        assert len(titles) == 3
        returned_title_numbers = self._get_title_numbers(titles)
        assert existing_title_numbers == returned_title_numbers

    def test_get_title_registers_returns_empty_list_when_no_title_found(self):
        titles = db_access.get_title_registers(['non-existing-1', 'non-existing-2'])
        assert titles == []

    def test_get_title_registers_does_not_return_deleted_titles(self):
        existing_title_number_1 = 'existing-1'
        existing_title_number_2 = 'existing-2'
        deleted_title_number_1 = 'deleted-1'
        deleted_title_number_2 = 'deleted-2'

        self._create_title(existing_title_number_1, is_deleted=False)
        self._create_title(existing_title_number_2, is_deleted=False)

        self._create_title(deleted_title_number_1, is_deleted=True)
        self._create_title(deleted_title_number_2, is_deleted=True)

        titles = db_access.get_title_registers([
            existing_title_number_1, deleted_title_number_1, existing_title_number_2, deleted_title_number_2
        ])

        assert len(titles) == 2
        assert self._get_title_numbers(titles) == {existing_title_number_1, existing_title_number_2}

    def test_get_official_copy_data_returns_none_when_title_not_in_the_db(self):
        assert db_access.get_official_copy_data('non-existing') is None

    def test_get_official_copy_data_returns_none_when_title_marked_as_deleted(self):
        title_number = 'title123'
        self._create_title(title_number, is_deleted=True, official_copy_data={'official': 'copy'})

        title = db_access.get_official_copy_data(title_number)
        assert title is None

    def test_get_official_copy_data_returns_the_copy_when_title_in_the_db(self):
        title_number = 'title123'
        register_data = {'register': 'data1'}
        geometry_data = {'geometry': 'data2'}
        is_deleted = False
        last_modified = datetime(2015, 9, 10, 12, 34, 56, 123)
        official_copy_data = {'official': 'copy'}
        lr_uprns = ['123', '456']

        self._create_title(title_number, register_data, geometry_data, is_deleted, last_modified, official_copy_data, lr_uprns)

        title = db_access.get_official_copy_data(title_number)
        assert title is not None
        assert title.title_number == title_number
        assert title.register_data == register_data
        assert title.geometry_data == geometry_data
        assert title.is_deleted == is_deleted
        assert title.last_modified.timestamp() == last_modified.timestamp()
        assert title.official_copy_data == official_copy_data
        assert title.lr_uprns == lr_uprns

    def _get_title_numbers(self, titles):
        return set(map(lambda title: title.title_number, titles))

    def _create_title(
            self,
            title_number,
            register_data={},
            geometry_data={},
            is_deleted=False,
            last_modified=datetime.now(),
            official_copy_data={},
            lr_uprns=[]):

        print(INSERT_TITLE_QUERY_FORMAT.format(self._get_string_list_for_pg(lr_uprns)))

        self.connection.cursor().execute(
            INSERT_TITLE_QUERY_FORMAT.format(self._get_string_list_for_pg(lr_uprns)),
            (
                title_number,
                json.dumps(register_data),
                json.dumps(geometry_data),
                is_deleted,
                last_modified,
                json.dumps(official_copy_data),
            )
        )

        return self.connection.commit()

    def _get_string_list_for_pg(self, strings):
        return ','.join(['"{}"'.format(s) for s in strings])

    def _delete_all_titles(self):
        self.connection.cursor().execute(DELETE_ALL_TITLES_QUERY)
        self.connection.commit()

    def _connect_to_db(self):
        return pg8000.connect(**DB_CONNECTION_PARAMS)
