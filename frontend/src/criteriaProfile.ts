import type { CriterionId, Multipliers } from "./api/types";

const STORAGE_KEY = "desdobra1x2.multiplicadores";
export const MULTIPLIER_MAX = 2; // same limit as the backend (app/models.py)

/** Only the criteria the user moved away from 100%: an empty object means "default model". */
export function customOnly(multipliers: Multipliers): Multipliers {
  return Object.fromEntries(Object.entries(multipliers).filter(([, m]) => m !== 1)) as Multipliers;
}

export function isCustom(multipliers: Multipliers): boolean {
  return Object.keys(customOnly(multipliers)).length > 0;
}

export function loadMultipliers(): Multipliers {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "{}");
    if (!parsed || typeof parsed !== "object") return {};
    const valid = Object.entries(parsed).filter(
      ([, m]) => typeof m === "number" && m >= 0 && m <= MULTIPLIER_MAX,
    ) as [CriterionId, number][];
    return Object.fromEntries(valid);
  } catch {
    return {};
  }
}

export function saveMultipliers(multipliers: Multipliers): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(customOnly(multipliers)));
  } catch {
    // storage blocked (private window): the choice still applies until the page is closed
  }
}
