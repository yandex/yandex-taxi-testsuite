class BaseError(Exception):
    """Base class for exceptions from this package."""


class MockServerError(BaseError):
    pass


class HandlerNotFoundError(MockServerError):
    pass
