import { Badge } from "react-bootstrap";

import { formatDate, formatSize } from "@/shared/lib/format";
import type { Column } from "@/shared/ui/DataTable";

import { PROCESSING_LABELS, PROCESSING_VARIANTS, presentScan } from "../model/status";
import type { FileItem } from "../model/types";

export function ProcessingBadge({ file }: { file: FileItem }) {
  return (
    <Badge bg={PROCESSING_VARIANTS[file.processing_status]}>
      {PROCESSING_LABELS[file.processing_status]}
    </Badge>
  );
}

export function ScanCell({ file }: { file: FileItem }) {
  const scan = presentScan(file);
  return (
    <div className="d-flex flex-column gap-1">
      <div>
        <Badge bg={scan.variant}>{scan.label}</Badge>
      </div>
      <span className="small text-secondary">{scan.details}</span>
    </div>
  );
}

/** Колонки сущности «файл»; действия (скачать, удалить) добавляет виджет. */
export const fileColumns: Column<FileItem>[] = [
  {
    key: "title",
    header: "Название",
    render: (file) => (
      <>
        <div className="fw-semibold">{file.title}</div>
        <div className="small text-secondary font-monospace">{file.id}</div>
      </>
    ),
    sortValue: (file) => file.title,
    searchValue: (file) => `${file.title} ${file.id}`,
  },
  {
    key: "original_name",
    header: "Файл",
    render: (file) => file.original_name,
    sortValue: (file) => file.original_name,
    searchValue: (file) => file.original_name,
  },
  {
    key: "mime_type",
    header: "Тип",
    render: (file) => <span className="font-monospace small">{file.mime_type}</span>,
    sortValue: (file) => file.mime_type,
    searchValue: (file) => file.mime_type,
  },
  {
    key: "size",
    header: "Размер",
    render: (file) => formatSize(file.size),
    sortValue: (file) => file.size,
    className: "text-nowrap",
  },
  {
    key: "processing_status",
    header: "Статус",
    render: (file) => <ProcessingBadge file={file} />,
    sortValue: (file) => file.processing_status,
    searchValue: (file) => PROCESSING_LABELS[file.processing_status],
  },
  {
    key: "scan_status",
    header: "Проверка",
    render: (file) => <ScanCell file={file} />,
    sortValue: (file) => file.scan_status,
    searchValue: (file) => `${presentScan(file).label} ${file.scan_details ?? ""}`,
  },
  {
    key: "created_at",
    header: "Создан",
    render: (file) => formatDate(file.created_at),
    sortValue: (file) => file.created_at,
    className: "text-nowrap",
  },
];
