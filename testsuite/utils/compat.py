import contextlib

# Required for python3.6 compatibility
if not hasattr(contextlib, 'asynccontextmanager'):
    import contextlib2  # pylint: disable=import-error
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
