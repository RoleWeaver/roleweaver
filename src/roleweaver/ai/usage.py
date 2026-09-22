"""Content-free local AI usage and estimated-cost records."""

from __future__ import annotations

import sqlite3
import threading
import time
from contextlib import closing
from pathlib import Path
from typing import Any

from .contracts import AIRequest, AIResult

WINDOWS = {"session": None, "24h": 86400, "7d": 604800, "30d": 2592000}


class UsageStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        with self.lock, closing(sqlite3.connect(self.path)) as database, database:
            database.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS requests (
                  id INTEGER PRIMARY KEY,
                  created REAL NOT NULL,
                  session TEXT NOT NULL,
                  provider TEXT NOT NULL,
                  model TEXT NOT NULL,
                  purpose TEXT NOT NULL,
                  status TEXT NOT NULL,
                  provider_calls INTEGER NOT NULL DEFAULT 1,
                  duration_seconds REAL NOT NULL,
                  input_tokens INTEGER,
                  output_tokens INTEGER,
                  total_tokens INTEGER,
                  usage_source TEXT NOT NULL,
                  guardrail_action TEXT NOT NULL,
                  error_type TEXT NOT NULL,
                  estimated_cost REAL
                );
                CREATE INDEX IF NOT EXISTS usage_created ON requests(created);
                CREATE TABLE IF NOT EXISTS guardrail_events (
                  id INTEGER PRIMARY KEY,
                  created REAL NOT NULL,
                  session TEXT NOT NULL,
                  purpose TEXT NOT NULL,
                  direction TEXT NOT NULL,
                  category TEXT NOT NULL,
                  action TEXT NOT NULL,
                  backend TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS guardrail_created ON guardrail_events(created);
                """
            )
            columns = {
                row[1] for row in database.execute("PRAGMA table_info(requests)")
            }
            if "provider_calls" not in columns:
                database.execute(
                    "ALTER TABLE requests ADD COLUMN provider_calls INTEGER NOT NULL DEFAULT 1"
                )

    def record_guardrail(
        self,
        *,
        session: str,
        purpose: str,
        direction: str,
        categories: tuple[str, ...],
        action: str,
        backend: str,
        category_actions: tuple[tuple[str, str], ...] = (),
    ) -> None:
        """Record policy metadata without storing the triggering dialogue."""

        if action == "pass" or not categories:
            return
        created = time.time()
        actions = dict(category_actions)
        rows = [
            (created, session, purpose, direction, category, actions.get(category, action), backend)
            for category in categories
        ]
        with self.lock, closing(sqlite3.connect(self.path)) as database, database:
            database.executemany(
                "INSERT INTO guardrail_events(created,session,purpose,direction,category,"
                "action,backend) VALUES (?,?,?,?,?,?,?)",
                rows,
            )
            database.execute(
                "DELETE FROM guardrail_events WHERE created < ?",
                (created - 2592000,),
            )

    def record(
        self,
        request: AIRequest,
        *,
        session: str,
        result: AIResult | None = None,
        status: str = "ok",
        duration_seconds: float = 0.0,
        guardrail_action: str = "pass",
        error: Exception | None = None,
        input_rate: float | None = None,
        output_rate: float | None = None,
        provider: str = "",
        model: str = "",
        provider_calls: int = 1,
    ) -> None:
        usage = result.usage if result else None
        input_tokens = usage.input_tokens if usage else None
        output_tokens = usage.output_tokens if usage else None
        total_tokens = usage.total_tokens if usage else None
        cost = None
        if input_tokens is not None and output_tokens is not None:
            if input_rate is not None and output_rate is not None:
                cost = (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000
        row = (
            time.time(),
            session,
            result.provider if result else provider,
            result.model if result else model,
            request.purpose.value,
            status,
            max(0, int(provider_calls)),
            result.duration_seconds if result else max(0.0, duration_seconds),
            input_tokens,
            output_tokens,
            total_tokens,
            usage.source if usage else "unavailable",
            guardrail_action,
            type(error).__name__ if error else "",
            cost,
        )
        with self.lock, closing(sqlite3.connect(self.path)) as database, database:
            database.execute(
                "INSERT INTO requests(created,session,provider,model,purpose,status,provider_calls,"
                "duration_seconds,input_tokens,output_tokens,total_tokens,usage_source,"
                "guardrail_action,error_type,estimated_cost) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                row,
            )
            database.execute("DELETE FROM requests WHERE created < ?", (time.time() - 2592000,))

    def report(self, window: str = "24h", session: str = "") -> dict[str, Any]:
        if window not in WINDOWS:
            raise ValueError("Unknown usage window")
        if window == "session" and not session:
            return _summarize([])
        clauses = []
        arguments: list[Any] = []
        if WINDOWS[window] is not None:
            clauses.append("created >= ?")
            arguments.append(time.time() - WINDOWS[window])
        if window == "session":
            clauses.append("session = ?")
            arguments.append(session)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.lock, closing(sqlite3.connect(self.path)) as database:
            database.row_factory = sqlite3.Row
            statement = "SELECT * FROM requests" + where + " ORDER BY created"
            rows = [dict(row) for row in database.execute(statement, arguments)]
        return _summarize(rows)

    def guardrail_events(
        self,
        window: str = "24h",
        session: str = "",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if window not in WINDOWS:
            raise ValueError("Unknown usage window")
        if window == "session" and not session:
            return []
        clauses = []
        arguments: list[Any] = []
        if WINDOWS[window] is not None:
            clauses.append("created >= ?")
            arguments.append(time.time() - WINDOWS[window])
        if window == "session":
            clauses.append("session = ?")
            arguments.append(session)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        arguments.append(max(1, min(int(limit), 1000)))
        statement = (
            "SELECT created,purpose,direction,category,action,backend "
            "FROM guardrail_events" + where + " ORDER BY created DESC LIMIT ?"
        )
        with self.lock, closing(sqlite3.connect(self.path)) as database:
            database.row_factory = sqlite3.Row
            return [dict(row) for row in database.execute(statement, arguments)]


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate content-free request rows for the usage UI."""

    known = [row for row in rows if row["total_tokens"] is not None]
    priced = [row for row in rows if row["estimated_cost"] is not None]
    by_purpose: dict[str, dict[str, int | float]] = {}
    for row in rows:
        group = by_purpose.setdefault(
            row["purpose"],
            {
                "requests": 0,
                "provider_calls": 0,
                "tokens": 0,
                "estimated_cost": 0.0,
                "priced_requests": 0,
            },
        )
        group["requests"] += 1
        group["provider_calls"] += row["provider_calls"]
        group["tokens"] += row["total_tokens"] or 0
        if row["estimated_cost"] is not None:
            group["estimated_cost"] += row["estimated_cost"]
            group["priced_requests"] += 1
    return {
        "requests": len(rows),
        "provider_calls": sum(row["provider_calls"] for row in rows),
        "errors": sum(row["status"] == "error" for row in rows),
        "blocked": sum(row["guardrail_action"] == "block" for row in rows),
        "input_tokens": sum(row["input_tokens"] or 0 for row in known),
        "output_tokens": sum(row["output_tokens"] or 0 for row in known),
        "total_tokens": sum(row["total_tokens"] or 0 for row in known),
        "token_requests": len(known),
        "unknown_token_requests": len(rows) - len(known),
        "estimated_cost": sum(row["estimated_cost"] or 0 for row in priced),
        "priced_requests": len(priced),
        "by_purpose": by_purpose,
        "rows": rows,
    }
