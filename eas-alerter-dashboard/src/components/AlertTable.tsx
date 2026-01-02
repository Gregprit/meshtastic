import { AlertListItem } from "../types";

interface AlertTableProps {
  alerts: AlertListItem[];
  onSelect?: (alert: AlertListItem) => void;
}

export default function AlertTable({ alerts, onSelect }: AlertTableProps) {
  return (
    <table className="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Headline</th>
          <th>Severity</th>
          <th>Area</th>
          <th>Received</th>
          <th>Expires</th>
        </tr>
      </thead>
      <tbody>
        {alerts.map((alert) => (
          <tr key={alert.id} onClick={() => onSelect?.(alert)}>
            <td>
              <span className="badge">#{alert.id}</span>
            </td>
            <td>{alert.headline}</td>
            <td>{alert.severity}</td>
            <td>{alert.area}</td>
            <td>{new Date(alert.received_ts).toLocaleString()}</td>
            <td>{alert.expires_ts}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
