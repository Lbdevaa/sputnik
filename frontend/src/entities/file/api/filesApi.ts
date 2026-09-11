import { apiUrl, request } from "@/shared/api/client";
import type { Page, PageQuery } from "@/shared/api/types";

import type { FileItem, FileUpdate } from "../model/types";

export function getFiles(query: PageQuery, signal?: AbortSignal): Promise<Page<FileItem>> {
  const params = new URLSearchParams({ limit: String(query.limit), offset: String(query.offset) });
  return request<Page<FileItem>>(`/files?${params}`, { signal });
}

export function uploadFile(title: string, file: File, signal?: AbortSignal): Promise<FileItem> {
  const body = new FormData();
  body.append("title", title);
  body.append("file", file);
  return request<FileItem>("/files", { method: "POST", body, signal });
}

export function updateFile(id: string, payload: FileUpdate): Promise<FileItem> {
  return request<FileItem>(`/files/${id}`, { method: "PATCH", json: payload });
}

export function deleteFile(id: string): Promise<void> {
  return request<void>(`/files/${id}`, { method: "DELETE" });
}

export function fileDownloadUrl(id: string): string {
  return apiUrl(`/files/${id}/download`);
}
