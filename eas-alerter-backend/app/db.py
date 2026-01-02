import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signature TEXT UNIQUE,
    received_ts TEXT,
    event_code TEXT,
    headline TEXT,
    severity TEXT,
    area TEXT,
    expires_ts TEXT,
    same_header TEXT,
    raw_text TEXT,
    json_payload TEXT
);

CREATE TABLE IF NOT EXISTS alert_broadcasts (
    signature TEXT PRIMARY KEY,
    last_broadcast_ts TEXT,
    last_raw_hash TEXT
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def raw_hash(raw_text: str) -> str:
    return hashlib.sha256(raw_text.encode("utf-8")).hexdigest()


def signature_for(alert: Dict[str, Any]) -> str:
    base = (
        f"{alert.get('event_code', '')}"
        f"{alert.get('expires_ts', '')}"
        f"{alert.get('area', '')}"
        f"{alert.get('same_header', '')}"
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


class AlertStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def upsert_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        signature = signature_for(alert)
        received_ts = alert.get("received_ts") or now_iso()
        payload = json.dumps(alert)
        values = (
            signature,
            received_ts,
            alert.get("event_code"),
            alert.get("headline"),
            alert.get("severity"),
            alert.get("area"),
            alert.get("expires_ts"),
            alert.get("same_header"),
            alert.get("raw_text"),
            payload,
        )

        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id, raw_text FROM alerts WHERE signature = ?",
                (signature,),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE alerts
                    SET received_ts = ?,
                        event_code = ?,
                        headline = ?,
                        severity = ?,
                        area = ?,
                        expires_ts = ?,
                        same_header = ?,
                        raw_text = ?,
                        json_payload = ?
                    WHERE signature = ?
                    """,
                    (
                        received_ts,
                        alert.get("event_code"),
                        alert.get("headline"),
                        alert.get("severity"),
                        alert.get("area"),
                        alert.get("expires_ts"),
                        alert.get("same_header"),
                        alert.get("raw_text"),
                        payload,
                        signature,
                    ),
                )
                alert_id = existing["id"]
                raw_changed = (existing["raw_text"] or "") != (alert.get("raw_text") or "")
                return {
                    "id": alert_id,
                    "signature": signature,
                    "raw_changed": raw_changed,
                    "is_new": False,
                }

            cursor = conn.execute(
                """
                INSERT INTO alerts (
                    signature, received_ts, event_code, headline, severity, area,
                    expires_ts, same_header, raw_text, json_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            return {
                "id": cursor.lastrowid,
                "signature": signature,
                "raw_changed": True,
                "is_new": True,
            }

    def update_broadcast(self, signature: str, raw_text: str) -> None:
        timestamp = now_iso()
        hashed = raw_hash(raw_text or "")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO alert_broadcasts (signature, last_broadcast_ts, last_raw_hash)
                VALUES (?, ?, ?)
                ON CONFLICT(signature) DO UPDATE SET
                    last_broadcast_ts = excluded.last_broadcast_ts,
                    last_raw_hash = excluded.last_raw_hash
                """,
                (signature, timestamp, hashed),
            )

    def last_broadcast_info(self, signature: str) -> Optional[Dict[str, str]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT last_broadcast_ts, last_raw_hash FROM alert_broadcasts WHERE signature = ?",
                (signature,),
            ).fetchone()
            if not row:
                return None
            return {
                "last_broadcast_ts": row["last_broadcast_ts"],
                "last_raw_hash": row["last_raw_hash"],
            }

    def list_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, received_ts, event_code, headline, severity, area, expires_ts
                FROM alerts
                ORDER BY received_ts DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_alert(self, alert_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, received_ts, event_code, headline, severity, area,
                       expires_ts, same_header, raw_text, json_payload
                FROM alerts WHERE id = ?
                """,
                (alert_id,),
            ).fetchone()
            return dict(row) if row else None

    def list_recent_bbs(self, limit: int = 5) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, headline, severity, area, expires_ts
                FROM alerts
                ORDER BY received_ts DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
