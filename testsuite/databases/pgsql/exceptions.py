class BaseError(Exception):
    pass


class PostgresqlError(BaseError):
    pass


class NameCannotBeShortend(BaseError):
    pass
