from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

_MAX_TEXT = 800


class _NoOp:
    def update(self, **_payload: Any) -> None:
        return None


class Tracer:
    def __init__(self) -> None:
        self.enabled = False
        self._client: Any | None = None
        self._environment = "development"

    def configure(
        self,
        *,
        public_key: str,
        secret_key: str,
        host: str,
        environment: str = "development",
    ) -> None:
        self._environment = environment
        if not public_key or not secret_key:
            self.enabled = False
            self._client = None
            return
        try:
            from langfuse import Langfuse

            self._client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host or "https://cloud.langfuse.com",
                environment=environment,
            )
            self.enabled = True
        except Exception:
            self.enabled = False
            self._client = None

    @contextmanager
    def trace(
        self,
        name: str,
        *,
        user_id: str | None = None,
        tags: list[str] | None = None,
        input: Any | None = None,
    ) -> Iterator[Any]:
        if self._client is None:
            yield _NoOp()
            return
        from langfuse import propagate_attributes

        attr_kwargs: dict[str, Any] = {"environment": self._environment}
        if user_id:
            attr_kwargs["user_id"] = user_id
        if tags:
            attr_kwargs["tags"] = tags
        attrs = propagate_attributes(**attr_kwargs)
        try:
            with attrs:
                with self._client.start_as_current_observation(
                    as_type="span",
                    name=name,
                    input=input,
                ) as root:
                    try:
                        root.set_trace_as_public()
                    except Exception:
                        pass
                    try:
                        yield root
                    except Exception as exc:
                        root.update(level="ERROR", status_message=str(exc)[:400])
                        raise
        finally:
            self.flush()

    @contextmanager
    def observation(
        self,
        name: str,
        *,
        as_type: str = "span",
        model: str | None = None,
        input: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Iterator[Any]:
        if self._client is None:
            yield _NoOp()
            return
        kwargs: dict[str, Any] = {"as_type": as_type, "name": name}
        if model:
            kwargs["model"] = model
        if input is not None:
            kwargs["input"] = input
        if metadata:
            kwargs["metadata"] = metadata
        with self._client.start_as_current_observation(**kwargs) as obs:
            try:
                yield obs
            except Exception as exc:
                obs.update(level="ERROR", status_message=str(exc)[:400])
                raise

    def flush(self) -> None:
        if self._client is None:
            return
        try:
            self._client.flush()
        except Exception:
            return


def clip_text(value: str, limit: int = _MAX_TEXT) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


tracer = Tracer()
