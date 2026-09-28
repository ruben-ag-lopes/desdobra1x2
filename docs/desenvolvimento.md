# Desenvolvimento

Guia para quem quer correr, testar ou alterar o desdobra1X2. Para o método de previsão, ver [criterios.md](criterios.md).

## Estrutura

```
backend/    FastAPI (Python): scraping, modelos de previsão, backtest, geradores de números
frontend/   React + Vite + TypeScript: um separador por jogo, mais "Futebol"
docs/       planos, critérios, tutorial e resultados dos backtests (docs/backtests/)
```

## Correr localmente

Precisas de dois terminais (um para o backend, outro para o frontend), ambos a correr enquanto usas a aplicação.

### Backend

PowerShell:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Bash/Git Bash:

```bash
cd backend
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Confirma em http://localhost:8000/api/health (deve devolver `{"status":"ok"}`). A documentação interativa da API está em http://localhost:8000/docs

### Frontend

```powershell
cd frontend
npm install    # só da primeira vez
npm run dev
```

Abre **http://localhost:5173**.

### Parar

`Ctrl+C` em cada terminal. Se um servidor ficar preso numa porta, mata o processo que a usa (PowerShell: `Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process`).

## Testes

```powershell
cd backend
.\venv\Scripts\python -m unittest discover -s tests
cd ..\frontend
npx tsc -b
npx oxlint src
```

Os testes incluem a verificação de que os modelos **não usam informação do futuro** (`tests/test_research.py`).

## Backtest (validação cronológica)

Cada modelo é reajustado de 4 em 4 semanas usando só jogos anteriores e prevê o bloco seguinte. As métricas são calculadas só no período de teste.

```powershell
cd backend
.\venv\Scripts\python -m app.research.backtest --league P1                    # 1X2 de uma liga
.\venv\Scripts\python -m app.research.backtest --league P1 --goals            # mercados de golos
.\venv\Scripts\python -m app.research.backtest --international --seasons 10   # seleções
.\venv\Scripts\python -m app.research.backtest --league P1 --calibration      # tabelas de calibração
.\venv\Scripts\python -m app.research.backtest --league P1 --json saida.json  # guardar resultados
```

Um passo novo (forma, confronto direto, Dixon–Coles, …) só entra na app se baixar o log loss no backtest. Os resultados de todas as ligas estão em `docs/backtests/`.

## Como acrescentar uma liga
1. Corre o backtest da liga (1X2 e `--goals`) e vê que modelo ganha.
2. Em `backend/app/services/trained_model.py`, acrescenta uma linha a `LEAGUES` com `_league(código, nome, "elo" ou "poisson", nomes da competição, mercados de golos que ganharam)`.
3. Se os nomes das equipas diferirem dos do ficheiro de dados, acrescenta sinónimos a `_CLUB_ALIASES`.
4. Corre os testes.

## Variáveis de ambiente

| Variável | Onde | Para quê |
|---|---|---|
| `CORS_ORIGINS` | backend | origens permitidas, separadas por vírgula (por omissão `http://localhost:5173`) |
| `DATA_DIR` | backend | onde guardar os CSV descarregados (por omissão `backend/data/`) |
| `FOOTBALL_DATA_API_KEY` | backend | dados de equipas via football-data.org (opcional) |
| `GCP_PROJECT`, `BQ_DATASET` | backend | guardar previsões no BigQuery (opcional) |
| `VITE_API_URL` | frontend | endereço da API quando não é o mesmo domínio |
| `VITE_BUYMEACOFFEE_URL` | frontend | ligação do botão de apoio (`frontend/.env.example`) |

## BigQuery (opcional)
Instala o extra (`pip install -r requirements-optional.txt`) e define `GCP_PROJECT` e `BQ_DATASET` (credenciais via `gcloud auth application-default login`). A app passa a guardar cada previsão mostrada na tabela `predictions` (concurso, data, equipas, probabilidades, resultado fixo, versão do modelo), e `backtest ... --bigquery` guarda todas as previsões do teste em `backtest_predictions`. Sem as variáveis não escreve nada.

## Publicação
Ver [plano-publicacao-vercel.md](plano-publicacao-vercel.md).
