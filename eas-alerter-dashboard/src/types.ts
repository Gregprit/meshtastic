export interface AlertListItem {
  id: number;
  received_ts: string;
  event_code?: string;
  headline?: string;
  severity?: string;
  area?: string;
  expires_ts?: string;
}

export interface AlertDetails extends AlertListItem {
  same_header?: string;
  raw_text?: string;
}

export interface SettingsPayload {
  meshtastic_serial?: string | null;
  meshtastic_host?: string | null;
  meshtastic_port?: number | null;
  alert_channel_index?: number | null;
  dm_only?: boolean | null;
  auto_broadcast?: boolean | null;
  db_path?: string | null;
}
