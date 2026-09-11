"use client";

import { type PagedQueryState, usePagedQuery } from "@/shared/lib/usePagedQuery";

import { getAlerts } from "../api/alertsApi";
import type { AlertItem } from "./types";

type Options = {
  /** Алерты появляются в конце конвейера, поэтому интервал им задаёт тот, кто знает про файлы. */
  pollMs: number | null;
};

export function useAlerts({ pollMs }: Options): PagedQueryState<AlertItem> {
  return usePagedQuery(getAlerts, { pollMs });
}
