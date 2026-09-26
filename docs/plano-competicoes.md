# Plano 6 — Jogos das principais competições

## Objetivo
Um novo separador **"Futebol"** que aplica os mesmos princípios do Totobola a qualquer jogo das principais competições:
- **pesquisar** jogos por equipa, competição ou data;
- **prever o vencedor:** 1X2 com o palpite e o pop-up de critérios e pesos;
- **prever golos:** golos esperados, mais/menos de 2,5, ambas marcam e resultados exatos mais prováveis;
- **sugerir apostas:** simples, duplas e um "boletim" com vários jogos, com fixos e duplas como no Totobola.

## Competições (por fases)
| Fase | Competições | Porquê |
|---|---|---|
| 1 | Primeira Liga, Premier League, LaLiga, Serie A, Bundesliga, Ligue 1 | Têm histórico e próximos jogos gratuitos no football-data.co.uk. |
| 2 | Liga 2, Eredivisie, Bélgica, Turquia, Grécia, Escócia, 2.as divisões | Mesma fonte: o ficheiro de próximos jogos já cobre 22 ligas. |
| 3 | Liga dos Campeões, Liga Europa, Conference League | Precisam de uma força comparável entre ligas (ver abaixo) e de outra fonte de calendário. |
| — | Seleções | Já existe o modelo; falta o calendário (Liga das Nações, qualificações). |

## Dados
- **Próximos jogos (pesquisa):** `https://www.football-data.co.uk/fixtures.csv`.
  - Confirmado: 22 ligas, com data, hora e odds de várias casas. Atualiza algumas vezes por semana.
- **Histórico para treino:** os CSV por época do football-data.co.uk, já usados para a Primeira Liga (`app/research/data.py`, `load_league(<código>)`).
- **Competições europeias e horários exatos:** API football-data.org (chave gratuita, 10 pedidos/min). Cobre a Liga dos Campeões e as principais ligas. O histórico das taças europeias pode vir do openfootball (domínio público, a confirmar).
- **Força entre ligas:** um Elo único para todos os clubes, ligado pelos jogos europeus. Assim o Benfica de Portugal e o Inter de Itália ficam na mesma escala. O clubelo.com serve de referência quando estiver em funcionamento (esteve em baixo nos nossos testes).

## Modelo
1. **Generalizar o `trained_model.py`**: hoje tem dois "domínios" (seleções e Primeira Liga). Passa a ter um por liga, com a mesma função de treino, e um domínio europeu com o Elo entre ligas.
2. **Escolha automática por liga:** o backtest cronológico (`app/research/backtest.py`) corre para cada liga, e fica o modelo com menor log loss (Elo calibrado, Poisson, com ou sem H2H e Dixon–Coles), como fizemos para a Primeira Liga e as seleções.
3. **Golos:** o modelo Poisson já calcula os golos esperados e a grelha de resultados exatos. Basta expor:
   - golos esperados de cada equipa;
   - P(mais de 2,5) e P(menos de 2,5);
   - P(ambas marcam);
   - os 3 resultados exatos mais prováveis.

   Cada mercado novo tem de ser validado no backtest (log loss próprio) antes de aparecer na app.
4. **Artefacto pré-calculado:** a tarefa diária (planos 3 e 4) calcula as previsões de todos os próximos jogos. A pesquisa passa a ser uma leitura rápida, sem treinar nada no momento.

### Resultados do backtest (25/09/2026)
Teste cronológico nas duas últimas épocas de cada liga (desde agosto de 2025), com os modelos reajustados de 4 em 4 semanas. Log loss (quanto mais baixo, melhor):

| Liga | Frequências | Motor anterior | Melhor modelo nosso | Casas de apostas |
|---|---|---|---|---|
| Primeira Liga (P1) | 1,086 | 0,942 | **0,930** Elo calibrado | 0,918 |
| Premier League (E0) | 1,090 | 1,041 | **1,029** Poisson+H2H+Dixon–Coles | 1,017 |
| LaLiga (SP1) | 1,054 | 0,992 | **0,986** Poisson+H2H | 0,963 |
| Serie A (I1) | 1,083 | 1,022 | **0,991** Elo calibrado | 0,975 |
| Bundesliga (D1) | 1,065 | 0,974 | **0,966** Poisson+H2H+Dixon–Coles | 0,949 |
| Ligue 1 (F1) | 1,069 | 1,014 | **1,006** Elo calibrado | 0,982 |

