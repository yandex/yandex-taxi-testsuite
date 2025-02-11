import contextlib


# Required for python3.6 compatibility
if not hasattr(contextlib, 'asynccontextmanager'):
    # pylint: disable=import-error
    import contextlib2  # type: ignore

    asynccontextmanager = contextlib2.asynccontextmanager
else:
    asynccontextmanager = contextlib.asynccontextmanager


if not hasattr(contextlib, 'aclosing'):

    @asynccontextmanager
    async def aclosing(obj):
        try:
            yield obj
        finally:
            await obj.aclose()

else:
    aclosing = contextlib.aclosing
