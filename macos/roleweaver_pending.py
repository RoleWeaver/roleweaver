"""Durable summary batches. Memory's completion ID is authoritative."""
import copy
import json
from pathlib import Path
import uuid
import threading
import roleweaver_storage as storage

_processing_locks = {}


class SummaryJournal:
    def __init__(self, path):
        self.path = Path(path)
        with storage.LOCK:
            self.processing_lock = _processing_locks.setdefault(str(self.path.resolve()), threading.Lock())
        self._read()  # Fail explicitly; never reset damaged pending work.

    def _read(self):
        if not self.path.exists():
            return {"version": 1, "pending": [], "active": None}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if (not isinstance(data, dict) or data.get("version") != 1
                or not isinstance(data.get("pending"), list)
                or any(not isinstance(e, dict) for e in data["pending"])):
            raise ValueError(f"Invalid summary journal: {self.path}")
        active = data.get("active")
        if active is not None and (not isinstance(active, dict)
                or not isinstance(active.get("id"), str)
                or not isinstance(active.get("events"), list)
                or any(not isinstance(e, dict) for e in active["events"])
                or not (active.get("response") is None or isinstance(active["response"], dict))):
            raise ValueError(f"Invalid active summary batch: {self.path}")
        return data

    def _write(self, data):
        storage.atomic_write_text(self.path, json.dumps(data, ensure_ascii=False))

    @storage.synchronized
    def append(self, event):
        data = self._read()
        data["pending"].append(copy.deepcopy(event))
        self._write(data)

    @storage.synchronized
    def events(self):
        data = self._read()
        return (data["active"]["events"] if data["active"] else []) + data["pending"]

    @storage.synchronized
    def begin(self, completed_id=None):
        data = self._read()
        if data["active"] and data["active"]["id"] == completed_id:
            data["active"] = None
        if data["active"] is None and data["pending"]:
            data["active"] = {"id": uuid.uuid4().hex, "events": data["pending"], "response": None}
            data["pending"] = []
        self._write(data)
        return data["active"]

    @storage.synchronized
    def cache_response(self, batch_id, response):
        if not isinstance(response, dict):
            raise ValueError("Summary response must be a JSON object")
        data = self._read()
        if not data["active"] or data["active"]["id"] != batch_id:
            raise ValueError("Summary batch changed")
        data["active"]["response"] = response
        self._write(data)

    @storage.synchronized
    def acknowledge(self, batch_id):
        data = self._read()
        if data["active"] and data["active"]["id"] == batch_id:
            data["active"] = None
            self._write(data)
