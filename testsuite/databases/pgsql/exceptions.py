class BaseError(Exception):
    pass


class PostgresqlError(BaseError):
    pass


class NameCannotBeShortend(BaseError):
    pass


def __tracebackhide__(excinfo):
    return excinfo.errisinstance(BaseError)
