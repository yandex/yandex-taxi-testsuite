import pathlib


async def test_formatter(servicelogs_register_logfile):
    def formatter(line: bytes):
        return line.decode('utf-8')

    servicelogs_register_logfile(
        pathlib.Path('oops'), title='oops', formatter_factory=lambda: formatter
    )


async def test_flusher(
    servicelogs_register_flusher, _servicelogs_logging_plugin
):
    async def flusher(): ...

    servicelogs_register_flusher(flusher)
