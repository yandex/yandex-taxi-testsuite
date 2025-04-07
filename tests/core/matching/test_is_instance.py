from testsuite import matching


def test_repr():
    assert repr(matching.IsInstance(int)) == '<IsInstance int>'
    assert repr(matching.IsInstance((int, float))) == '<IsInstance int, float>'


def test_matching():
    assert matching.IsInstance(int) == 123
    assert matching.IsInstance(int) != 123.0


def test_equality():
    assert matching.IsInstance(int) == matching.IsInstance(int)
    assert matching.IsInstance(int) != matching.IsInstance(float)
