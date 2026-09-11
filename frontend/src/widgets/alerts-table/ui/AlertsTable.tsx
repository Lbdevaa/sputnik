"use client";

import { alertColumns, type AlertItem } from "@/entities/alert";
import type { PagedQueryState } from "@/shared/lib/usePagedQuery";
import { DataTable } from "@/shared/ui/DataTable";
import { ErrorBanner } from "@/shared/ui/ErrorBanner";
import { SectionCard } from "@/shared/ui/SectionCard";

type Props = {
  query: PagedQueryState<AlertItem>;
  live: boolean;
};

export function AlertsTable({ query, live }: Props) {
  return (
    <SectionCard title="Алерты" count={query.pagination.total} live={live}>
      <ErrorBanner message={query.error} onRetry={() => void query.refetch()} />
      <DataTable
        columns={alertColumns}
        rows={query.items}
        rowKey={(alert) => alert.id}
        isLoading={query.isLoading}
        emptyText="Алертов пока нет"
        pagination={query.pagination}
        searchPlaceholder="Поиск по сообщению, файлу, уровню"
      />
    </SectionCard>
  );
}
