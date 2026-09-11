export const ALERT_LEVELS = ["info", "warning", "critical"] as const;
export type AlertLevel = (typeof ALERT_LEVELS)[number];

export type AlertItem = {
  id: number;
  file_id: string;
  level: AlertLevel;
  message: string;
  created_at: string;
};
