from testsuite import matching


def test_repr():
    assert (
        repr(matching.RegexString('foo'))
        == "<RegexString pattern=re.compile('foo')>"
    )


def test_regex_string():
    pred = matching.RegexString('^foo.*')
    assert pred == 'foo'
    assert pred == 'foobar'
    assert pred != 'fo'
    assert pred != 1

    assert matching.any_string == pred
    assert pred != matching.any_string


def test_uuid_string():
    assert matching.uuid_string == 'd08535a5904f4790bd8f95c51c1f3cbe'
    assert matching.uuid_string != 'foobar'


def test_objectid_string():
    assert matching.objectid_string == '5e64beab56d0bf70bd8eebbc'
    assert matching.objectid_string != 'foobar'


def test_equality():
    assert matching.RegexString('foo') == matching.RegexString('foo')
    assert matching.RegexString('foo') != matching.RegexString('bar')
