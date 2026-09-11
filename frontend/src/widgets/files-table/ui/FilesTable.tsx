"use client";

import { useMemo } from "react";
import { Button } from "react-bootstrap";

import {
  fileColumns,
  fileDownloadUrl,
  type FileItem,
  type FilesQuery,
  isPending,
} from "@/entities/file";
import { DeleteFileButton } from "@/features/delete-file";
import { type Column, DataTable } from "@/shared/ui/DataTable";
import { ErrorBanner } from "@/shared/ui/ErrorBanner";
import { SectionCard } from "@/shared/ui/SectionCard";

type Props = {
  query: FilesQuery;
  actions?: React.ReactNode;
  onChanged: () => void;
  onError: (message: string) => void;
};

export function FilesTable({ query, actions, onChanged, onError }: Props) {
  const columns = useMemo<Column<FileItem>[]>(
    () => [
      ...fileColumns,
      {
        key: "actions",
        header: "",
        className: "text-nowrap text-end",
        render: (file) => (
          <div className="d-inline-flex gap-2">
            <Button
              as="a"
              href={fileDownloadUrl(file.id)}
              variant="outline-primary"
              size="sm"
              download={file.original_name}
            >
              Скачать
            </Button>
            <DeleteFileButton file={file} onDeleted={onChanged} onError={onError} />
          </div>
        ),
      },
    ],
    [onChanged, onError],
  );

  return (
    <SectionCard title="Файлы" count={query.pagination.total} live={query.isLive} actions={actions}>
      <ErrorBanner message={query.error} onRetry={() => void query.refetch()} />
      <DataTable
        columns={columns}
        rows={query.items}
        rowKey={(file) => file.id}
        isLoading={query.isLoading}
        emptyText="Файлы пока не загружены"
        pagination={query.pagination}
        searchPlaceholder="Поиск по названию, файлу, типу"
        rowClassName={(file) => (isPending(file) ? "table-light" : undefined)}
      />
    </SectionCard>
  );
}
