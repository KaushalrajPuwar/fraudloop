"""Structured JSON logging, optionally shipped to Logstash over TCP."""

from __future__ import annotations

import contextlib
import json
import logging
import logging.handlers
import queue
import socket
import sys
from datetime import UTC, datetime

# Attributes every LogRecord carries; anything else was passed via `extra=`
# and belongs in the JSON payload.
_RESERVED = frozenset(
    {
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "module", "msecs",
        "message", "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "thread", "threadName", "taskName",
    }
)


class JsonFormatter(logging.Formatter):
    """Render a LogRecord as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str, separators=(",", ":"))


class JsonSocketHandler(logging.Handler):
    """Write newline-delimited JSON to a TCP socket.

    Logstash's `tcp` input with `codec => json_lines` reads exactly this
    format. The standard SocketHandler is unusable here because it frames
    messages with a length prefix and pickles the record.

    Failures are swallowed on purpose: a log shipper that takes the
    application down with it is worse than a few lost lines.
    """

    def __init__(self, host: str, port: int, timeout: float = 2.0) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: socket.socket | None = None

    def _connect(self) -> socket.socket:
        if self._sock is None:
            self._sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        return self._sock

    def emit(self, record: logging.LogRecord) -> None:
        try:
            line = (self.format(record) + "\n").encode("utf-8")
            self._connect().sendall(line)
        except Exception:  # noqa: BLE001 - never let logging break the request
            self._reset()

    def _reset(self) -> None:
        if self._sock is not None:
            with contextlib.suppress(OSError):
                self._sock.close()
            self._sock = None

    def close(self) -> None:
        self._reset()
        super().close()


def configure_logging(
    level: str = "INFO",
    logstash_host: str | None = None,
    logstash_port: int = 5000,
) -> logging.handlers.QueueListener | None:
    """Install JSON logging on the root logger.

    Returns the QueueListener when Logstash shipping is active so the caller
    can stop it cleanly on shutdown.
    """
    root = logging.getLogger()
    root.setLevel(level)

    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    formatter = JsonFormatter()

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    root.addHandler(stream)

    if not logstash_host:
        return None

    socket_handler = JsonSocketHandler(logstash_host, logstash_port)
    socket_handler.setFormatter(formatter)

    log_queue: queue.Queue = queue.Queue(-1)
    queue_handler = logging.handlers.QueueHandler(log_queue)
    root.addHandler(queue_handler)

    listener = logging.handlers.QueueListener(log_queue, socket_handler, respect_handler_level=True)
    listener.start()
    return listener
