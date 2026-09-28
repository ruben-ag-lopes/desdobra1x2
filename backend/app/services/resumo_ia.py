"""AI-written plain-language summary of a desdobramento (docs/plano-resumo-ia.md).

The model never computes probabilities: it only receives numbers already produced by
totobola_engine and rewrites them as a short explanation. Optional feature: without
ANTHROPIC_API_KEY the app works exactly the same, just without the "Explicar" button.
"""

import hashlib
import json

import httpx

from app.cache import TTLCache
from app.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from app.models import ResultProbabilities
from app.services import criteria as criteria_service

_cache = TTLCache(ttl_seconds=24 * 3600)
_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

_SYSTEM_PROMPT = """Explicas, em português de Portugal e em 3 a 6 frases curtas, um desdobramento de \
apostas do Totobola a partir SÓ dos dados fornecidos em JSON. Nunca inventes números que não estejam \
no JSON. Nunca sugiras apostar mais, gastar mais dinheiro, ou dês conselhos financeiros. Nunca \
garantas ou insinues que as apostas vão acertar. Lembra sempre, pelo menos uma vez, que é uma \
previsão estatística sem garantia. Refere os critérios que mais pesam nos jogos mais decisivos e, \
se algum jogo for "pouco fiável" (sem histórico), menciona-o. Escreve só o texto do resumo, sem \
título nem listas."""


def enabled() -> bool:
    return bool(ANTHROPIC_API_KEY)


def _context(probabilities: list[ResultProbabilities], n_apostas: int) -> dict:
    models = criteria_service.describe(list(dict.fromkeys(p.modelo for p in probabilities if p.modelo != "fixo")))
    top_criterion = {m.modelo: m.criterios[0].nome for m in models if m.criterios}

    jogos = []
    for i, p in enumerate(probabilities, start=1):
        jogo: dict = {
            "numero": i,
            "casa": p.home_team,
            "fora": p.away_team,
            "modelo": p.modelo,
            "pouco_fiavel": p.low_confidence,
        }
        if p.fixed_results and p.modelo == "fixo":
            jogo["fixo"] = p.fixed_results[0]
        else:
            jogo["prob"] = {"1": p.prob_home, "X": p.prob_draw, "2": p.prob_away}
            if len(p.fixed_results) == 2:
                jogo["dupla"] = p.fixed_results
            if p.modelo in top_criterion:
                jogo["criterio_principal"] = top_criterion[p.modelo]
        jogos.append(jogo)

    return {"n_apostas": n_apostas, "jogos": jogos}


def _cache_key(context: dict) -> str:
    return hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()


def summarize(probabilities: list[ResultProbabilities], n_apostas: int) -> str | None:
    """A short AI-written explanation of the desdobramento, or None if the feature is off."""
    if not enabled():
        return None

    context = _context(probabilities, n_apostas)
    return _cache.get_or_set(_cache_key(context), lambda: _call_anthropic(context))


def _call_anthropic(context: dict) -> str:
    resp = httpx.post(
        _ANTHROPIC_URL,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 400,
            "system": _SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": json.dumps(context, ensure_ascii=False)}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    return "".join(block["text"] for block in resp.json()["content"] if block["type"] == "text").strip()
