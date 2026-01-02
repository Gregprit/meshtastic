import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass
class Settings:
    meshtastic_serial: str | None
    meshtastic_host: str | None
    meshtastic_port: int | None
    alert_channel_index: int
    dm_only: bool
    auto_broadcast: bool
    db_path: str


DEFAULT_SETTINGS_PATH = Path(__file__).resolve().parent / "settings.json"


def load_settings() -> Settings:
    env = os.environ
    meshtastic_serial = env.get("MESHTASTIC_SERIAL")
    meshtastic_host = env.get("MESHTASTIC_HOST")
    meshtastic_port = int(env["MESHTASTIC_PORT"]) if env.get("MESHTASTIC_PORT") else None
    alert_channel_index = int(env.get("ALERT_CHANNEL_INDEX", "1"))
    dm_only = env.get("DM_ONLY", "true").lower() == "true"
    auto_broadcast = env.get("AUTO_BROADCAST", "true").lower() == "true"
    db_path = env.get("DB_PATH", str(Path(__file__).resolve().parent.parent / "alerts.db"))

    if DEFAULT_SETTINGS_PATH.exists():
        payload = json.loads(DEFAULT_SETTINGS_PATH.read_text())
        meshtastic_serial = payload.get("meshtastic_serial") or meshtastic_serial
        meshtastic_host = payload.get("meshtastic_host") or meshtastic_host
        meshtastic_port = payload.get("meshtastic_port") or meshtastic_port
        alert_channel_index = payload.get("alert_channel_index", alert_channel_index)
        dm_only = payload.get("dm_only", dm_only)
        auto_broadcast = payload.get("auto_broadcast", auto_broadcast)
        db_path = payload.get("db_path", db_path)

    return Settings(
        meshtastic_serial=meshtastic_serial,
        meshtastic_host=meshtastic_host,
        meshtastic_port=meshtastic_port,
        alert_channel_index=alert_channel_index,
        dm_only=dm_only,
        auto_broadcast=auto_broadcast,
        db_path=db_path,
    )


def save_settings(settings: Settings) -> None:
    payload: Dict[str, Any] = {
        "meshtastic_serial": settings.meshtastic_serial,
        "meshtastic_host": settings.meshtastic_host,
        "meshtastic_port": settings.meshtastic_port,
        "alert_channel_index": settings.alert_channel_index,
        "dm_only": settings.dm_only,
        "auto_broadcast": settings.auto_broadcast,
        "db_path": settings.db_path,
    }
    DEFAULT_SETTINGS_PATH.write_text(json.dumps(payload, indent=2))
