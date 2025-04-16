from testsuite.plugins.servicelogs import LogFileReporter


def test_reporter(tmp_path):
    def formatter(line: bytes):
        return f'message: {line.decode("utf-8").strip()}'

    logfile = LogFileReporter(
        tmp_path / 'log', formatter_factory=lambda: formatter
    )
    with logfile.path.open('wb') as fp:
        fp.write(b'foo\n')
        fp.flush()

    assert logfile.make_report() == 'message: foo\n'


def test_reporter_noline(tmp_path):
    def formatter(line: bytes):
        return None

    logfile = LogFileReporter(
        tmp_path / 'log', formatter_factory=lambda: formatter
    )
    with logfile.path.open('wb') as fp:
        fp.write(b'foo\n')
        fp.flush()

    assert logfile.make_report() == ''
