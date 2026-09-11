import type { AlertLevel } from "./types";

export type LevelVariant = "success" | "warning" | "danger";

export const LEVEL_VARIANTS: Record<AlertLevel, LevelVariant> = {
  info: "success",
  warning: "warning",
  critical: "danger",
};

export const LEVEL_LABELS: Record<AlertLevel, string> = {
  info: "инфо",
  warning: "внимание",
  critical: "критично",
};

/** Порядок для сортировки по важности. */
export const LEVEL_RANK: Record<AlertLevel, number> = { info: 0, warning: 1, critical: 2 };
