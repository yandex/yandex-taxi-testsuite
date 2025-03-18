from testsuite.utils import matching


def test_repr():
    pred = matching.PartialDict(foo='bar')
    assert repr(pred) == "<PartialDict {'foo': 'bar'}>"


def test_partial_dict():
    sample = {
        'some_int': 1,
        'some_str': 'abc',
        'some_dict': {'a': 5, 'b': 'b', 'c': 6},
    }

    assert sample == matching.PartialDict(some_int=1)
    assert sample == matching.PartialDict(some_int=1, some_str='abc')
    assert sample == matching.PartialDict(
        some_int=1,
        some_str='abc',
        some_dict=matching.PartialDict(a=5),
    )

    assert sample != matching.PartialDict(some_int=2)
    assert sample != matching.PartialDict(unknown=3)
    assert sample != matching.PartialDict(
        some_int=1,
        some_str='abc',
        some_dict=matching.PartialDict(a=123, asd=55),
    )

    assert matching.PartialDict() != 5

    assert sample == matching.PartialDict({'some_int': 1})

    assert sample == matching.PartialDict(some_int=1)
    assert not (sample != matching.PartialDict(some_int=1))


def test_mapping():
    pred = matching.PartialDict(foo='bar')
    assert 'foo' in pred
    assert 'bar' in pred
    assert len(pred) == 1


def test_visit():
    pred = matching.PartialDict(foo='bar')

    visited = []

    def visitor(value):
        visited.append(value)
        return value

    copy = pred.__testsuite_visit__(visitor)

    assert visited == [{'foo': 'bar'}]
    assert copy == pred
    assert copy is not pred
