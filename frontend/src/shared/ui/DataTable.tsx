"use client";

import { type ReactNode, useMemo, useState } from "react";
import { Form, Spinner, Table } from "react-bootstrap";

import type { Pagination } from "@/shared/lib/usePagedQuery";
import { filterRows, nextSort, type SortState, type SortValue, sortRows } from "@/shared/lib/table";
import { TablePagination } from "@/shared/ui/TablePagination";

export type Column<T> = {
  key: string;
  header: ReactNode;
  render: (row: T) => ReactNode;
  /** Значение для сортировки; колонка без него не сортируется. */
  sortValue?: (row: T) => SortValue;
  /** Текст для поиска; колонка без него в поиске не участвует. */
  searchValue?: (row: T) => string;
  className?: string;
  headerClassName?: string;
};

type Props<T> = {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  isLoading: boolean;
  emptyText: string;
  pagination?: Pagination;
  searchPlaceholder?: string;
  /** Пометка строки: например, файл в обработке. */
  rowClassName?: (row: T) => string | undefined;
};

/**
 * Таблица с сортировкой, поиском и пагинацией (Г10).
 *
 * Страница — серверная: бэкенд отдаёт окно `limit/offset`. Сортировка и поиск — над
 * загруженной страницей; это честно подписано в подвале, чтобы «поиск нашёл 0» не
 * читалось как «в базе нет».
 */
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  isLoading,
  emptyText,
  pagination,
  searchPlaceholder = "Поиск на странице",
  rowClassName,
}: Props<T>) {
  const [sort, setSort] = useState<SortState | null>(null);
  const [query, setQuery] = useState("");

  const searchable = useMemo(() => columns.filter((c) => c.searchValue), [columns]);
  const columnByKey = useMemo(() => new Map(columns.map((c) => [c.key, c])), [columns]);

  const visible = useMemo(() => {
    const filtered = filterRows(rows, query, (row) =>
      searchable.map((c) => c.searchValue?.(row) ?? "").join(" "),
    );
    return sortRows(filtered, sort, (row, key) => columnByKey.get(key)?.sortValue?.(row));
  }, [rows, query, sort, searchable, columnByKey]);

  const colSpan = columns.length;

  return (
    <div className="d-flex flex-column gap-3">
      {searchable.length > 0 ? (
        <Form.Control
          type="search"
          size="sm"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={searchPlaceholder}
          aria-label={searchPlaceholder}
          style={{ maxWidth: 320 }}
        />
      ) : null}

      <div className="table-responsive">
        <Table hover bordered className="align-middle mb-0">
          <thead className="table-light">
            <tr>
              {columns.map((column) => {
                const sortable = Boolean(column.sortValue);
                const active = sort?.key === column.key ? sort.direction : null;
                return (
                  <th
                    key={column.key}
                    className={column.headerClassName}
                    role={sortable ? "button" : undefined}
                    aria-sort={active ? (active === "asc" ? "ascending" : "descending") : undefined}
                    onClick={sortable ? () => setSort((s) => nextSort(s, column.key)) : undefined}
                    style={sortable ? { cursor: "pointer", userSelect: "none" } : undefined}
                  >
                    {column.header}
                    {sortable ? (
                      <span className="ms-1 text-secondary">
                        {active === "asc" ? "▲" : active === "desc" ? "▼" : "↕"}
                      </span>
                    ) : null}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={colSpan} className="text-center py-5">
                  <Spinner animation="border" role="status" />
                </td>
              </tr>
            ) : visible.length === 0 ? (
              <tr>
                <td colSpan={colSpan} className="text-center py-4 text-secondary">
                  {query ? "На этой странице ничего не найдено" : emptyText}
                </td>
              </tr>
            ) : (
              visible.map((row) => (
                <tr key={rowKey(row)} className={rowClassName?.(row)}>
                  {columns.map((column) => (
                    <td key={column.key} className={column.className}>
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </Table>
      </div>

      {pagination ? (
        <TablePagination pagination={pagination} shown={visible.length} filtered={Boolean(query)} />
      ) : null}
    </div>
  );
}
