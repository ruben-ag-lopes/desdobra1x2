# Critérios do modelo antigo (`criterios-v0`) — defaults e afinações futuras

> Este ficheiro documenta o modelo de recurso "pouco fiável" (`criterios-v0`), usado só quando não há
> histórico das equipas (nem modelo treinado nem Elo publicado). É diferente do sistema de
> multiplicadores 0–200% do pop-up "Critérios e pesos" (ver [criterios.md](criterios.md)): aqui os
> 5 pesos são uma **partilha de 100%** — a soma nunca pode ultrapassar 100% e nenhum pode sozinho
> ultrapassar 100% (validado em `app/models.py`, `DesdobramentoRequest`).

## Defaults atuais (código: `app/services/totobola_engine.py`, `LEGACY_WEIGHTS_DEFAULT`)

| # | Critério | Id | Peso |
|---|---|---|---|
| 1 | Forma recente (últimos 5 jogos) | `forma` | 40% |
| 2 | Ranking UEFA do país | `ranking_uefa` | 30% |
| 3 | Últimos 2 jogos na competição (ignorado se houver menos de 2) | `ultimos2` | 15% |
| 4 | Confronto direto | `confronto_direto` | 10% |
| 5 | Classificação no campeonato doméstico | `classificacao` | 5% |

**Bónus de casa** (`HOME_ADVANTAGE_BONUS_DEFAULT`): +10% na força da equipa da casa, **exceto** se jogar em
casa emprestada — lista em `app/scrapers/loaned_venues.py` (Torreense, Casa Pia, Lourosa, União de Leiria,
Oliveirense, Belenenses, Sporting CP B). É um bónus aditivo, não faz parte da partilha de 100% acima.

Estes defaults foram confirmados por ti (mensagem de 2026-09-28) e já correspondiam exatamente ao que estava implementado — este ficheiro serve para não se perder essa validação e para anotar afinações futuras.

## API
- `GET /api/totobola/criterios?modelos=criterios-v0` devolve os 5 critérios com `id`, nome e peso atual.
- `POST /api/totobola/desdobramento` aceita `pesos_antigos: {id: peso}` (0–1, soma ≤ 1) e `bonus_casa` (0–1, opcional). Omitidos = defaults acima. Só afeta jogos sem modelo treinado nem Elo.

## O teu texto original (2026-09-28), para referência de afinações futuras
> 1º critério: o momento de forma de resultados atual das equipas (1º critério) (40%)
> 2º critério: uma ponderação entre o ranking UEFA do país (ranking elevado tem maior probabilidade de vencer, especialmente maior nos 3 primeiros) (30%)
> 3º critério: os últimos 2 resultados na competição, se houver menos de 2 jogos ignora (15%)
> 5ª critério: o confronto direto das equipas nos últimos 5 anos (10%)
> 6ª: a classificação no campeonato doméstico (restante %)
> A equipa da casa começa sempre com 10% de vantagem, exceto se não jogar no seu estádio próprio mas sim em casa emprestada — exemplos: Torreense, Casa Pia, Lourosa.

Notas para quando quiseres afinar:
- O "ranking elevado tem maior probabilidade... especialmente maior nos 3 primeiros" sugere uma curva **não linear** (ex.: top-3 vale desproporcionalmente mais do que a diferença entre o 20º e o 23º). Hoje `uefa_ranking.rank_to_score` é linear; ver `app/scrapers/uefa_ranking.py` se quiseres testar uma curva côncava.
- O confronto direto hoje olha aos **últimos 5 jogos** (`manual_h2h`, até 5), não aos últimos 5 anos. Se quiseres mesmo "últimos 5 anos" (podem ser mais ou menos de 5 jogos), é uma mudança separada em `_h2h_score` e no formulário.
- Antes de mudar qualquer peso, considera validar no backtest se a mudança melhora ou piora o acerto — este modelo de recurso não tem backtest próprio hoje (só é usado quando não há dados suficientes para os modelos treinados, que são validados em `docs/backtests/`).
