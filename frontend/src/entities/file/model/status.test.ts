import { describe, expect, it } from "vitest";

import { hasPendingFiles, isPending, presentScan } from "./status";

describe("presentScan", () => {
  it("до проверки — нейтральный бейдж, а не зелёный (Г4)", () => {
    const result = presentScan({ scan_status: null, scan_details: null });
    expect(result.variant).toBe("secondary");
    expect(result.label).toBe("ожидает");
  });

  it.each([
    ["clean", "success"],
    ["suspicious", "warning"],
    ["failed", "danger"],
  ] as const)("%s → %s", (status, variant) => {
    expect(presentScan({ scan_status: status, scan_details: "x" }).variant).toBe(variant);
  });

  it("пробрасывает детали проверки", () => {
    expect(
      presentScan({ scan_status: "suspicious", scan_details: "suspicious extension .exe" }).details,
    ).toBe("suspicious extension .exe");
  });
});

describe("isPending", () => {
  it.each([
    ["uploaded", true],
    ["processing", true],
    ["processed", false],
    ["failed", false],
  ] as const)("%s → %s", (status, expected) => {
    expect(isPending({ processing_status: status })).toBe(expected);
  });

  it("hasPendingFiles: опрос нужен, пока хоть один файл в работе", () => {
    expect(hasPendingFiles([{ processing_status: "processed" }])).toBe(false);
    expect(
      hasPendingFiles([{ processing_status: "processed" }, { processing_status: "uploaded" }]),
    ).toBe(true);
    expect(hasPendingFiles([])).toBe(false);
  });
});
