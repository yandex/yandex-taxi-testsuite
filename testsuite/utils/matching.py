import collections.abc
import operator
import re

import dateutil.parser


class Any:
    """Matches any value."""

    def __repr__(self):
        return '<Any>'

    def __eq__(self, other):
        return True


class AnyString:
    """Matches any string."""

    def __repr__(self):
        return '<AnyString>'

    def __eq__(self, other):
        return isinstance(other, str)


class RegexString(AnyString):
    """Match string with regular expression.

    .. code-block:: python

       assert response.json() == {
          'order_id': matching.RegexString('^[0-9a-f]*$'),
          ...
       }
    """

    def __init__(self, pattern):
        self._pattern = re.compile(pattern)

    def __repr__(self):
        return f'<{self.__class__.__name__} pattern={self._pattern!r}>'

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self._pattern.match(other) is not None


class UuidString(RegexString):
    """Matches lower-case hexadecimal uuid string."""

    def __init__(self):
        super().__init__('^[0-9a-f]{32}$')


class ObjectIdString(RegexString):
    """Matches lower-case hexadecimal objectid string."""

    def __init__(self):
        super().__init__('^[0-9a-f]{24}$')


class DatetimeString(AnyString):
    """Matches datetime string in any format."""

    def __repr__(self):
        return '<DatetimeString>'

    def __eq__(self, other):
        if not super().__eq__(other):
            return False

        try:
            dateutil.parser.parse(other)
            return True
        except ValueError:
            return False


class IsInstance:
    """Match value by its type.

    Use this class when you only need to check value type.

    .. code-block:: python

       assert response.json() == {
          # order_id must be a string
          'order_id': matching.IsInstance(str),
          # int or float is acceptable here
          'weight': matching.IsInstance([int, float]),
          ...
       }
    """

    def __init__(self, types):
        self.types = types

    def __repr__(self):
        if isinstance(self.types, (list, tuple)):
            type_names = [t.__name__ for t in self.types]
        else:
            type_names = [self.types.__name__]
        return f'<of-type {", ".join(type_names)}>'

    def __eq__(self, other):
        return isinstance(other, self.types)


class And:
    """Logical AND on conditions.

    .. code-block:: python

       # match integer is in range [10, 100)
       assert num == matching.And([matching.Ge(10), matching.Lt(100)])
    """

    def __init__(self, *conditions):
        self.conditions = conditions

    def __repr__(self):
        conditions = [repr(cond) for cond in self.conditions]
        return f'<And {" ".join(conditions)}>'

    def __eq__(self, other):
        for condition in self.conditions:
            if condition != other:
                return False
        return True


class Or:
    """Logical OR on conditions.

    .. code-block:: python

       # match integers abs(num) >= 10
       assert num == matching.Or([matching.Ge(10), matching.Le(-10)])
    """

    def __init__(self, *conditions):
        self.conditions = conditions

    def __repr__(self):
        conditions = [repr(cond) for cond in self.conditions]
        return f'<Or {" ".join(conditions)}>'

    def __eq__(self, other):
        for condition in self.conditions:
            if condition == other:
                return True
        return False


class Not:
    """Condition inversion.

    Example:

    .. code-block:: python

       # check value is not 1
       assert value == matching.Not(1)
    """

    def __init__(self, condition):
        self.condition = condition

    def __repr__(self):
        return f'<Not {self.condition!r}>'

    def __eq__(self, other):
        return self.condition != other


class Comparator:
    op = operator.eq

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'<{self.op.__name__} {self.value}>'

    def __eq__(self, other):
        try:
            return self.op(other, self.value)
        except TypeError:
            return False


class Gt(Comparator):
    """Value is greater than.

    Example:

    .. code-block:: python

       # Value must be > 10
       assert value == matching.Gt(10)
    """

    op = operator.gt


class Ge(Comparator):
    """Value is greater or equal.

    Example:

    .. code-block:: python

       # Value must be >= 10
       assert value == matching.Ge(10)
    """

    op = operator.ge


class Lt(Comparator):
    """Value is less than.

    Example:

    .. code-block:: python

       # Value must be < 10
       assert value == matching.Lt(10)
    """

    op = operator.lt


class Le(Comparator):
    """Value is less or equal.

    Example:

    .. code-block:: python

       # Value must be <= 10
       assert value == matching.Le(10)
    """

    op = operator.le


class PartialDict(collections.abc.Mapping):
    """Partial dictionary comparison.

    Sometimes you only need to check dictionary subset ignoring all
    other keys. :py:class:`PartialDict` is there for this purpose.

    `PartialDict` is wrapper around regular `dict()` when instantiated
    all arguments are passed as is to internal dict object.

    Example:

    .. code-block:: python

       assert {'foo': 1, 'bar': 2} == matching.PartialDict({
           # Only check for foo >= 1 ignoring other keys
           'foo': matching.Ge(1),
       })
    """

    def __init__(self, *args, **kwargs):
        self._dict = dict(*args, **kwargs)

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return self._dict.get(item, any_value)

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def __repr__(self):
        return f'<PartialDict {self._dict!r}>'

    def __eq__(self, other):
        if not isinstance(other, collections.abc.Mapping):
            return False

        for key in self:
            if other.get(key) != self.get(key):
                return False

        return True


class UnorderedList:
    def __init__(self, sequence, key):
        self.value = sorted(sequence, key=key)
        self.key = key

    def __repr__(self):
        return f'<UnorderedList: {self.value}>'

    def __eq__(self, other):
        return sorted(other, key=self.key) == self.value


def unordered_list(sequence, *, key=None):
    """Unordered list comparison.

    You may want to compare lists without respect to order. For instance,
    when your service is serializing std::unordered_map to array.

    `unordered_list` can help you with that. It sorts both array before
    comparison.

    :param sequence: Initial sequence
    :param key: Sorting key function

    Example:

    .. code-block:: python

       assert [3, 2, 1] == matching.unordered_list([1, 2, 3])
    """
    return UnorderedList(sequence, key)


any_value = Any()
any_float = IsInstance(float)
any_integer = IsInstance(int)
any_numeric = IsInstance((int, float))
positive_float = And(any_float, Gt(0))
positive_integer = And(any_integer, Gt(0))
positive_numeric = And(any_numeric, Gt(0))
negative_float = And(any_float, Lt(0))
negative_integer = And(any_integer, Lt(0))
negative_numeric = And(any_numeric, Lt(0))
non_negative_float = And(any_float, Ge(0))
non_negative_integer = And(any_integer, Ge(0))
non_negative_numeric = And(any_numeric, Ge(0))
any_string = AnyString()
datetime_string = DatetimeString()
objectid_string = ObjectIdString()
uuid_string = UuidString()
