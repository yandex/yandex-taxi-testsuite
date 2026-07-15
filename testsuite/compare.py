import dataclasses
import typing


class Reporter(typing.Protocol):
    def __call__(self, msg: str, *, path: typing.Any) -> None:
        pass


@dataclasses.dataclass(kw_only=True)
class CompareVisitor:
    """
    Extension point for `pytest_register_compare_visitors`: lets a plugin
    teach the `assertrepr_compare` machinery how to decompose a custom type
    into something comparable (e.g. a nested dict/list/set), so that a
    failing `==` assertion involving it gets a helpful diff.
    """

    class Predicate(typing.Protocol):
        def __call__(self, left: typing.Any, right: typing.Any) -> bool:
            pass

    class Visitor(typing.Protocol):
        def __call__(
            self,
            left: typing.Any,
            right: typing.Any,
            reporter: Reporter,
        ) -> tuple[typing.Any, typing.Any]:
            pass

    predicate: Predicate
    visit: Visitor