Conclusões:
- **O que já funciona bem:** em todas as ligas os modelos treinados batem as frequências históricas e o motor anterior. O mesmo código de treino serve para todas, por isso generalizar é seguro.
- **Diferenças pequenas:** entre os nossos modelos a diferença é ≤ 0,004, pouco. Escolher automaticamente por liga, mas com preferência pelo mais simples (Elo calibrado) quando a diferença for mínima.
- **Casas de apostas continuam à frente:** ganham em todas as ligas, por 0,012 a 0,024. Confirma a regra de não anunciar "apostas de valor" (ver abaixo).
- **Próxima melhoria a testar:** usar as odds de abertura como variável adicional ("combinar com o mercado") e medir se o log loss desce.

Repetir com `python -m app.research.backtest --league <código>`.

### Backtest dos mercados de golos (25/09/2026)
Mesmo teste, com `--goals`. Log loss de "mais de 2,5 golos" e de "ambas marcam". A referência "freq." é prever sempre a percentagem histórica da liga:

| Liga | +2,5: freq. → melhor modelo nosso | +2,5: casas | Ambas marcam: freq. → nosso |
|---|---|---|---|
| Primeira Liga | 0,695 → **0,674** | 0,673 | 0,693 → **0,690** |
| Premier League | **0,688** → 0,692 | 0,683 | 0,687 → 0,686 |
| LaLiga | 0,697 → **0,680** | 0,665 | **0,690** → 0,692 |
| Serie A | 0,697 → 0,696 | 0,698 | 0,704 → **0,695** |
| Bundesliga | 0,649 → **0,636** | 0,634 | **0,666** → 0,667 |
| Ligue 1 | 0,692 → 0,690 | 0,666 | 0,696 → 0,696 |
| Seleções | 0,696 → **0,672** | — | 0,687 → **0,677** |

Conclusões:
- **Ganho modesto:** o modelo de golos só melhora de forma clara em parte das ligas e mercados, e as casas de apostas continuam melhores quase sempre.
- **O que não ajuda:** o confronto direto e o ajuste Dixon–Coles não ajudam nos golos. O Dixon–Coles não pode mudar o "+2,5", porque só redistribui a probabilidade entre 0-0, 1-0, 0-1 e 1-1.
- **Regra para a app:** um mercado só aparece numa liga se o modelo ganhar à frequência histórica por pelo menos 0,002 de log loss. Onde não ganhar, mostra-se a percentagem histórica da liga, identificada como tal.
  - Com os números de hoje, "+2,5" aparece em P1, SP1, D1, F1 e seleções.
  - "Ambas marcam" aparece em P1, I1 e seleções.
- **Resultados exatos e golos esperados** saem da mesma grelha de resultados. Mostrar só como informação, sem "sugestão".

Repetir com `python -m app.research.backtest --league <código> --goals`.

## Sugestão de apostas: como a fazer de forma honesta
- **Ponto de partida:** no backtest da Primeira Liga o nosso modelo teve log loss **0,930**, contra **0,918** das odds das casas de apostas. As casas de apostas preveem melhor. Por isso **não** anunciamos "apostas de valor" até o modelo bater as odds de fecho num backtest com amostra suficiente e retorno positivo.
- **O que sugerimos na fase 1:**
  - resultado mais provável e nível de confiança (alto, médio, baixo pela margem entre o 1.º e o 2.º resultado);
  - "dupla recomendada" nos jogos equilibrados;
  - probabilidades das casas (retiradas das odds do `fixtures.csv`, sem a margem) ao lado das nossas, como referência.
- **Boletim:** o utilizador junta jogos de várias competições e escolhe fixos e duplas. A app mostra a probabilidade de acertar tudo, que é o produto das probabilidades.
- **Jogo responsável:** +18, sem links para casas de apostas (salvo decisão do plano 5) e aviso de que nenhuma previsão garante ganhos.

## API (backend)
| Endpoint | Descrição |
|---|---|
| `GET /api/futebol/competicoes` | Lista de competições disponíveis. |
| `GET /api/futebol/jogos?competicao=&q=&de=&ate=` | Pesquisa de próximos jogos (texto sem acentos, por equipa). |
| `GET /api/futebol/jogos/{id}` | 1X2, golos, resultados exatos, odds de referência e modelo. |
| `POST /api/futebol/boletim` | Probabilidade conjunta de um conjunto de escolhas (fixos/duplas). |
| `GET /api/totobola/criterios` | Reutilizado para o pop-up de critérios. |

## Frontend
- **Separador "Futebol":**
  - caixa de pesquisa com sugestões;
  - filtros por competição e data (hoje, fim de semana, 7 dias);
  - lista de jogos agrupada por dia e competição.
