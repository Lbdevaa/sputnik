import { Badge } from "react-bootstrap";

import { formatDate } from "@/shared/lib/format";
import type { Column } from "@/shared/ui/DataTable";

import { LEVEL_LABELS, LEVEL_RANK, LEVEL_VARIANTS } from "../model/level";
import type { AlertItem } from "../model/types";

export function LevelBadge({ level }: { level: AlertItem["level"] }) {
  return <Badge bg={LEVEL_VARIANTS[level]}>{LEVEL_LABELS[level]}</Badge>;
}

export const alertColumns: Column<AlertItem>[] = [
  {
    key: "id",
    header: "ID",
    render: (alert) => alert.id,
    sortValue: (alert) => alert.id,
    className: "text-nowrap",
  },
  {
    key: "file_id",
    header: "Файл",
    render: (alert) => <span className="small font-monospace">{alert.file_id}</span>,
    searchValue: (alert) => alert.file_id,
  },
  {
    key: "level",
    header: "Уровень",
    render: (alert) => <LevelBadge level={alert.level} />,
    sortValue: (alert) => LEVEL_RANK[alert.level],
    searchValue: (alert) => LEVEL_LABELS[alert.level],
  },
  {
    key: "message",
    header: "Сообщение",
    render: (alert) => alert.message,
    sortValue: (alert) => alert.message,
    searchValue: (alert) => alert.message,
  },
  {
    key: "created_at",
    header: "Создан",
    render: (alert) => formatDate(alert.created_at),
    sortValue: (alert) => alert.created_at,
    className: "text-nowrap",
  },
];
