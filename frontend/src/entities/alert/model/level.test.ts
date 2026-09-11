import { describe, expect, it } from "vitest";

import { LEVEL_LABELS, LEVEL_RANK, LEVEL_VARIANTS } from "./level";
import { ALERT_LEVELS } from "./types";

describe("уровни алертов", () => {
  it("каждый уровень бэкенда имеет вариант, подпись и ранг", () => {
    for (const level of ALERT_LEVELS) {
      expect(LEVEL_VARIANTS[level]).toBeTruthy();
      expect(LEVEL_LABELS[level]).toBeTruthy();
      expect(LEVEL_RANK[level]).toBeTypeOf("number");
    }
  });

  it("ранг растёт с важностью", () => {
    expect(LEVEL_RANK.info).toBeLessThan(LEVEL_RANK.warning);
    expect(LEVEL_RANK.warning).toBeLessThan(LEVEL_RANK.critical);
  });
});
