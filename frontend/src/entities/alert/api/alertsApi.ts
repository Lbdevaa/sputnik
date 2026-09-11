import { request } from "@/shared/api/client";
import type { Page, PageQuery } from "@/shared/api/types";

import type { AlertItem } from "../model/types";

export function getAlerts(query: PageQuery, signal?: AbortSignal): Promise<Page<AlertItem>> {
  const params = new URLSearchParams({ limit: String(query.limit), offset: String(query.offset) });
  return request<Page<AlertItem>>(`/alerts?${params}`, { signal });
}
