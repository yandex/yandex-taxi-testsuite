import pathlib

import pytest

from testsuite.databases.mysql import discover

SCHEMAS_DIR = pathlib.Path(__file__).parent.joinpath('schemas')


@pytest.fixture(scope='session')
def mysql_local():
    return discover.find_schemas([SCHEMAS_DIR])


@pytest.mark.mysql(
    'testdb',
    queries=[
        'INSERT INTO foo (id, value) VALUES (1, "foo")',
        'INSERT INTO foo (id, value) VALUES (2, "bar")',
    ],
)
def test_foo(mysql):
    cursor = mysql['testdb'].cursor()

    cursor.execute('select * from foo order by id')
    assert cursor.fetchall() == ((1, 'foo'), (2, 'bar'))

    cursor.execute('select * from bar order by id')
    assert cursor.fetchall() == ()


@pytest.mark.mysql(
    'testdb',
    queries=[
        'INSERT INTO bar (id, value) VALUES (1, "foo")',
        'INSERT INTO bar (id, value) VALUES (2, "bar")',
    ],
)
def test_bar(mysql):
    cursor = mysql['testdb'].cursor()

    cursor.execute('select * from foo order by id')
    assert cursor.fetchall() == ()

    cursor.execute('select * from bar order by id')
    assert cursor.fetchall() == ((1, 'foo'), (2, 'bar'))


def test_file_data(mysql):
    cursor = mysql['testdb'].cursor()

    cursor.execute('select * from foo order by id')
    assert cursor.fetchall() == ((1, 'one'), (2, 'two'))

    cursor.execute('select * from bar order by id')
    assert cursor.fetchall() == ((1, 'foo'), (2, 'bar'))


@pytest.mark.mysql(
    'testdb', queries=['INSERT INTO foo (id, value) VALUES (1, "foo")'],
)
def test_dict_cursor(mysql):
    cursor = mysql['testdb'].dict_cursor()

    cursor.execute('select * from foo order by id')
    assert cursor.fetchone() == {'id': 1, 'value': 'foo'}
