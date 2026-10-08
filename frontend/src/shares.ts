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

/** The predefined shares of the criteria this boletim uses: each model's weights, counted once per game it predicted. */
export function defaultShares(models: ModelCriteria[], usage: Map<string, number[]>): Shares {
  const raw: Shares = {};
  for (const m of models) {
    const games = usage.get(m.modelo)?.length ?? 1;
    for (const c of m.criterios) {
      if (c.id && TRAINED_IDS.has(c.id) && c.peso) {
        const id = c.id as CriterionId;
        raw[id] = (raw[id] ?? 0) + games * c.peso;
      }
    }
  }
  const ids = (Object.keys(raw) as CriterionId[]).sort((a, b) => (raw[b] ?? 0) - (raw[a] ?? 0));
  const parts = distribute(
    ids.map((i) => raw[i] ?? 0),
    100,
  );
  return Object.fromEntries(ids.map((id, k) => [id, parts[k]]));
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
 * variation match `target`. A criterion's share is proportional to multiplier x default share, so
 * the multiplier is target/default, scaled so the largest one is 1 (nothing is amplified).
 * Returns {} when the target equals the defaults.
 */
export function sharesToMultipliers(target: Shares, defaults: Shares): Multipliers {
  const ids = (Object.keys(defaults) as CriterionId[]).filter((i) => (defaults[i] ?? 0) > 0);
  const ratios = ids.map((i) => (target[i] ?? 0) / (defaults[i] as number));
  const top = Math.max(...ratios, 0);
  if (top === 0) return {};
  const out: Multipliers = {};
  ids.forEach((id, k) => {
    const m = Math.round((ratios[k] / top) * 100) / 100;
    if (m !== 1) out[id] = m;
  });
  return out;
}

/** The inverse, to show what a stored set of multipliers amounts to. */
export function sharesFromMultipliers(multipliers: Multipliers, defaults: Shares): Shares {
  const ids = Object.keys(defaults) as CriterionId[];
  const parts = distribute(
    ids.map((i) => (multipliers[i] ?? 1) * (defaults[i] ?? 0)),
    100,
  );
  return Object.fromEntries(ids.map((id, k) => [id, parts[k]]));
}
