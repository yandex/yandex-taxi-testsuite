from testsuite import matching


def test_repr():
    assert repr(matching.Gt(0)) == '<gt 0>'


def test_gt():
    assert matching.Gt(0) != 0
    assert matching.Gt(0) == 1
    assert matching.Gt(0) != -1
    assert matching.Gt(0) != 'foo'


def test_ge():
    assert matching.Ge(0) == 0
    assert matching.Ge(0) == 1
    assert matching.Ge(0) != -1
    assert matching.Ge(0) != 'foo'


def test_lt():
    assert matching.Lt(0) != 0
    assert matching.Lt(0) != 1
    assert matching.Lt(0) == -1
    assert matching.Lt(0) != 'foo'


def test_le():
    assert matching.Le(0) == 0
    assert matching.Le(0) != 1
    assert matching.Le(0) == -1
    assert matching.Le(0) != 'foo'


def test_equality():
    assert matching.Gt(0) == matching.Gt(0)
    assert matching.Gt(0) != matching.Gt(1)
    assert matching.Gt(0) != matching.Lt(0)


def test_visit():
    pred = matching.Ge(0)
    visited = []

    def visitor(value):
        visited.append(value)
        return value

    copy = pred.__testsuite_visit__(visitor)
    assert visited == [0]
    assert copy == pred
    assert copy is not pred
