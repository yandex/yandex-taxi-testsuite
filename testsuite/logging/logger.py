import contextlib
import logging
import threading
import typing

from testsuite.utils import colors
from testsuite.utils import tskv


class Manager:
    def __init__(
            self,
            line_logger: 'LineLogger',
            output: typing.IO,
            ensure_newline: bool,
    ):
        self._line_logger = line_logger
        self._output = output
        self._ensure_newline = ensure_newline
        self._resumed = False

    def resume(self):
        if not self._resumed:
            self._line_logger.resume(self._output, self._ensure_newline)
            self._resumed = True

    def clear(self):
        self._line_logger.clear()


class LineLogger:
    def __init__(self):
        self._buffer = []
        self._ensure_newline = False
        self._lock = threading.Lock()
        self._output = None

    def writeline(self, line: str) -> None:
        with self._lock:
            if self._output:
                try:
                    self._writeline(line)
                except ValueError:
                    if not self._output.closed:
                        raise
                    # Capture manager closed output buffer.
                    self._output = None
            if not self._output:
                self._buffer.append(line)

    def resume(self, output, ensure_newline=True):
        with self._lock:
            self._output = output
            self._ensure_newline = ensure_newline
            self._flush_buffer()

    def suspend(self):
        with self._lock:
            self._output = None

    def clear(self):
        with self._lock:
            self._buffer = []

    @contextlib.contextmanager
    def temporary_suspend(self):
        with self._lock:
            log_manager = Manager(
                self, self._output, ensure_newline=self._ensure_newline,
            )
            self._output = None
        try:
            yield log_manager
        finally:
            log_manager.resume()

    def _writeline(self, line: str) -> None:
        if self._ensure_newline:
            print(file=self._output)
            self._ensure_newline = False
        print(line, file=self._output)

    def _flush_buffer(self) -> None:
        if self._buffer:
            for line in self._buffer:
                self._writeline(line)
            self._buffer = []


class Logger:
    """
    legacy class responsible for printing to console,
    will be replaced by standard python logging
    """

    def __init__(self, writer: LineLogger):
        self._writer = writer

    def writeline(self, line: str) -> None:
        self._writer.writeline(line)

    def log_service_line(self, line: str) -> None:
        """Log service output line."""
        self.writeline(line)

    def log_entry(self, entry: dict) -> None:
        """Log simple key-value entry."""
        line = tskv.dict_to_tskv(entry, add_header=False)
        self.writeline(line)


class ColoredLevelFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: colors.Colors.GRAY,
        logging.INFO: colors.Colors.BRIGHT_GREEN,
        logging.WARNING: colors.Colors.YELLOW,
        logging.ERROR: colors.Colors.RED,
        logging.CRITICAL: colors.Colors.BRIGHT_RED,
    }

    def __init__(self, *, colors_enabled=False):
        super().__init__()
        self._colors_enabled = colors_enabled

    def format(self, record: logging.LogRecord):
        message = super().format(record)
        if not self._colors_enabled:
            return f'{record.levelname} {message}'
        color = self.LEVEL_COLORS.get(record.levelno, colors.Colors.DEFAULT)
        return f'{color}{record.levelname}{colors.Colors.DEFAULT} {message}'


class Handler(logging.Handler):
    def __init__(self, *, writer: Logger, level=logging.NOTSET):
        super().__init__(level)
        self._writer = writer

    def emit(self, record):
        if hasattr(record, 'tskv'):
            self._writer.log_entry(
                {**record.tskv, 'text': record.msg, 'level': record.levelname},
            )
        else:
            message = self.format(record)
            self._writer.writeline(message)
