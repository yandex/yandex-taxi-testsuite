import operator
import re

import dateutil.parser


class AnyString:
    """Matches any string."""

    def __repr__(self):
        return '<AnyString>'

    def __eq__(self, other):
        return isinstance(other, str)


class RegexString(AnyString):
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
    op = operator.gt


class Ge(Comparator):
    op = operator.ge


class Lt(Comparator):
    op = operator.lt


class Le(Comparator):
    op = operator.le


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
