import contextlib


if not hasattr(contextlib, 'aclosing'):

    @contextlib.asynccontextmanager
    async def aclosing(obj):
        try:
            yield obj
        finally:
            await obj.aclose()

else:
    aclosing = contextlib.aclosing
