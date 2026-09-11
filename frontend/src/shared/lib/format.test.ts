import { describe, expect, it } from "vitest";

import { formatDate, formatSize } from "./format";

describe("formatSize", () => {
  it.each([
    [0, "0 B"],
    [29, "29 B"],
    [1023, "1023 B"],
    [1024, "1.0 KB"],
    [1536, "1.5 KB"],
    [1024 * 1024, "1.0 MB"],
    [11_000_000, "10.5 MB"],
    [3 * 1024 ** 3, "3.0 GB"],
  ])("%d → %s", (size, expected) => {
    expect(formatSize(size)).toBe(expected);
  });

  it("не падает на мусоре", () => {
    expect(formatSize(-1)).toBe("—");
    expect(formatSize(Number.NaN)).toBe("—");
  });
});

describe("formatDate", () => {
  it("форматирует ISO-дату в короткий русский формат", () => {
    expect(formatDate("2026-09-04T10:30:00+00:00")).toMatch(/^\d{2}\.\d{2}\.\d{4}, \d{2}:\d{2}$/);
  });

  it("не бросает на невалидной строке", () => {
    expect(formatDate("not a date")).toBe("—");
  });
});
