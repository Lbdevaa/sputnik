import { describe, expect, it } from "vitest";

import { filterRows, nextSort, pageCount, sortRows } from "./table";

type Row = { name: string; size: number | null };

const rows: Row[] = [
  { name: "файл 10", size: 300 },
  { name: "файл 2", size: null },
  { name: "Файл 1", size: 100 },
];

const valueOf = (row: Row, key: string) => (key === "name" ? row.name : row.size);

describe("sortRows", () => {
  it("без сортировки возвращает копию в исходном порядке", () => {
    const result = sortRows(rows, null, valueOf);
    expect(result).toEqual(rows);
    expect(result).not.toBe(rows);
  });

  it("сортирует строки с учётом чисел внутри и без учёта регистра", () => {
    const names = sortRows(rows, { key: "name", direction: "asc" }, valueOf).map((r) => r.name);
    expect(names).toEqual(["Файл 1", "файл 2", "файл 10"]);
  });

  it("пустые значения всегда в конце", () => {
    const asc = sortRows(rows, { key: "size", direction: "asc" }, valueOf).map((r) => r.size);
    const desc = sortRows(rows, { key: "size", direction: "desc" }, valueOf).map((r) => r.size);
    expect(asc).toEqual([100, 300, null]);
    expect(desc).toEqual([300, 100, null]);
  });
});

describe("nextSort", () => {
  it("идёт по кругу: asc → desc → без сортировки", () => {
    const first = nextSort(null, "name");
    const second = nextSort(first, "name");
    const third = nextSort(second, "name");
    expect(first).toEqual({ key: "name", direction: "asc" });
    expect(second).toEqual({ key: "name", direction: "desc" });
    expect(third).toBeNull();
  });

  it("смена колонки начинает с asc", () => {
    expect(nextSort({ key: "name", direction: "desc" }, "size")).toEqual({
      key: "size",
      direction: "asc",
    });
  });
});

describe("filterRows", () => {
  it("ищет подстроку без учёта регистра и пробелов по краям", () => {
    const result = filterRows(rows, "  ФАЙЛ 1 ", (r) => r.name);
    expect(result.map((r) => r.name)).toEqual(["файл 10", "Файл 1"]);
  });

  it("пустой запрос возвращает всё", () => {
    expect(filterRows(rows, "   ", (r) => r.name)).toHaveLength(3);
  });
});

describe("pageCount", () => {
  it.each([
    [0, 20, 1],
    [1, 20, 1],
    [20, 20, 1],
    [21, 20, 2],
    [152, 50, 4],
  ])("total=%d pageSize=%d → %d", (total, pageSize, expected) => {
    expect(pageCount(total, pageSize)).toBe(expected);
  });
});
