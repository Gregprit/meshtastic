from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .db import AlertStore
from .meshtastic_client import MeshtasticClient
from .settings import Settings, load_settings, save_settings


class AlertIngest(BaseModel):
    event_code: str
    headline: str
    severity: str
    area: str
    expires_ts: str
    same_header: str
    raw_text: str
    received_ts: Optional[str] = None


class AlertListItem(BaseModel):
    id: int
    received_ts: str
    event_code: Optional[str]
    headline: Optional[str]
    severity: Optional[str]
    area: Optional[str]
    expires_ts: Optional[str]


app = FastAPI()
settings = load_settings()
store = AlertStore(settings.db_path)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SettingsModel(BaseModel):
    meshtastic_serial: Optional[str] = None
    meshtastic_host: Optional[str] = None
    meshtastic_port: Optional[int] = None
    alert_channel_index: Optional[int] = None
    dm_only: Optional[bool] = None
    auto_broadcast: Optional[bool] = None
    db_path: Optional[str] = None


meshtastic_client: Optional[MeshtasticClient] = None


def within_broadcast_window(last_broadcast: Optional[str], minutes: int = 10) -> bool:
    if not last_broadcast:
        return False
    try:
        last_dt = datetime.fromisoformat(last_broadcast)
    except ValueError:
        return False
    return datetime.now(timezone.utc) - last_dt <= timedelta(minutes=minutes)


def build_waiting_message(alert: Dict[str, Any], alert_id: int) -> str:
    headline = alert.get("headline") or "Alert"
    area = alert.get("area") or "area"
    expires_ts = alert.get("expires_ts") or ""
    base = f"NWS ALERT WAITING: {headline} for {area}. Expires {expires_ts}. BBS #{alert_id}."
    tail = " DM 'GET {0}'".format(alert_id)
    message = f"{base}{tail}"
    if len(message) <= 140:
        return message
    trimmed_headline = (headline[:40] + "...") if len(headline) > 43 else headline
    trimmed_area = (area[:20] + "...") if len(area) > 23 else area
    base = f"ALERT WAITING: {trimmed_headline} for {trimmed_area}. Expires {expires_ts}. BBS #{alert_id}."
    message = f"{base}{tail}"
    return message[:180]


def parse_command(text: str) -> Dict[str, Any]:
    parts = text.strip().split()
    if not parts:
        return {"command": ""}
    command = parts[0].upper()
    if command == "GET" and len(parts) >= 2:
        return {
            "command": "GET",
            "id": parts[1],
            "summary": len(parts) >= 3 and parts[2].upper() == "SUMMARY",
        }
    return {"command": command}


def handle_meshtastic_text(text: str, channel: Optional[int], sender: Optional[str]) -> None:
    if not sender:
        return
    if channel is not None and channel != settings.alert_channel_index:
        return
    command = parse_command(text)
    mode_dm_only = settings.dm_only

    def reply(message: str) -> None:
        if not meshtastic_client:
            return
        if mode_dm_only or channel is None:
            meshtastic_client.send_chunked(message, sender)
        else:
            meshtastic_client.send_chunked_channel(message)

    if command["command"] == "HELP":
        reply("Commands: ALERTS, GET <id>, GET <id> SUMMARY")
        return

    if command["command"] == "ALERTS":
        items = store.list_recent_bbs()
        if not items:
            reply("No alerts on the BBS.")
            return
        lines = [
            f"BBS #{item['id']}: {item.get('headline','')} ({item.get('severity','')}) {item.get('area','')} Expires {item.get('expires_ts','')}"
            for item in items
        ]
        reply("\n".join(lines))
        return

    if command["command"] == "GET":
        try:
            alert_id = int(command.get("id", "0"))
        except ValueError:
            reply("Invalid bulletin id.")
            return
        alert = store.get_alert(alert_id)
        if not alert:
            reply("Bulletin not found.")
            return
        if command.get("summary"):
            summary = (
                f"BBS #{alert['id']}: {alert.get('headline','')} ({alert.get('severity','')}) "
                f"{alert.get('area','')} Expires {alert.get('expires_ts','')}"
            )
            reply(summary)
        else:
            reply(alert.get("raw_text") or "(empty bulletin)")
        return


def start_meshtastic() -> None:
    global meshtastic_client
    meshtastic_client = MeshtasticClient(
        serial_path=settings.meshtastic_serial,
        host=settings.meshtastic_host,
        port=settings.meshtastic_port,
        alert_channel_index=settings.alert_channel_index,
        on_text=handle_meshtastic_text,
    )
    meshtastic_client.start()


@app.on_event("startup")
def on_startup() -> None:
    start_meshtastic()


@app.post("/api/alerts/ingest")
def ingest_alert(alert: AlertIngest) -> Dict[str, Any]:
    payload = alert.dict()
    result = store.upsert_alert(payload)
    signature = result["signature"]
    alert_id = result["id"]
    broadcast_info = store.last_broadcast_info(signature)
    raw_changed = result["raw_changed"]
    should_broadcast = result["is_new"]

    if raw_changed:
        if not broadcast_info:
            should_broadcast = True
        elif not within_broadcast_window(broadcast_info.get("last_broadcast_ts")):
            should_broadcast = True

    if settings.auto_broadcast and should_broadcast and meshtastic_client:
        message = build_waiting_message(payload, alert_id)
        meshtastic_client.send_channel(message)
        store.update_broadcast(signature, payload.get("raw_text", ""))
    elif settings.auto_broadcast and raw_changed and not broadcast_info:
        store.update_broadcast(signature, payload.get("raw_text", ""))

    return {"id": alert_id, "signature": signature}


@app.get("/api/alerts", response_model=list[AlertListItem])
def list_alerts() -> list[Dict[str, Any]]:
    return store.list_alerts()


@app.get("/api/alerts/{alert_id}")
def get_alert(alert_id: int) -> Dict[str, Any]:
    alert = store.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.get("/api/settings")
def get_settings() -> Dict[str, Any]:
    return asdict(settings)


@app.post("/api/settings")
def update_settings(payload: SettingsModel) -> Dict[str, Any]:
    global settings
    updated = Settings(
        meshtastic_serial=payload.meshtastic_serial or settings.meshtastic_serial,
        meshtastic_host=payload.meshtastic_host or settings.meshtastic_host,
        meshtastic_port=payload.meshtastic_port or settings.meshtastic_port,
        alert_channel_index=payload.alert_channel_index or settings.alert_channel_index,
        dm_only=payload.dm_only if payload.dm_only is not None else settings.dm_only,
        auto_broadcast=payload.auto_broadcast
        if payload.auto_broadcast is not None
        else settings.auto_broadcast,
        db_path=payload.db_path or settings.db_path,
    )
    settings = updated
    save_settings(settings)
    return asdict(settings)
