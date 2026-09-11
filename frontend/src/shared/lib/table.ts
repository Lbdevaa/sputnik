// Сортировка и фильтр над уже загруженной страницей: чистые функции, без React.

export type SortDirection = "asc" | "desc";

export type SortState = {
  key: string;
  direction: SortDirection;
};

export type SortValue = string | number | boolean | null | undefined;

const collator = new Intl.Collator("ru", { numeric: true, sensitivity: "base" });

function compareValues(a: SortValue, b: SortValue): number {
  if (a == null && b == null) return 0;
  if (a == null) return 1; // пустые — в конец при любом направлении
  if (b == null) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  if (typeof a === "boolean" && typeof b === "boolean") return Number(a) - Number(b);
  return collator.compare(String(a), String(b));
}

export function sortRows<T>(
  rows: readonly T[],
  sort: SortState | null,
  valueOf: (row: T, key: string) => SortValue,
): T[] {
  if (!sort) {
    return [...rows];
  }
  const sign = sort.direction === "asc" ? 1 : -1;
  return [...rows]
    .map((row, index) => ({ row, index }))
    .sort((left, right) => {
      const byValue = compareValues(valueOf(left.row, sort.key), valueOf(right.row, sort.key));
      const a = valueOf(left.row, sort.key);
      const b = valueOf(right.row, sort.key);
      // Пустые значения всегда в конце, остальное — по направлению; равные — в исходном порядке.
      if (a == null || b == null) return byValue || left.index - right.index;
      return byValue * sign || left.index - right.index;
    })
    .map(({ row }) => row);
}

export function nextSort(current: SortState | null, key: string): SortState | null {
  if (current?.key !== key) return { key, direction: "asc" };
  if (current.direction === "asc") return { key, direction: "desc" };
  return null;
}

export function filterRows<T>(
  rows: readonly T[],
  query: string,
  searchText: (row: T) => string,
): T[] {
  const needle = query.trim().toLocaleLowerCase();
  if (!needle) {
    return [...rows];
  }
  return rows.filter((row) => searchText(row).toLocaleLowerCase().includes(needle));
}

export function pageCount(total: number, pageSize: number): number {
  return Math.max(1, Math.ceil(total / pageSize));
}
