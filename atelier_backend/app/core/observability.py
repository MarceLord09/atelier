from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any


class Span:
    def __init__(self, observation: Any | None, started: float) -> None:
        self._observation = observation
        self._started = started

    @property
    def duration_ms(self) -> int:
        return int((perf_counter() - self._started) * 1000)

    def update(self, **payload: Any) -> None:
        if self._observation is None:
            return
        try:
            self._observation.update(**payload)
        except Exception:
            return


class Tracer:
    def __init__(self) -> None:
        self.enabled = False
        self._client: Any | None = None

    def configure(self, *, public_key: str, secret_key: str, host: str) -> None:
        if not public_key or not secret_key:
            self.enabled = False
            self._client = None
            return
        try:
            from langfuse import Langfuse

            self._client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
            self.enabled = True
        except Exception:
            self.enabled = False
            self._client = None

    @contextmanager
    def span(self, name: str, **metadata: Any) -> Iterator[Span]:
        started = perf_counter()
        observation = None
        if self._client is not None:
            try:
                observation = self._client.start_span(name=name, metadata=metadata or None)
            except Exception:
                observation = None
        span = Span(observation, started)
        try:
            yield span
        except Exception as exc:
            span.update(level="ERROR", status_message=str(exc)[:400])
            raise
        finally:
            if observation is not None:
                try:
                    observation.end()
                except Exception:
                    pass

    def flush(self) -> None:
        if self._client is None:
            return
        try:
            self._client.flush()
        except Exception:
            return


tracer = Tracer()
