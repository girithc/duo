"""Redis Streams event bus — stages publish run events, the UI replays them.

One stream per run (`duo:run:<run_id>`), JSON payloads:

    {"event": "stage_start", "ts": 176..., "pid": 4242, "run_id": "9f3c1a2b",
     "stage": "clone"}

Streams, not Pub/Sub: an entry survives until TTL, so a UI that connects late
(or refreshes) replays the whole run from id 0 instead of seeing nothing.

Config:
    DUO_REDIS_URL       default redis://127.0.0.1:6379/0
    DUO_RUN_ID          set by run/main.py or the API; tags every publish
    DUO_STREAM_PREFIX   default duo:run:
    DUO_STREAM_TTL      seconds a run's stream lives, default 86400
    DUO_STREAM_MAXLEN   approximate cap per stream, default 10000
    DUO_BUS_STRICT=1    raise instead of degrading when Redis is unreachable

Telemetry never blocks a review: an unreachable bus is reported once on stderr
and events for that process are dropped (unless DUO_BUS_STRICT=1).

Usage:
    python3 engine/bus.py <run_id>     # tail one run's stream
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

DEFAULT_URL = "redis://127.0.0.1:6379/0"

_client: Any = None
_degraded = False


def _url() -> str:
    return os.environ.get("DUO_REDIS_URL", DEFAULT_URL)


def _prefix() -> str:
    return os.environ.get("DUO_STREAM_PREFIX", "duo:run:")


def _stream(run_id: str) -> str:
    if not run_id:
        raise ValueError("run_id is empty — cannot name an event stream")
    return f"{_prefix()}{run_id}"


def _connect() -> Any:
    """Lazy, process-wide connection. Raises RuntimeError if Redis is absent."""
    global _client
    if _client is not None:
        return _client
    try:
        import redis
    except ImportError as exc:
        raise RuntimeError(
            "redis package missing — install it in the interpreter running the "
            "stages (pip install redis)"
        ) from exc
    client = redis.Redis.from_url(
        _url(), decode_responses=True,
        socket_connect_timeout=2.0, socket_timeout=5.0,
    )
    client.ping()
    _client = client
    return client


def endpoint() -> str:
    """The Redis URL this process publishes to."""
    return _url()


def ping() -> None:
    """Raise if Redis is unreachable."""
    _connect().ping()


def publish(event: str, run_id: str | None = None, **fields: Any) -> str:
    """Append one event to the run's stream; returns the entry id ("" if dropped).

    `run_id` defaults to $DUO_RUN_ID. Returns "" without raising if the bus is
    down, after one warning — a UI outage must not decide whether a review
    completes. Set DUO_BUS_STRICT=1 to turn that into an exception.
    """
    global _degraded
    strict = os.environ.get("DUO_BUS_STRICT") == "1"
    if _degraded and not strict:
        return ""

    run_id = run_id or os.environ.get("DUO_RUN_ID", "")
    record = {
        "event": event,
        "ts": time.time(),
        "pid": os.getpid(),
        "run_id": run_id,
        **fields,
    }
    try:
        client = _connect()
        entry_id = client.xadd(
            _stream(run_id),
            {"data": json.dumps(record, default=str)},
            maxlen=int(os.environ.get("DUO_STREAM_MAXLEN", "10000")),
            approximate=True,
        )
        client.expire(_stream(run_id), int(os.environ.get("DUO_STREAM_TTL", "86400")))
        return entry_id
    except Exception as exc:
        if strict:
            raise
        _degraded = True
        print(
            f"bus: {type(exc).__name__}: {exc} — UI events dropped for "
            f"{os.getpid()} ({_stream(run_id or '?')} @ {_url()})",
            file=sys.stderr,
        )
        return ""


def read_events(run_id: str, last_id: str = "0-0", block_ms: int = 5000,
                count: int = 200) -> list[tuple[str, dict]]:
    """Read entries after `last_id`; returns [(entry_id, event)].

    Empty list means nothing new — the caller decides whether to keep waiting.
    `block_ms=0` blocks forever; `block_ms=None` or negative drains what exists
    and returns immediately.
    """
    client = _connect()
    key = _stream(run_id)
    if block_ms is None or block_ms < 0:
        response = client.xread({key: last_id}, count=count)
    else:
        response = client.xread({key: last_id}, count=count, block=block_ms)
    if not response:
        return []
    events: list[tuple[str, dict]] = []
    for _key, entries in response:
        for entry_id, fields in entries:
            try:
                payload = json.loads(fields["data"])
            except (KeyError, json.JSONDecodeError):
                payload = {"event": "unparsable", "raw": fields.get("data")}
            events.append((entry_id, payload))
    return events


def last_event(run_id: str) -> dict | None:
    """Most recent event in the run's stream, or None if the stream is empty."""
    client = _connect()
    entries = client.xrevrange(_stream(run_id), count=1)
    if not entries:
        return None
    _entry_id, fields = entries[0]
    try:
        return json.loads(fields["data"])
    except (KeyError, json.JSONDecodeError):
        return {"event": "unparsable", "raw": fields.get("data")}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: bus.py <run_id>", file=sys.stderr)
        return 2
    run_id = sys.argv[1]
    print(f"tailing {_stream(run_id)} @ {_url()} (ctrl-c to stop)", file=sys.stderr)
    last_id = "0-0"
    try:
        while True:
            for entry_id, event in read_events(run_id, last_id, block_ms=5000):
                last_id = entry_id
                rest = {k: v for k, v in event.items()
                        if k not in ("ts", "pid", "run_id")}
                stamp = time.strftime("%H:%M:%S",
                                      time.localtime(event.get("ts", time.time())))
                print(f"{stamp} {event.get('run_id', '?')} {event['event']} {rest}")
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
