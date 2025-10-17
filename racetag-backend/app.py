from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse

from domain.race import RaceState
from models_api import EventType, TagEventDTO, ParticipantDTO


app = FastAPI(title="Racetag Backend")


# Global single race for MVP
race = RaceState(total_laps=20)

# Debug/event store
events: List[TagEventDTO] = []

# SSE subscribers: list of buffers
subscribers: List[List[Dict[str, Any]]] = []


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@app.post("/events/tag/batch")
def post_events_batch(batch: List[TagEventDTO]):
    if not batch:
        return JSONResponse({"accepted": 0})
    accepted = 0
    for ev in batch:
        events.append(ev)
        accepted += 1
        # Update race on ARRIVE (simple rule for MVP)
        if ev.event_type == EventType.arrive:
            # Use event timestamp as the pass time
            p = race.add_lap(ev.tag_id, ev.timestamp)
            # Broadcast lap update
            lap_payload = {
                "type": "lap",
                "tag_id": p.tag_id,
                "laps": p.laps,
                "finished": p.finished,
                "last_pass_time": p.last_pass_time,
            }
            for q in list(subscribers):
                try:
                    q.append(lap_payload)
                except Exception:
                    pass
            # Optionally broadcast new standings snapshot (lightweight)
            table = [s.model_dump() for s in race.standings()]
            standings_payload = {"type": "standings", "items": table}
            for q in list(subscribers):
                try:
                    q.append(standings_payload)
                except Exception:
                    pass
    return {"accepted": accepted}


@app.get("/classification")
def get_classification():
    # Current classification ordered by race rules
    items = [ParticipantDTO(**p.model_dump()).model_dump() for p in race.standings()]
    return {"count": len(items), "standings": items}


@app.get("/race")
def get_race():
    return {
        "total_laps": race.total_laps,
        "start_time": race.start_time.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "participants": [ParticipantDTO(**p.model_dump()).model_dump() for p in race.participants.values()],
    }


@app.get("/stream")
def stream_events():
    # Simple Server-Sent Events stream
    client_buf: List[Dict[str, Any]] = []
    subscribers.append(client_buf)

    def iterator():
        try:
            last_idx = 0
            while True:
                if last_idx < len(client_buf):
                    item = client_buf[last_idx]
                    last_idx += 1
                    data = item
                    yield f"data: {data}\n\n"
                else:
                    # heartbeat
                    yield f": keepalive {_now_iso()}\n\n"
                    import time as _t

                    _t.sleep(1)
        finally:
            try:
                subscribers.remove(client_buf)
            except ValueError:
                pass

    return StreamingResponse(iterator(), media_type="text/event-stream")
