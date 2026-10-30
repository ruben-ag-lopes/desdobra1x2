// Run with: npm test
import assert from "node:assert/strict";
import { test } from "node:test";
import { montarAposta } from "./aposta.ts";

test("Euromilhões: 5 numbers then 2 stars", () => {
  assert.equal(montarAposta(["3", "4", "6", "7", "8", "1", "2"], 5), "3 4 6 7 8 + 1 2");
});

test("Totoloto: 5 numbers then the lucky number", () => {
  assert.equal(montarAposta(["3", "4", "6", "7", "8", "1"], 5), "3 4 6 7 8 + 1");
});

test("EuroDreams: 6 numbers then the dream number", () => {
  assert.equal(montarAposta(["1", "2", "3", "4", "5", "6", "2"], 6), "1 2 3 4 5 6 + 2");
});
