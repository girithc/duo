"""Duo HTTP API: start a review run, poll it, stream its events.

    POST /runs                    {"target": "owner/repo", "pr": 123}
    GET  /runs/{run_id}           status snapshot
    GET  /runs/{run_id}/events    Server-Sent Events, replayable via Last-Event-ID
    GET  /health                  Redis reachability

A run is a detached `run/main.py` process whose stdout/stderr go to
runtime/<run_id>.log. Progress arrives through the Redis Stream that
engine/bus.py writes to, so the SSE endpoint can replay a finished run from
id 0 — a UI that connects late or refreshes still sees everything.

Run:
    uvicorn app.api.main:app --port 8000
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Literal

ROOT = Path(__file__).resolve().parents[2]
RUN_DIR = ROOT / "runtime"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "run"))
sys.path.insert(0, str(ROOT / "engine"))

import bus  # noqa: E402
from clone import parse_target  # noqa: E402

app = FastAPI(title="Duo", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

_runs: dict[str, dict] = {}
_lock = threading.Lock()
_start_lock = threading.Lock()


class RunRequest(BaseModel):
    target: str
    pr: int | str | None = None
    stop_after: Literal["curate", "write", "sandbox"] | None = None


def _record(run_id: str) -> dict | None:
    with _lock:
        return dict(_runs[run_id]) if run_id in _runs else None


def _update(run_id: str, **fields) -> None:
    with _lock:
        if run_id in _runs:
            _runs[run_id].update(fields)


def _watch(run_id: str, proc: subprocess.Popen, log) -> None:
    """Reap the child and record how it ended."""
    code = proc.wait()
    log.close()
    _update(run_id,
            status="completed" if code == 0 else "failed",
            exit_code=code,
            finished_at=time.time())


@app.get("/health")
def health() -> dict:
    try:
        bus.ping()
        return {"redis": "ok", "url": bus.endpoint()}
    except Exception as exc:
        return {"redis": "unreachable", "url": bus.endpoint(),
                "error": f"{type(exc).__name__}: {exc}"}


@app.post("/runs", status_code=202)
def start_run(request: RunRequest) -> dict:
    try:
        owner_repo, pr_number = parse_target(request.target, request.pr)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # The stages still use shared on-disk paths. Serialize the complete start
    # transaction so two requests cannot both pass the active-run check.
    with _start_lock:
        with _lock:
            active = next(
                (dict(record) for record in _runs.values()
                 if record["status"] == "running"),
                None,
            )
        if active is not None:
            raise HTTPException(
                status_code=409,
                detail=(f"run {active['run_id']} is already active; "
                        "wait for it to finish"),
            )

        try:
            bus.ping()
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"event bus unavailable: {type(exc).__name__}: {exc}",
            ) from exc

        run_id = uuid.uuid4().hex[:12]
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        log_path = RUN_DIR / f"{run_id}.log"
        log = log_path.open("ab")
        env = dict(os.environ, DUO_RUN_ID=run_id, DUO_BUS_STRICT="1")
        command = [
            sys.executable, str(ROOT / "run" / "main.py"),
            owner_repo, str(pr_number),
        ]
        if request.stop_after is not None:
            command.extend(["--stop-after", request.stop_after])
        try:
            proc = subprocess.Popen(
                command,
                cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
            )
        except Exception:
            log.close()
            raise

        with _lock:
            _runs[run_id] = {
                "run_id": run_id,
                "repo": owner_repo,
                "pr": pr_number,
                "status": "running",
                "started_at": time.time(),
                "finished_at": None,
                "exit_code": None,
                "pid": proc.pid,
                "log": str(log_path),
            }
        watcher = threading.Thread(
            target=_watch, args=(run_id, proc, log), daemon=True,
        )
        try:
            watcher.start()
        except Exception:
            # Never leave an unwatchable "running" record holding the gate.
            if proc.poll() is None:
                proc.kill()
            code = proc.wait()
            log.close()
            _update(run_id, status="failed", exit_code=code,
                    finished_at=time.time())
            raise

    return {"run_id": run_id, "status": "running",
            "events": f"/runs/{run_id}/events"}


@app.get("/runs/{run_id}")
def run_status(run_id: str) -> dict:
    record = _record(run_id)
    if record is not None:
        return record

    # Unknown to this process (API restarted?): rebuild from the stream.
    try:
        last = bus.last_event(run_id)
    except Exception as exc:
        raise HTTPException(status_code=503,
                            detail=f"event bus unavailable: {exc}") from exc
    if last is None:
        raise HTTPException(status_code=404, detail=f"unknown run {run_id}")
    finished = last.get("event") == "run_end"
    return {
        "run_id": run_id,
        "status": "completed" if finished else "running",
        "decision": last.get("decision") if finished else None,
        "last_event": last.get("event"),
        "started_at": None,
        "finished_at": last.get("ts") if finished else None,
        "exit_code": None,
        "log": None,
        "recovered_from_stream": True,
    }


@app.get("/runs/{run_id}/events")
async def run_events(run_id: str, request: Request,
                     from_id: str = "0-0") -> StreamingResponse:
    """SSE stream of one run. `Last-Event-ID` (or ?from_id=) resumes."""
    last_id = request.headers.get("last-event-id") or from_id

    async def generate():
        nonlocal last_id
        while True:
            try:
                batch = await asyncio.to_thread(
                    bus.read_events, run_id, last_id, 1000, 200
                )
            except Exception as exc:
                payload = {"event": "bus_error",
                           "error": f"{type(exc).__name__}: {exc}"}
                yield f"event: bus_error\ndata: {json.dumps(payload)}\n\n"
                return

            if not batch:
                if await request.is_disconnected():
                    return
                yield ": keep-alive\n\n"
                continue

            for entry_id, payload in batch:
                last_id = entry_id
                yield f"id: {entry_id}\ndata: {json.dumps(payload)}\n\n"
                if payload.get("event") == "run_end":
                    return

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                 "Connection": "keep-alive"},
    )
