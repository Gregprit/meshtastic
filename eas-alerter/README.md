# Meshtastic SAME/EAS Alerter (BBS Mode)

This setup ingests SAME/EAS alerts, stores the full text in SQLite, and only broadcasts a short bulletin notice on a dedicated Meshtastic alert channel. Users can request full bulletins via DM or on-channel commands.

## Components

- **Backend**: `../eas-alerter-backend` (FastAPI + SQLite + Meshtastic client)
- **Dashboard**: `../eas-alerter-dashboard` (Vite + React)

## Raspberry Pi 3B/4 Setup

Install prerequisites:

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip nodejs npm
```

> For Node.js 18+ on Raspberry Pi, consider installing from NodeSource if your distro ships an older version.

## Backend: Install & Run

```bash
cd /workspace/meshtastic/eas-alerter-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
export MESHTASTIC_SERIAL=/dev/ttyUSB0   # or omit for TCP
export MESHTASTIC_HOST=192.168.1.50     # optional
export MESHTASTIC_PORT=4403             # optional
export ALERT_CHANNEL_INDEX=1
export DM_ONLY=true
export AUTO_BROADCAST=true
export DB_PATH=/workspace/meshtastic/eas-alerter-backend/alerts.db

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Optional: Systemd service (Pi)

```bash
sudo cp /workspace/meshtastic/eas-alerter/systemd/meshtastic-eas-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now meshtastic-eas-backend.service
```

## Dashboard: Install & Run

```bash
cd /workspace/meshtastic/eas-alerter-dashboard
npm install
npm run build
npm run preview -- --host 0.0.0.0 --port 5173
```

Open <http://<pi-ip>:5173>.

### Optional: Systemd service (Pi)

```bash
sudo cp /workspace/meshtastic/eas-alerter/systemd/meshtastic-eas-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now meshtastic-eas-dashboard.service
```

## Settings

The backend uses environment variables on startup, and a local `settings.json` (created when saved via the dashboard). Supported values:

- `MESHTASTIC_SERIAL` (e.g. `/dev/ttyUSB0`) **or** `MESHTASTIC_HOST` + `MESHTASTIC_PORT`
- `ALERT_CHANNEL_INDEX`
- `DM_ONLY` (default `true`)
- `AUTO_BROADCAST` (default `true`)
- `DB_PATH`

## Ingest API (test without RTL-SDR)

Sample alert payload:

```json
{
  "event_code": "TOR",
  "headline": "Tornado Warning",
  "severity": "Extreme",
  "area": "Travis County",
  "expires_ts": "2024-06-01T22:30:00Z",
  "same_header": "ZCZC-WXR-TOR-048453+0030-1532230-KTXW/NWS-",
  "raw_text": "TORNADO WARNING\n...full text..."
}
```

Send it to the backend:

```bash
curl -X POST http://localhost:8000/api/alerts/ingest \
  -H "Content-Type: application/json" \
  -d @sample-alert.json
```

### Adapter for JSON line output

If your decoder emits one JSON alert per line to stdout, pipe it into the adapter:

```bash
python -m app.ingest_adapter http://localhost:8000/api/alerts/ingest < alerts.jsonl
```

## Meshtastic Command Reference

Send commands to the **dedicated alert channel** or via DM. By default responses are sent via DM only.

- `ALERTS` — list last 5 bulletin IDs with headline + expires
- `GET <id>` — send full bulletin text
- `GET <id> SUMMARY` — send short summary
- `HELP` — usage help

## Acceptance Tests

- Posting the same alert JSON multiple times results in **one** bulletin id and **one** broadcast (unless the content changes and the last broadcast was > 10 minutes ago).
- New alerts create new bulletin IDs and broadcast a short notice to the alert channel.
- `ALERTS` returns a list.
- `GET <id>` returns the full alert in chunks over DM (default).
- Main channel remains quiet; alert traffic stays on the dedicated alert channel and DMs.
