# desdobra1X2

Ferramenta local de **análise e geração de apostas** para os jogos da Santa Casa
(jogossantacasa.pt). Não existe API oficial da Santa Casa, por isso esta
plataforma **não submete apostas automaticamente** — apenas calcula/gera
sugestões que introduzes manualmente no site oficial.

## Aviso importante

- Sem integração de submissão automática de apostas — seria contra os termos
  de serviço do site.
- O calendário de concursos do Totobola (nº do concurso, prazo de apostas,
  data de sorteio) é obtido automaticamente por scraping do site oficial.
- Os **jogos de cada concurso** do Totobola são obtidos automaticamente do
  detalhe do concurso no site oficial; se falhar, cola-os (um por linha).
- Totoloto, Euromilhões e EuroDreams mostram o próximo sorteio (concurso,
  fecho de apostas, data) lido da página de cada jogo.
- Os **dados estatísticos das equipas** (forma recente, últimos jogos na
  competição, classificação doméstica) tentam ser obtidos automaticamente via
  [football-data.org](https://www.football-data.org) (API gratuita, cobre as
  12 principais competições europeias). Fora dessas competições, ou sem API
  key configurada, introduz os dados manualmente no formulário.
- Confrontos diretos (H2H) e o ranking UEFA por país usam listas geridas
  localmente (`app/scrapers/uefa_ranking.py`), a atualizar periodicamente.

## Estrutura

```
backend/    FastAPI (Python) — scraping, motor de probabilidades, geradores de números
frontend/   React + Vite + TypeScript — uma aba por jogo
```

## Como correr localmente

Precisas de dois terminais (um para o backend, outro para o frontend) — ambos
ficam a correr enquanto usas a aplicação.

### Backend (terminal 1)

PowerShell:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Opcional, para dados estatísticos automáticos de equipas:
$env:FOOTBALL_DATA_API_KEY = "xxxxx"   # cria conta grátis em football-data.org

uvicorn app.main:app --reload --port 8000
```

Bash/Git Bash:

```bash
cd backend
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt

export FOOTBALL_DATA_API_KEY=xxxxx   # opcional

uvicorn app.main:app --reload --port 8000
```

Confirma que está a correr em http://localhost:8000/api/health (deve devolver
`{"status":"ok"}`). Swagger/documentação interativa em http://localhost:8000/docs

### Frontend (terminal 2)

```powershell
cd frontend
npm install    # só da primeira vez
npm run dev
```

Abre **http://localhost:5173** no browser.

### Parar

`Ctrl+C` em cada terminal. Se um servidor ficar preso numa porta, mata o
processo que a está a usar (ex: `Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process` em PowerShell, ou `lsof -ti:8000 | xargs kill` em Bash).

## Jogos suportados

- **Totobola / Totobola Extra**: os jogos do concurso ativo carregam
  sozinhos; podes fixar o resultado de qualquer jogo (1/X/2), que entra igual
  em todas as apostas, e o desdobramento é feito só nos restantes. As
  probabilidades vêm do melhor modelo disponível para cada jogo (ver abaixo).
- **Totoloto / Euromilhões / EuroDreams**: gerador de números aleatórios
  dentro das regras oficiais de cada jogo (sem histórico de sorteios).

## Modelo de previsão 1X2

Ordem de preferência por jogo (`backend/app/services/totobola_engine.py`):

1. **Modelo treinado com histórico** (`app/services/trained_model.py`):
   - seleções: Poisson (Elo + golos recentes + H2H) com correção Dixon–Coles,
     treinado com resultados internacionais desde há 10 anos
     ([martj42/international_results](https://github.com/martj42/international_results));
   - Primeira Liga, Premier League, LaLiga, Serie A e Ligue 1: diferença de
     Elo com logit ordenado; Bundesliga: Poisson + H2H + Dixon–Coles. Cada liga
     usa o modelo que ganhou o seu backtest (8 épocas de
     [football-data.co.uk](https://www.football-data.co.uk); resultados em
     `docs/plano-competicoes.md`). Os nomes das equipas em português
     ("Bayern Munique", "Inter Milão"…) são reconhecidos por sinónimos.
   Os dados ficam em `backend/data/` (ou em `DATA_DIR`). Cada liga só é
   carregada quando um jogo precisa dela e é retreinada a cada 12 h.
2. Elo atual de [eloratings.net](https://www.eloratings.net) / clubelo.com.
3. Critérios antigos (pouco fiável — a app assinala-o).

### Backtest (validação cronológica)

Cada modelo é reajustado de 4 em 4 semanas usando só jogos anteriores e prevê o
bloco seguinte; as métricas são calculadas só no período de teste.

```powershell
cd backend
.\venv\Scripts\python -m app.research.backtest --league P1            # Primeira Liga
.\venv\Scripts\python -m app.research.backtest --international --seasons 10
.\venv\Scripts\python -m app.research.backtest --league P1 --calibration  # tabelas de calibração
.\venv\Scripts\python -m unittest tests.test_research                     # inclui teste de "sem look-ahead"
```

Um passo novo (forma, H2H, Dixon–Coles, …) só entra no modelo da app se baixar
o log loss no backtest.

### BigQuery (opcional)

Instala o extra (`pip install -r requirements-optional.txt`) e define
`GCP_PROJECT` e `BQ_DATASET` (credenciais via
`gcloud auth application-default login`). A app passa a guardar cada previsão
mostrada na tabela `predictions` (concurso, data, equipas, probabilidades,
resultado fixo, versão do modelo) e `backtest ... --bigquery` guarda todas as
previsões do teste em `backtest_predictions`. Sem as variáveis não escreve nada.