- **Cartão do jogo:**
  - barras 1/X/2 com as nossas probabilidades e as das casas;
  - golos esperados;
  - mais/menos de 2,5 e ambas marcam;
  - 3 resultados exatos;
  - palpite e confiança;
  - botões 1/X/2 para juntar ao boletim (com os mesmos fixos e duplas do Totobola).
- **Painel "Boletim"** (lateral no computador, fundo do ecrã no telemóvel): jogos escolhidos, probabilidade conjunta, copiar.
- **Reutilizar:** `CopyButton`, `CriteriaDialog`, os botões 1/X/2 (`fix-toggle`) e o tema por jogo (plano 7), com uma cor própria para o separador.

### Backtest das 16 ligas novas (resultados brutos em `docs/backtests/`)
| Liga | Frequências | Motor anterior | Nosso (modelo) | Casas | Golos: modelo ganha à frequência em |
|---|---|---|---|---|---|
| Championship (E1) | 1,082 | 1,084 | **1,061** Elo | 1,043 | — |
| League One (E2) | 1,070 | 1,053 | **1,044** Elo | 1,027 | ambas marcam |
| League Two (E3) | 1,078 | 1,062 | **1,046** Elo | 1,027 | — |
| National League (EC) | 1,068 | 1,030 | **1,006** Elo | 0,994 | +2,5 e ambas marcam |
| Premiership (SC0) | 1,073 | 0,989 | **0,979** Elo | 0,971 | +2,5 e ambas marcam |
| Scottish Championship (SC1) | 1,091 | 1,068 | **1,059** Elo | 1,053 | — |
| Scottish League One (SC2) | 1,082 | 1,068 | **1,052** Elo | 1,008 | +2,5 |
| Scottish League Two (SC3) | 1,081 | 1,089 | **1,069** Poisson | 1,058 | +2,5 e ambas marcam |
| 2. Bundesliga (D2) | 1,067 | 1,069 | **1,052** Elo | 1,035 | — |
| Serie B (I2) | 1,071 | 1,025 | 1,027 Elo | 1,014 | +2,5 |
| LaLiga 2 (SP2) | 1,080 | 1,063 | **1,055** Poisson | 1,029 | +2,5 |
| Ligue 2 (F2) | 1,105 | 1,117 | **1,082** Elo | 1,061 | — |
| Eredivisie (N1) | 1,081 | 0,995 | **0,982** Elo | 0,970 | +2,5 |
| Liga belga (B1) | 1,078 | 1,040 | **1,014** Elo | 1,000 | — |
| Liga turca (T1) | 1,085 | 1,022 | **1,011** Poisson | 0,979 | +2,5 |
| Liga grega (G1) | 1,084 | 0,975 | **0,962** Elo | 0,943 | +2,5 |

Conclusões:
- Em 15 das 16 ligas o modelo treinado melhora o motor anterior. A exceção é a Serie B (1,027 contra 1,025, empate técnico).
- As casas de apostas continuam à frente em todas.
- Nas divisões baixas os mercados de golos quase nunca batem a média da liga, e a app mostra então a média, identificada como tal.

## Passos
1. ✅ Carregamento genérico de ligas e backtest por liga (tabela acima).
2. 🔨 Domínios por liga no `trained_model`: **feito para o 1X2** nas 6 ligas (P1, E0, SP1, I1, D1, F1). O Totobola já os usa quando aparecem jogos destas ligas. As previsões saem de um estado guardado (0,03 s por cálculo). Mercados de golos já validados no backtest (tabela acima). Falta expô-los na API, com a regra de só mostrar os que ganham.
3. ✅ Pesquisa de jogos (`fixtures.csv`) com nomes normalizados e sinónimos (testes em `tests/test_futebol.py`).
4. ✅ Endpoints `GET /api/futebol/competicoes` e `/jogos` + separador "Futebol": lista por dia, cartão com 1X2 nosso e das casas, golos, resultados prováveis e boletim com a probabilidade conjunta. Falta `GET /jogos/{id}` e `POST /boletim` (hoje o boletim é calculado no navegador).
5. Elo entre ligas + competições europeias (fase 3).
6. Registo das previsões e resultados na base de dados (plano 4) para medir o acerto por liga e por mercado.

## Verificação
- **Backtest por liga:** o modelo escolhido tem log loss menor que as frequências históricas e menor ou igual ao motor anterior. Mostrar a comparação com as casas de apostas.
- **Golos:** calibração de mais/menos 2,5 e de ambas marcam, com tabelas por decil.
- **Pesquisa:** "benfica", "Benfica", "SL Benfica" e "benfíca" encontram o mesmo jogo.
- **Boletim:** a probabilidade conjunta é igual ao produto das probabilidades, confirmado com um teste.
