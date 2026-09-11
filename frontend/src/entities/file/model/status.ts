import type { FileItem, ProcessingStatus, ScanStatus } from "./types";

export type BadgeVariant = "secondary" | "warning" | "success" | "danger" | "info";

export const PROCESSING_LABELS: Record<ProcessingStatus, string> = {
  uploaded: "загружен",
  processing: "обрабатывается",
  processed: "обработан",
  failed: "ошибка",
};

export const PROCESSING_VARIANTS: Record<ProcessingStatus, BadgeVariant> = {
  uploaded: "secondary",
  processing: "info",
  processed: "success",
  failed: "danger",
};

/** Файл ещё в конвейере: по таким строкам идёт опрос (Г3). */
export function isPending(file: Pick<FileItem, "processing_status">): boolean {
  return file.processing_status === "uploaded" || file.processing_status === "processing";
}

export function hasPendingFiles(files: readonly Pick<FileItem, "processing_status">[]): boolean {
  return files.some(isPending);
}

export type ScanPresentation = {
  label: string;
  variant: BadgeVariant;
  details: string;
};

/**
 * Проверка: пока её не было — нейтральный «ожидает», а не зелёный «чисто» (Г4).
 * Исходный код красил по `requires_attention`, и до проверки строка светилась успехом.
 */
export function presentScan(
  file: Pick<FileItem, "scan_status" | "scan_details">,
): ScanPresentation {
  const status: ScanStatus | null = file.scan_status;
  if (status === null) {
    return { label: "ожидает", variant: "secondary", details: "Проверка ещё не выполнялась" };
  }
  const details = file.scan_details ?? "";
  switch (status) {
    case "clean":
      return { label: "чисто", variant: "success", details };
    case "suspicious":
      return { label: "подозрительный", variant: "warning", details };
    case "failed":
      return { label: "ошибка", variant: "danger", details };
  }
}
