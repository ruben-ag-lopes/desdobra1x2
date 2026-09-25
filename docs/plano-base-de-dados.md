# Plano 4 — Base de dados: resultados reais e acerto das previsões

## Objetivo
Guardar cada previsão feita, juntar-lhe o resultado real quando o jogo acaba e medir continuamente o acerto de cada versão do modelo. Isto permite:
- saber se o modelo em produção continua bom (log loss, calibração, acerto do palpite);
- decidir com dados quando trocar de modelo (a versão nova só entra se for melhor);
- mostrar aos utilizadores uma página de transparência ("Acerto das previsões");
- guardar o artefacto do modelo treinado para arranques rápidos no Vercel (ver o plano 3, fase 2).

## Escolha da base de dados
**Recomendado: Postgres gerido (Neon ou Supabase, pelo Marketplace do Vercel).**
- Tem plano gratuito, é relacional (juntar previsões a resultados é um `JOIN` simples) e tem ligações próprias para funções serverless.

**BigQuery** (já ligado, opcional) fica para análises pesadas se um dia fizer falta. Não é boa escolha como base principal: escritas linha a linha lentas e custo por consulta.

## Modelo de dados (primeira versão)
```sql
-- Um jogo real, independentemente de onde veio
CREATE TABLE matches (
  id            BIGSERIAL PRIMARY KEY,
  competition   TEXT NOT NULL,          -- 'P1', 'selecoes', 'E0', 'CL', ...
  kickoff_date  DATE NOT NULL,
  home_team     TEXT NOT NULL,          -- nome normalizado (o do dataset de treino)
  away_team     TEXT NOT NULL,
  home_goals    SMALLINT,               -- NULL até haver resultado
  away_goals    SMALLINT,
  result        CHAR(1),                -- '1' | 'X' | '2'
  source        TEXT,                   -- de onde veio o resultado
  UNIQUE (competition, kickoff_date, home_team, away_team)
);

-- Concursos da Santa Casa e a ordem dos jogos no boletim
CREATE TABLE contests (
  id            BIGSERIAL PRIMARY KEY,
  game          TEXT NOT NULL,          -- 'totobola' | 'totobola_extra'
  concurso      TEXT NOT NULL,          -- '39/2026'
  contest_id    TEXT,                   -- id interno do site
  closes_at     TIMESTAMPTZ,
  draw_date     DATE,
  UNIQUE (game, concurso)
);
CREATE TABLE contest_matches (
  contest_id    BIGINT REFERENCES contests(id),
  position      SMALLINT NOT NULL,      -- 1..13 (14 = Super 14)
  match_id      BIGINT REFERENCES matches(id),
  PRIMARY KEY (contest_id, position)
);

-- Versões do modelo: parâmetros, dados de treino e métricas do backtest
CREATE TABLE model_versions (
  version       TEXT PRIMARY KEY,       -- 'selecoes-poisson-h2h-dc-v1'
  trained_at    TIMESTAMPTZ NOT NULL,
  data_from     DATE, data_to DATE, n_matches INT,
  backtest      JSONB,                  -- log_loss, rps, brier, ece...
  artifact      JSONB                   -- ratings Elo + coeficientes (arranque rápido)
);

-- Uma previsão mostrada na app (ou gerada pelo backtest)
CREATE TABLE predictions (
  id            BIGSERIAL PRIMARY KEY,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  match_id      BIGINT REFERENCES matches(id),
  contest_id    BIGINT REFERENCES contests(id),
  model_version TEXT REFERENCES model_versions(version),
  p_home REAL, p_draw REAL, p_away REAL,  -- probabilidades do modelo (antes de fixos/duplas)
  user_pick     TEXT,                     -- '', '1', '1X'... (escolha do utilizador)
  origin        TEXT NOT NULL DEFAULT 'app'  -- 'app' | 'backtest' | 'cron'
);
```
Notas:
- Guardam-se as probabilidades **do modelo**, antes de aplicar a dupla. Assim o acerto mede o modelo e não as escolhas dos utilizadores. As escolhas ficam em `user_pick`, para estatísticas à parte.
- **Duplicados:** o mesmo jogo pode ser calculado muitas vezes. Para as métricas usa-se a previsão mais recente antes do início do jogo, por `(match_id, model_version)`. Opção: guardar só uma previsão "oficial" por jogo, gerada pela tarefa agendada, em vez de uma por clique.
- **Sem dados pessoais:** não se guarda IP nem identificação do utilizador.

## Fluxos
1. **Previsão:** o `POST /desdobramento` cria ou encontra os `matches` e grava em `predictions`, em segundo plano, como já se faz hoje para o BigQuery.
2. **Resultados** (tarefa agendada diária, Vercel Cron):
   - seleções: o dataset `international_results` (atualizado com frequência);
   - ligas: os CSV do football-data.co.uk (atualizados 2×/semana);
   - Totobola: a página de resultados da Santa Casa (confirmar o URL) para os resultados oficiais do concurso, incluindo jogos anulados.
3. **Treino** (mesma tarefa): retreina, corre o backtest e grava em `model_versions` com o `artifact`. A app passa a usar a versão nova só se o log loss do backtest for melhor ou igual.
4. **Métricas** (vista SQL ou endpoint `/api/estatisticas`):
   - log loss, Brier, RPS e calibração por versão do modelo e por competição;
   - % de acerto do palpite (resultado mais provável);
   - Totobola: nº de jogos certos por concurso, e se as apostas geradas teriam tido prémio.

## Ligação dos nomes das equipas
- A chave de um jogo é `(competição, data, casa, fora)` com os nomes normalizados. Reutiliza-se o que já existe: `_plain()` e as tabelas de aliases em `trained_model.py`.
- Aliases novos passam para uma tabela `team_aliases (alias, competition, team)`, editável sem mexer em código.

## Implementação por passos
1. Interface `PredictionStore` em `app/storage/`. Implementações: `postgres` (nova), `bigquery` (atual) e `noop`. Escolha pela variável de ambiente (`DATABASE_URL` ou `GCP_PROJECT`).
2. Migrações SQL versionadas (pasta `backend/migrations/`; Alembic se o esquema crescer). Biblioteca: `psycopg[binary]` com a ligação "pooled" do Neon.
3. Gravar previsões e concursos a partir do `POST /desdobramento` e do `GET /draws`.
4. Tarefa de resultados + tarefa de treino (`POST /api/admin/cron`, protegida por um segredo `CRON_SECRET`, chamada pelo Vercel Cron).
5. Endpoint e página "Acerto das previsões", com gráfico de calibração e evolução do log loss.
6. Carregar o `artifact` do modelo no arranque em vez de treinar, o que resolve o arranque a frio no Vercel.

## Verificação
- Testes de integração com uma base Postgres local (Docker) ou uma branch do Neon.
- Criar uma previsão, inserir o resultado e confirmar que as métricas batem com `app/research/metrics.py`.
- Reprocessar a tarefa de resultados duas vezes e confirmar que não há duplicados (`UNIQUE` + `ON CONFLICT`).
