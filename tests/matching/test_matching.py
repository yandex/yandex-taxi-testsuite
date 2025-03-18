from testsuite.utils import matching


def test_anystring():
    assert matching.any_string == 'foo'
    assert matching.any_string != b'foo'
    assert matching.any_string != 1

    assert matching.any_string == matching.any_string


def test_any_float():
    assert matching.any_float == 1.0
    assert matching.any_float != 1
    assert matching.any_float != 'foo'


def test_any_integer():
    assert matching.any_integer == 1
    assert matching.any_integer != 1.0
    assert matching.any_integer != 'foo'


def test_any_numeric():
    assert matching.any_numeric == 1
    assert matching.any_numeric == 1.0
    assert matching.any_numeric != 'foo'


def test_positive_float():
    assert matching.positive_float != 0.0
    assert matching.positive_float == 1.0
    assert matching.positive_float != -1.0
    assert matching.positive_float != 'foo'


def test_positive_integer():
    assert matching.positive_integer != 0
    assert matching.positive_integer == 1
    assert matching.positive_integer != -1
    assert matching.positive_integer != 'foo'


def test_positive_numeric():
    assert matching.positive_numeric != 0.0
    assert matching.positive_numeric == 1.0
    assert matching.positive_numeric != -1.0
    assert matching.positive_numeric != 0
    assert matching.positive_numeric == 1
    assert matching.positive_numeric != -1
    assert matching.positive_numeric != 'foo'


def test_negative_float():
    assert matching.negative_float != 0.0
    assert matching.negative_float != 1.0
    assert matching.negative_float == -1.0
    assert matching.negative_float != 'foo'


def test_negative_integer():
    assert matching.negative_integer != 0
    assert matching.negative_integer != 1
    assert matching.negative_integer == -1
    assert matching.negative_integer != 'foo'


def test_negative_numeric():
    assert matching.negative_numeric != 0.0
    assert matching.negative_numeric != 1.0
    assert matching.negative_numeric == -1.0
    assert matching.negative_numeric != 0
    assert matching.negative_numeric != 1
    assert matching.negative_numeric == -1
    assert matching.negative_numeric != 'foo'


def test_non_negative_float():
    assert matching.non_negative_float == 0.0
    assert matching.non_negative_float == 1.0
    assert matching.non_negative_float != -1.0
    assert matching.non_negative_float != 'foo'


def test_non_negative_integer():
    assert matching.non_negative_integer == 0
    assert matching.non_negative_integer == 1
    assert matching.non_negative_integer != -1
    assert matching.non_negative_integer != 'foo'


def test_non_negative_numeric():
    assert matching.non_negative_numeric == 0.0
    assert matching.non_negative_numeric == 1.0
    assert matching.non_negative_numeric != -1.0
    assert matching.non_negative_numeric == 0
    assert matching.non_negative_numeric == 1
    assert matching.non_negative_numeric != -1
    assert matching.non_negative_numeric != 'foo'
