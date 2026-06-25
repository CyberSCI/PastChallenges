"""OpenSearch logging handler for shipping Django logs to OpenSearch."""

import atexit
import json
import logging
import logging.handlers
import os
import queue
import threading

from opensearchpy.exceptions import (
    ConnectionError as OSConnectionError,
)
from opensearchpy.exceptions import (
    TransportError,
)
from structlog.typing import EventDict, WrappedLogger

from shared.opensearch import OpenSearchLogClient


class _OpenSearchEmitter(logging.Handler):
    """Internal handler that batches records and bulk-sends to OpenSearch.

    Collects up to ``batch_size`` records, then flushes via the bulk API
    in a single HTTP call.  The ``QueueListener`` thread calls ``emit()``
    sequentially, so no extra locking is needed.
    """

    BATCH_SIZE = 50
    FLUSH_INTERVAL = 2.0  # seconds

    def __init__(
        self,
        opensearch_url: str = "http://localhost:9200",
        index_prefix: str = "django-logs",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._client: OpenSearchLogClient = OpenSearchLogClient(
            opensearch_url=opensearch_url, index_prefix=index_prefix
        )
        self._batch: list[logging.LogRecord] = []
        self._last_flush = threading.Event()
        self._flush_timer: threading.Timer | None = None
        self._schedule_flush()

    def emit(self, record: logging.LogRecord) -> None:
        self._batch.append(record)
        if len(self._batch) >= self.BATCH_SIZE:
            self._flush()

    def _flush(self) -> None:
        batch, self._batch = self._batch, []
        if not batch:
            return
        try:
            self._client.send_logs_bulk(batch)
        except (OSConnectionError, TransportError, Exception):
            if batch:
                self.handleError(batch[-1])
        self._schedule_flush()

    def _schedule_flush(self) -> None:
        if self._flush_timer is not None:
            self._flush_timer.cancel()
        self._flush_timer = threading.Timer(
            self.FLUSH_INTERVAL, self._flush
        )
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def close(self) -> None:
        if self._flush_timer is not None:
            self._flush_timer.cancel()
        self._flush()
        super().close()


class OpenSearchHandler(logging.Handler):
    """Non-blocking logging handler that ships logs to OpenSearch.

    Enqueues records into an in-memory queue and drains them on a
    background thread via ``QueueListener``, so the calling thread
    (gunicorn worker) is never blocked by OpenSearch I/O.

    Inherits from ``logging.Handler`` (not ``QueueHandler``) to avoid
    Python 3.12+ ``dictConfig`` special-casing of ``QueueHandler``
    subclasses.
    """

    def __init__(
        self,
        opensearch_url: str = "http://localhost:9200",
        index_prefix: str = "django-logs",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._queue: queue.Queue[logging.LogRecord] = queue.Queue(
            maxsize=1024
        )

        emitter = _OpenSearchEmitter(
            opensearch_url=opensearch_url,
            index_prefix=index_prefix,
        )
        self._listener = logging.handlers.QueueListener(
            self._queue, emitter, respect_handler_level=True
        )
        self._listener.start()
        atexit.register(self._listener.stop)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            self.handleError(record)


def add_metadata(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    metadata = json.loads(os.environ.get("LOGGER_METADATA_JSON", "{}"))
    event_dict.update(metadata)
    return event_dict
