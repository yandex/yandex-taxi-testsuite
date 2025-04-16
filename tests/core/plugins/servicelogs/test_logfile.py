import itertools
import pathlib

from testsuite._internal.logreader import LogFile


def test_filesize(get_file_path):
    logfile = LogFile(get_file_path('sample.log'))
    assert logfile.filesize() > 0

    logfile = LogFile(pathlib.Path('does-not-exist'))
    assert logfile.filesize() == 0


def test_update_position(tmp_path):
    logfile = LogFile(tmp_path / 'log')
    with logfile.path.open('wb') as fp:
        assert logfile.position == 0
        assert logfile.update_position() == 0

        fp.write(b'foo\n')
        fp.flush()

        assert logfile.update_position() == 4
        assert logfile.position == 4


def test_readlines(tmp_path):
    logfile = LogFile(tmp_path / 'log')
    with logfile.path.open('wb') as fp:
        fp.write(b'foo\n')
        fp.flush()

        lines = list(logfile.readlines())
        assert lines == [b'foo\n']

        fp.write(b'bar\n')
        fp.flush()

        lines = list(logfile.readlines())
        assert lines == [b'bar\n']


def test_readlines_eof_handler(tmp_path):
    logfile = LogFile(tmp_path / 'log')
    with logfile.path.open('wb') as fp:
        fp.write(b'foo\n')
        fp.flush()

        def eof_handler(counter=itertools.count()):
            if next(counter):
                return True
            fp.write(b'bar\n')
            fp.flush()
            return False

        lines = list(logfile.readlines(eof_handler=eof_handler))
        assert lines == [b'foo\n', b'bar\n']


def test_readlines_limit(tmp_path):
    logfile = LogFile(tmp_path / 'log')
    with logfile.path.open('wb') as fp:
        fp.write(b'foo\n')
        fp.flush()

        def eof_handler(counter=itertools.count()):
            return False

        lines = list(
            logfile.readlines(limit_position=True, eof_handler=eof_handler)
        )
        assert lines == [b'foo\n']


def test_readlines_partial(tmp_path):
    logfile = LogFile(tmp_path / 'log')
    with logfile.path.open('wb') as fp:
        fp.write(b'foo')
        fp.flush()

        lines = list(logfile.readlines())
        assert lines == []

        def eof_handler(counter=itertools.count()):
            if next(counter):
                return True
            fp.write(b'bar\n')
            fp.flush()
            return False

        logfile = LogFile(logfile.path)
        lines = list(logfile.readlines(eof_handler=eof_handler))
        assert lines == [b'foobar\n']
