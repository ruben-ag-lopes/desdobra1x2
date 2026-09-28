import type { Criteria, CriterionId, LegacyCriterionId, LegacyWeights, Multipliers } from "./api/types";

const STORAGE_KEY = "desdobra1x2.criterios";
export const MULTIPLIER_MAX = 2; // same limit as the backend (app/models.py)
export const LEGACY_SHARE_MAX = 1; // same limit as the backend (app/models.py, "Share")

// Mirrors app/services/totobola_engine.py, LEGACY_WEIGHTS_DEFAULT — used only to tell "still at
// the default" apart from "changed", the way 1.0 does for the multipliers above.
export const LEGACY_DEFAULTS: Record<LegacyCriterionId, number> = {
  forma: 0.4,
  ranking_uefa: 0.3,
  ultimos2: 0.15,
  confronto_direto: 0.1,
  classificacao: 0.05,
};

export function emptyCriteria(): Criteria {
  return { multiplicadores: {}, pesosAntigos: {} };
}

/** Only the criteria the user moved away from 100%: an empty object means "default model". */
export function customOnly(multipliers: Multipliers): Multipliers {
  return Object.fromEntries(Object.entries(multipliers).filter(([, m]) => m !== 1)) as Multipliers;
}

/** Only the legacy shares that differ from LEGACY_DEFAULTS. */
export function legacyCustomOnly(weights: LegacyWeights): LegacyWeights {
  return Object.fromEntries(
    Object.entries(weights).filter(([id, w]) => w !== LEGACY_DEFAULTS[id as LegacyCriterionId]),
  ) as LegacyWeights;
}

export function isCustom(multipliers: Multipliers): boolean {
  return Object.keys(customOnly(multipliers)).length > 0;
}

export function isLegacyCustom(weights: LegacyWeights): boolean {
  return Object.keys(legacyCustomOnly(weights)).length > 0;
}

export function isCriteriaCustom(c: Criteria): boolean {
  return isCustom(c.multiplicadores) || isLegacyCustom(c.pesosAntigos);
}

/** Sum of the legacy shares (must stay <= 100%, enforced by the backend too). */
export function legacySum(weights: LegacyWeights): number {
  return Object.values(weights).reduce((sum: number, w) => sum + (w ?? 0), 0);
}

export function loadCriteria(): Criteria {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "{}");
    if (!parsed || typeof parsed !== "object") return emptyCriteria();
    const { multiplicadores, pesosAntigos } = parsed as Partial<Criteria>;
    const validMult = Object.entries(multiplicadores ?? {}).filter(
      ([, m]) => typeof m === "number" && m >= 0 && m <= MULTIPLIER_MAX,
    ) as [CriterionId, number][];
    const validLegacy = Object.entries(pesosAntigos ?? {}).filter(
      ([, w]) => typeof w === "number" && w >= 0 && w <= LEGACY_SHARE_MAX,
    ) as [LegacyCriterionId, number][];
    return { multiplicadores: Object.fromEntries(validMult), pesosAntigos: Object.fromEntries(validLegacy) };
  } catch {
    return emptyCriteria();
  }
}

export function saveCriteria(c: Criteria): void {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ multiplicadores: customOnly(c.multiplicadores), pesosAntigos: legacyCustomOnly(c.pesosAntigos) }),
    );
  } catch {
    // storage blocked (private window): the choice still applies until the page is closed
  }
}
