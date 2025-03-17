import pytest

from testsuite.utils import matching


def test_capture():
    capture_foo = matching.Capture()
    pattern = {'foo': capture_foo}
    assert pattern == {'foo': 'bar'}
    assert capture_foo.value == 'bar'
    assert capture_foo.values_list == ['bar']


def test_capture_multiple():
    capture_foo = matching.Capture()
    pattern = {'foo': capture_foo}
    assert pattern == {'foo': 'bar'}
    assert pattern == {'foo': 'baz'}
    assert capture_foo.value == 'bar'
    assert capture_foo.values_list == ['bar', 'baz']


def test_capture_failure():
    capture_foo = matching.Capture(matching.any_string)
    pattern = {'foo': capture_foo}
    assert pattern != {'foo': 1}
    with pytest.raises(matching.NoValueCapturedError):
        capture_foo.value
    assert capture_foo.values_list == []


def test_capture_linked():
    capture_foo = matching.Capture()
    assert {'foo': 'bar'} == {'foo': capture_foo(matching.any_string)}

    assert capture_foo.value == 'bar'
    assert capture_foo.values_list == ['bar']


def test_deep_capture():
    capture_foo = matching.Capture()
    assert {
        'foo': {
            'items': [
                {'name': 'foo'},
                {'name': 'bar', 'last': 'bar'},
                {'name': 'maurice'},
            ],
            'extra': ...,
        },
    } == {
        'foo': matching.PartialDict(
            {
                'items': matching.ListOf(
                    matching.PartialDict(
                        {
                            'name': capture_foo(matching.any_string),
                        }
                    )
                )
            }
        ),
    }

    assert capture_foo.value == 'foo'
    assert capture_foo.values_list == ['foo', 'bar', 'maurice']
