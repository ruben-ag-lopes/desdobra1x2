import type { Outcome } from "./api/types";

export const OUTCOMES: Outcome[] = ["1", "X", "2"];

/** Toggle an outcome, keeping at most the two most recently chosen ones (1 = fixed/simple, 2 = "dupla"). */
export function togglePick(current: Outcome[], outcome: Outcome): Outcome[] {
  if (current.includes(outcome)) return current.filter((o) => o !== outcome);
  return [...current, outcome].slice(-2);
}

/** "1X", "X2"… in the site's 1-X-2 order. */
export function pickLabel(picks: Outcome[]): string {
  return OUTCOMES.filter((o) => picks.includes(o)).join("");
}

/** Probability that one of the picked outcomes happens, from 1/X/2 probabilities. */
export function pickProbability(prob: number[], picks: Outcome[]): number {
  return picks.reduce((sum, o) => sum + prob[OUTCOMES.indexOf(o)], 0);
}

/** Confidence from the gap between the two likeliest outcomes; a "dupla" is suggested when it is low. */
export function confidence(prob: number[]): { level: "alta" | "média" | "baixa"; suggestion: Outcome[] } {
  const ranked = [0, 1, 2].sort((a, b) => prob[b] - prob[a]);
  const gap = prob[ranked[0]] - prob[ranked[1]];
  const level = gap >= 0.2 ? "alta" : gap >= 0.08 ? "média" : "baixa";
  const suggestion = (level === "baixa" ? ranked.slice(0, 2) : ranked.slice(0, 1)).map((i) => OUTCOMES[i]);
  return { level, suggestion };
}
