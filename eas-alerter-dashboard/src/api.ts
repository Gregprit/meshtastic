import { AlertDetails, AlertListItem, SettingsPayload } from "./types";

const baseUrl = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function fetchAlerts(): Promise<AlertListItem[]> {
  const response = await fetch(`${baseUrl}/api/alerts`);
  if (!response.ok) {
    throw new Error("Failed to fetch alerts");
  }
  return response.json();
}

export async function fetchAlert(id: number): Promise<AlertDetails> {
  const response = await fetch(`${baseUrl}/api/alerts/${id}`);
  if (!response.ok) {
    throw new Error("Failed to fetch alert");
  }
  return response.json();
}

export async function fetchSettings(): Promise<SettingsPayload> {
  const response = await fetch(`${baseUrl}/api/settings`);
  if (!response.ok) {
    throw new Error("Failed to fetch settings");
  }
  return response.json();
}

export async function saveSettings(payload: SettingsPayload): Promise<SettingsPayload> {
  const response = await fetch(`${baseUrl}/api/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to save settings");
  }
  return response.json();
}
