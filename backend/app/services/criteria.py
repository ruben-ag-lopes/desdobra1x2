"""Plain-language criteria and weights of each prediction model (shown in the app's pop-up)."""

from app.models import Criterion, ModelCriteria
from app.research.importance import CRITERIA
from app.services import totobola_engine as engine
from app.services import trained_model
from app.services.elo_formula import ELO_HOME_ADVANTAGE

# Explanation per model kind; title and data source come from the domain spec.
_KIND_TEXT = {
    "poisson": {
        "descricao": (
            "Estima quantos golos cada equipa deve marcar (distribuição de Poisson) e soma as "
            "probabilidades de todos os resultados exatos (0-0, 1-0, 1-1, …) para obter 1, X e 2."
        ),
        "notas": [
            "Inclui um ajuste para resultados de poucos golos (Dixon–Coles), que melhora a previsão de empates.",
            "Escolhido por ter o menor erro (log loss) na validação cronológica entre os modelos testados.",
        ],
    },
    "elo": {
        "descricao": (
            "Converte a diferença de força Elo entre as duas equipas, mais o fator casa, em "
            "probabilidades de 1, X e 2, com parâmetros ajustados aos resultados históricos."
        ),
        "notas": [
            "Nos testes, juntar forma recente, confronto direto ou um modelo de golos não melhorou as "
            "previsões de forma relevante, por isso ficou o modelo mais simples.",
        ],
    },
}

_STATIC = {
    "elo-direto-v1": ModelCriteria(
        modelo="elo-direto-v1",
        titulo="Elo atual (sem histórico local)",
        descricao="Usa o rating Elo publicado para cada equipa e uma fórmula fixa para obter 1, X e 2.",
        criterios=[
            Criterion(nome="Força das equipas (Elo)", detalhe="Diferença de rating entre as duas equipas."),
            Criterion(nome="Fator casa", detalhe=f"+{ELO_HOME_ADVANTAGE:.0f} pontos Elo para a equipa da casa."),
        ],
        dados="eloratings.net (seleções) e clubelo.com (clubes)",
        notas=["O empate é mais provável quanto mais equilibradas forem as equipas."],
    ),
    "criterios-v0": ModelCriteria(
        modelo="criterios-v0",
        titulo="Estimativa sem dados (pouco fiável)",
        descricao=(
            "Usado quando não há histórico das equipas. Sem dados, a maioria dos critérios fica neutra "
            "e as probabilidades ficam próximas de um terço cada."
        ),
        criterios=[
            Criterion(nome="Forma recente (últimos 5 jogos)", peso=engine.WEIGHT_RECENT_FORM),
            Criterion(nome="Ranking UEFA do país", peso=engine.WEIGHT_UEFA_RANKING),
            Criterion(
                nome="Últimos 2 jogos na competição",
                peso=engine.WEIGHT_LAST2_COMPETITION,
                detalhe="Redistribuído pelos outros critérios quando não há 2 jogos.",
            ),
            Criterion(nome="Confronto direto", peso=engine.WEIGHT_H2H),
            Criterion(nome="Classificação no campeonato", peso=engine.WEIGHT_DOMESTIC_STANDING),
        ],
        notas=[f"A equipa da casa recebe um bónus de {engine.HOME_ADVANTAGE_BONUS:.0%} na força."],
    ),
}


def _trained_criteria(version: str) -> ModelCriteria | None:
    info = trained_model.model_info(version)
    if info is None:
        return None
    text = _KIND_TEXT[info["kind"]]
    criterios = [
        Criterion(id=criterion_id, nome=CRITERIA[criterion_id]["label"], peso=round(peso, 3))
        for criterion_id, peso in sorted(info["weights"].items(), key=lambda kv: -kv[1])
    ]
    periodo = f"{info['data_from']:%m/%Y} a {info['data_to']:%d/%m/%Y}"
    return ModelCriteria(
        modelo=version,
        titulo=info["title"],
        descricao=text["descricao"],
        criterios=criterios,
        dados=f"{info['source']} — {info['n_matches']} jogos, {periodo}",
        notas=[
            "O peso de cada critério é a parte da variação das probabilidades que se deve a ele, "
            "medida nos jogos mais recentes.",
            *text["notas"],
        ],
    )


def describe(versions: list[str]) -> list[ModelCriteria]:
    out = []
    for version in dict.fromkeys(versions):  # keep order, drop duplicates
        if version in trained_model.SPECS:
            described = _trained_criteria(version)
        else:
            described = _STATIC.get(version)
        if described:
            out.append(described)
    return out


ALL_MODELS = [*trained_model.SPECS, *_STATIC]
