from testsuite import matching


def test_foo():
    assert {
        'foo': {'foo': 'bar'},
        'bar': [1, 2, 3, 6],
        'x': 1234,
    } == {
        'foo': {'foo': matching.any_integer},
        'bar': [
            matching.any_integer,
            matching.any_string,
            matching.any_integer,
        ],
        'x': matching.any_integer,
    }
