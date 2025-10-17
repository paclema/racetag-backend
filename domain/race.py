from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel


def parse_iso(s: str) -> datetime:
    if s.endswith("Z"):
        s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s)


class Participant(BaseModel):
    tag_id: str
    laps: int = 0
    last_pass_time: Optional[str] = None
    finish_time: Optional[str] = None
    finished: bool = False
    total_time_ms: Optional[int] = None


class RaceState:
    def __init__(self, total_laps: int = 20) -> None:
        self.total_laps = total_laps
        self.start_time = datetime.now(timezone.utc)
        self.participants: Dict[str, Participant] = {}

    def add_lap(self, tag_id: str, pass_time_iso: str) -> Participant:
        p = self.participants.get(tag_id)
        if p is None:
            p = Participant(tag_id=tag_id)
            self.participants[tag_id] = p
        p.laps += 1
        p.last_pass_time = pass_time_iso
        if not p.finished and p.laps >= self.total_laps:
            p.finished = True
            p.finish_time = pass_time_iso
        t = parse_iso(p.finish_time or p.last_pass_time) if (p.finish_time or p.last_pass_time) else None
        if t is not None:
            p.total_time_ms = int((t - self.start_time).total_seconds() * 1000)
        return p

    def standings(self) -> List[Participant]:
        def key(p: Participant) -> Tuple[int, int, int]:
            finished_flag = 1 if p.finished else 0
            ref = p.finish_time or p.last_pass_time
            tt = parse_iso(ref).timestamp() if ref else float("inf")
            tt_i = int(tt * 1000)
            return (finished_flag, p.laps, -tt_i)

        arr = list(self.participants.values())
        arr.sort(key=key, reverse=True)
        return arr
