"use client";

import { Form, Pagination as BsPagination } from "react-bootstrap";

import { PAGE_SIZES } from "@/shared/config/polling";
import type { Pagination } from "@/shared/lib/usePagedQuery";

type Props = {
  pagination: Pagination;
  /** Сколько строк реально видно после поиска на странице. */
  shown: number;
  filtered: boolean;
};

function pageNumbers(current: number, pages: number): number[] {
  const window = 2;
  const from = Math.max(1, current - window);
  const to = Math.min(pages, current + window);
  return Array.from({ length: to - from + 1 }, (_, i) => from + i);
}

export function TablePagination({ pagination, shown, filtered }: Props) {
  const { page, pageSize, total, pages, setPage, setPageSize } = pagination;
  const first = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const last = Math.min(page * pageSize, total);

  return (
    <div className="d-flex flex-wrap justify-content-between align-items-center gap-3">
      <div className="small text-secondary">
        {total === 0
          ? "Нет записей"
          : filtered
            ? `Показано ${shown} из ${last - first + 1} на странице (${first}–${last} из ${total})`
            : `${first}–${last} из ${total}`}
      </div>

      <div className="d-flex align-items-center gap-3">
        <Form.Select
          size="sm"
          value={pageSize}
          onChange={(event) => setPageSize(Number(event.target.value))}
          aria-label="Строк на странице"
          style={{ width: "auto" }}
        >
          {PAGE_SIZES.map((size) => (
            <option key={size} value={size}>
              {size} на странице
            </option>
          ))}
        </Form.Select>

        {pages > 1 ? (
          <BsPagination size="sm" className="mb-0">
            <BsPagination.First disabled={page === 1} onClick={() => setPage(1)} />
            <BsPagination.Prev disabled={page === 1} onClick={() => setPage(page - 1)} />
            {pageNumbers(page, pages).map((n) => (
              <BsPagination.Item key={n} active={n === page} onClick={() => setPage(n)}>
                {n}
              </BsPagination.Item>
            ))}
            <BsPagination.Next disabled={page === pages} onClick={() => setPage(page + 1)} />
            <BsPagination.Last disabled={page === pages} onClick={() => setPage(pages)} />
          </BsPagination>
        ) : null}
      </div>
    </div>
  );
}
