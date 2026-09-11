// Статусы — union-типы, согласованные с перечислениями бэкенда (Б5, Г4).
export const PROCESSING_STATUSES = ["uploaded", "processing", "processed", "failed"] as const;
export type ProcessingStatus = (typeof PROCESSING_STATUSES)[number];

export const SCAN_STATUSES = ["clean", "suspicious", "failed"] as const;
export type ScanStatus = (typeof SCAN_STATUSES)[number];

export type FileItem = {
  id: string;
  title: string;
  original_name: string;
  mime_type: string;
  size: number;
  processing_status: ProcessingStatus;
  scan_status: ScanStatus | null;
  scan_details: string | null;
  metadata_json: Record<string, unknown> | null;
  requires_attention: boolean;
  created_at: string;
  updated_at: string;
};

export type FileUpdate = {
  title: string;
};
