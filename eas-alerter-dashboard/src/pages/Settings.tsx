import { useEffect, useState } from "react";
import { fetchSettings, saveSettings } from "../api";
import { SettingsPayload } from "../types";

export default function Settings() {
  const [form, setForm] = useState<SettingsPayload>({});
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings()
      .then((data) => setForm(data))
      .catch((err) => setStatus(err.message));
  }, []);

  const updateField = (field: keyof SettingsPayload, value: string | number | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const saved = await saveSettings(form);
      setForm(saved);
      setStatus("Settings saved.");
    } catch (error) {
      setStatus((error as Error).message);
    }
  };

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>Settings</h2>
      {status && <p className="note">{status}</p>}
      <div className="form-grid">
        <div>
          <label htmlFor="serial">Meshtastic Serial Path</label>
          <input
            id="serial"
            type="text"
            value={form.meshtastic_serial ?? ""}
            onChange={(event) => updateField("meshtastic_serial", event.target.value)}
            placeholder="/dev/ttyUSB0"
          />
        </div>
        <div>
          <label htmlFor="host">Meshtastic Host</label>
          <input
            id="host"
            type="text"
            value={form.meshtastic_host ?? ""}
            onChange={(event) => updateField("meshtastic_host", event.target.value)}
            placeholder="192.168.1.50"
          />
        </div>
        <div>
          <label htmlFor="port">Meshtastic Port</label>
          <input
            id="port"
            type="number"
            value={form.meshtastic_port ?? ""}
            onChange={(event) => updateField("meshtastic_port", Number(event.target.value))}
            placeholder="4403"
          />
        </div>
        <div>
          <label htmlFor="channel">Alert Channel Index</label>
          <input
            id="channel"
            type="number"
            value={form.alert_channel_index ?? 1}
            onChange={(event) => updateField("alert_channel_index", Number(event.target.value))}
          />
        </div>
        <div>
          <label htmlFor="dm-only">Replies via DM Only</label>
          <select
            id="dm-only"
            value={form.dm_only ? "true" : "false"}
            onChange={(event) => updateField("dm_only", event.target.value === "true")}
          >
            <option value="true">True (default)</option>
            <option value="false">False (reply in channel)</option>
          </select>
        </div>
        <div>
          <label htmlFor="auto-broadcast">Auto Broadcast Enabled</label>
          <select
            id="auto-broadcast"
            value={form.auto_broadcast ? "true" : "false"}
            onChange={(event) => updateField("auto_broadcast", event.target.value === "true")}
          >
            <option value="true">Enabled</option>
            <option value="false">Disabled</option>
          </select>
        </div>
        <div>
          <label htmlFor="db-path">Database Path</label>
          <input
            id="db-path"
            type="text"
            value={form.db_path ?? ""}
            onChange={(event) => updateField("db_path", event.target.value)}
          />
        </div>
      </div>
      <div style={{ marginTop: "1.5rem" }}>
        <button type="submit">Save Settings</button>
      </div>
    </form>
  );
}
