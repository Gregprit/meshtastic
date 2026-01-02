import { useEffect, useState } from "react";
import { fetchAlert, fetchAlerts } from "../api";
import { AlertDetails, AlertListItem } from "../types";

export default function BBSViewer() {
  const [alerts, setAlerts] = useState<AlertListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selected, setSelected] = useState<AlertDetails | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAlerts()
      .then(setAlerts)
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selectedId) {
      return;
    }
    fetchAlert(selectedId)
      .then(setSelected)
      .catch((err) => setError(err.message));
  }, [selectedId]);

  return (
    <div className="card">
      <h2>BBS Viewer</h2>
      {error && <p className="note">{error}</p>}
      <label htmlFor="bbs-select">Select bulletin</label>
      <select
        id="bbs-select"
        value={selectedId ?? ""}
        onChange={(event) => setSelectedId(Number(event.target.value))}
      >
        <option value="" disabled>
          Choose a bulletin
        </option>
        {alerts.map((alert) => (
          <option key={alert.id} value={alert.id}>
            #{alert.id} — {alert.headline}
          </option>
        ))}
      </select>
      {selected && (
        <div style={{ marginTop: "1rem" }}>
          <p>
            <strong>BBS #{selected.id}</strong> — {selected.headline}
          </p>
          <pre>{selected.raw_text}</pre>
        </div>
      )}
    </div>
  );
}
