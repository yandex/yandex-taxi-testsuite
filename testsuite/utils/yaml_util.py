import yaml
import yaml.parser


class BaseError(Exception):
    pass


class ParserError(BaseError):
    pass


if hasattr(yaml, 'CLoader'):
    _Loader = yaml.CLoader  # type: ignore
else:
    _Loader = yaml.Loader  # type: ignore


def load_file(path, encoding='utf-8'):
    with open(path, 'r', encoding=encoding) as fp:
        return load(fp)


def load(string_or_stream):
    try:
        return yaml.load(string_or_stream, Loader=_Loader)
    except yaml.parser.ParserError as exc:
        raise ParserError(str(exc)) from exc
