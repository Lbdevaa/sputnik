"use client";

import type { Page } from "@/shared/api/types";
import { POLL_INTERVAL_MS } from "@/shared/config/polling";
import { type PagedQueryState, usePagedQuery } from "@/shared/lib/usePagedQuery";

import { getFiles } from "../api/filesApi";
import { hasPendingFiles } from "./status";
import type { FileItem } from "./types";

export type FilesQuery = PagedQueryState<FileItem> & {
  /** Есть файлы в конвейере — список обновляется сам. */
  isLive: boolean;
};

// Опрос включается только пока на странице есть файлы «в работе» (Г3): как только все
// обработаны, запросы прекращаются сами.
function pollWhilePending(page: Page<FileItem> | null): number | null {
  return page && hasPendingFiles(page.items) ? POLL_INTERVAL_MS : null;
}

export function useFiles(): FilesQuery {
  const query = usePagedQuery(getFiles, { pollMs: pollWhilePending });
  return { ...query, isLive: hasPendingFiles(query.items) };
}
