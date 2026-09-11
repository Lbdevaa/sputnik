"use client";

import { useCallback, useMemo, useState } from "react";

import type { Page, PageQuery } from "@/shared/api/types";
import { DEFAULT_PAGE_SIZE } from "@/shared/config/polling";
import { pageCount } from "@/shared/lib/table";
import { type QueryOptions, type QueryState, useQuery } from "@/shared/lib/useQuery";

export type Pagination = {
  page: number;
  pageSize: number;
  total: number;
  pages: number;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
};

export type PagedQueryState<T> = QueryState<Page<T>> & {
  items: T[];
  pagination: Pagination;
};

/** Серверная пагинация поверх useQuery: страница и размер живут здесь, окно уходит в запрос. */
export function usePagedQuery<T>(
  fetcher: (query: PageQuery, signal: AbortSignal) => Promise<Page<T>>,
  options: QueryOptions<Page<T>> = {},
): PagedQueryState<T> {
  const [page, setPageState] = useState(1);
  const [pageSize, setPageSizeState] = useState<number>(DEFAULT_PAGE_SIZE);

  const load = useCallback(
    (signal: AbortSignal) => fetcher({ limit: pageSize, offset: (page - 1) * pageSize }, signal),
    [fetcher, page, pageSize],
  );
  const query = useQuery(load, options);

  const total = query.data?.total ?? 0;
  const pages = pageCount(total, pageSize);

  const setPage = useCallback(
    (next: number) => setPageState(Math.min(Math.max(1, next), pages)),
    [pages],
  );
  const setPageSize = useCallback((size: number) => {
    setPageSizeState(size);
    setPageState(1);
  }, []);

  const pagination = useMemo<Pagination>(
    () => ({ page: Math.min(page, pages), pageSize, total, pages, setPage, setPageSize }),
    [page, pageSize, total, pages, setPage, setPageSize],
  );

  return { ...query, items: query.data?.items ?? [], pagination };
}
