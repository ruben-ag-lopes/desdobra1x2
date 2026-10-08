import type { CriterionId, ModelCriteria, Multipliers, Shares } from "./api/types";

export const TRAINED_IDS = new Set<string>(["elo", "casa", "ataque", "defesa", "h2h"]);

/** Splits `total` into whole numbers proportional to `weights`; the parts always add up to `total`. */
export function distribute(weights: number[], total: number): number[] {
  const sum = weights.reduce((a, b) => a + b, 0);
  if (total <= 0 || sum <= 0) return weights.map(() => 0);
  const raw = weights.map((w) => (w / sum) * total);
  const out = raw.map(Math.floor);
  let left = total - out.reduce((a, b) => a + b, 0);
  const byFraction = raw.map((r, i) => [r - Math.floor(r), i] as const).sort((a, b) => b[0] - a[0] || a[1] - b[1]);
  for (const [, i] of byFraction) {
    if (left <= 0) break;
    out[i] += 1;
    left -= 1;
  }
  return out;
}

/** All five criteria, always listed in this order. */
export const ALL_IDS: CriterionId[] = ["elo", "casa", "ataque", "defesa", "h2h"];

/**
 * The predefined shares of the five criteria in this boletim: each model's weights, counted once per
 * game it predicted. A criterion the model doesn't use (e.g. attack in an Elo league) is 0.
 */
export function defaultShares(models: ModelCriteria[], usage: Map<string, number[]>): Shares {
  const raw: Record<string, number> = Object.fromEntries(ALL_IDS.map((i) => [i, 0]));
  for (const m of models) {
    const games = usage.get(m.modelo)?.length ?? 1;
    for (const c of m.criterios) {
      if (c.id && TRAINED_IDS.has(c.id) && c.peso) raw[c.id] += games * c.peso;
    }
  }
  const parts = distribute(
    ALL_IDS.map((i) => raw[i]),
    100,
  );
  return Object.fromEntries(ALL_IDS.map((id, k) => [id, parts[k]]));
}

/**
 * How much each criterion weighs in the model that uses all five, for this boletim (same
 * game-weighted average, fractions of 1). This is what a customisation is measured against.
 */
export function fullWeights(models: ModelCriteria[], usage: Map<string, number[]>): Record<CriterionId, number> {
  const raw = Object.fromEntries(ALL_IDS.map((i) => [i, 0])) as Record<CriterionId, number>;
  let games = 0;
  for (const m of models) {
    const n = usage.get(m.modelo)?.length ?? 1;
    games += n;
    for (const id of ALL_IDS) {
      const own = m.criterios.find((c) => c.id === id)?.peso ?? 0;
      raw[id] += n * (m.pesos_completos?.[id] ?? own);
    }
  }
  return Object.fromEntries(ALL_IDS.map((id) => [id, Math.max(raw[id] / Math.max(games, 1), 0.005)])) as Record<
    CriterionId,
    number
  >;
}

/** Sets one criterion and spreads the rest over the others in proportion, so the total stays exactly 100. */
export function setShare(current: Shares, id: CriterionId, value: number): Shares {
  const ids = Object.keys(current) as CriterionId[];
  const chosen = Math.min(100, Math.max(0, Math.round(value)));
  const others = ids.filter((i) => i !== id);
  if (others.length === 0) return { [id]: 100 };
  let weights = others.map((i) => current[i] ?? 0);
  if (weights.every((w) => w === 0)) weights = others.map(() => 1);
  const spread = distribute(weights, 100 - chosen);
  return Object.fromEntries(
    ids.map((i) => [i, i === id ? chosen : spread[others.indexOf(i)]]),
  );
}

export function sameShares(a: Shares, b: Shares): boolean {
  const ids = new Set([...Object.keys(a), ...Object.keys(b)]) as Set<CriterionId>;
  return [...ids].every((i) => (a[i] ?? 0) === (b[i] ?? 0));
}

/**
 * The multipliers (0..1, what the server understands) that make each criterion's share of the
 * variation match `target`. A criterion's share is proportional to multiplier x its weight in the
 * full model, so the multiplier is target/weight, scaled so the largest is 1 (nothing is amplified).
 * Returns {} when nothing would change.
 */
export function sharesToMultipliers(target: Shares, full: Record<CriterionId, number>): Multipliers {
  const ratios = ALL_IDS.map((i) => (target[i] ?? 0) / full[i]);
  const top = Math.max(...ratios, 0);
  if (top === 0) return {};
  const out: Multipliers = {};
  ALL_IDS.forEach((id, k) => {
    const m = Math.round((ratios[k] / top) * 100) / 100;
    if (m !== 1) out[id] = m;
  });
  return out;
}

/** The inverse, to show what a stored set of multipliers amounts to. */
export function sharesFromMultipliers(multipliers: Multipliers, full: Record<CriterionId, number>): Shares {
  const parts = distribute(
    ALL_IDS.map((i) => (multipliers[i] ?? 1) * full[i]),
    100,
  );
  return Object.fromEntries(ALL_IDS.map((id, k) => [id, parts[k]]));
}
