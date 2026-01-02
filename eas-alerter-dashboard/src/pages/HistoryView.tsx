import { useEffect, useState } from "react";
import { fetchAlerts } from "../api";
import { AlertListItem } from "../types";
import AlertTable from "../components/AlertTable";

export default function HistoryView() {
  const [alerts, setAlerts] = useState<AlertListItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAlerts()
      .then(setAlerts)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="card">
      <h2>Alert History</h2>
      {error && <p className="note">{error}</p>}
      <AlertTable alerts={alerts} />
    </div>
  );
}
