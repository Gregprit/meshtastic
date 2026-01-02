import { useEffect, useState } from "react";
import AlertTable from "../components/AlertTable";
import { fetchAlerts, fetchAlert } from "../api";
import { AlertDetails, AlertListItem } from "../types";

export default function Dashboard() {
  const [alerts, setAlerts] = useState<AlertListItem[]>([]);
  const [selected, setSelected] = useState<AlertDetails | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAlerts()
      .then(setAlerts)
      .catch((err) => setError(err.message));
  }, []);

  const handleSelect = (alert: AlertListItem) => {
    fetchAlert(alert.id)
      .then(setSelected)
      .catch((err) => setError(err.message));
  };

  return (
    <div>
      <section className="card">
        <h2>Recent Alerts</h2>
        {error && <p className="note">{error}</p>}
        <AlertTable alerts={alerts} onSelect={handleSelect} />
      </section>
      <section className="card">
        <h2>Selected Bulletin</h2>
        {selected ? (
          <div>
            <p>
              <strong>BBS #{selected.id}</strong> — {selected.headline}
            </p>
            <p className="note">
              Severity: {selected.severity} | Area: {selected.area} | Expires: {selected.expires_ts}
            </p>
            <pre>{selected.raw_text}</pre>
          </div>
        ) : (
          <p className="note">Select an alert to view the full bulletin text.</p>
        )}
      </section>
    </div>
  );
}
