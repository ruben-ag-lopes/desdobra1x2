# Plano — Análise de jogos: principais ligas internacionais e todas as ligas portuguesas

> **Estado:** as ligas do football-data.co.uk estão feitas (22 ligas com modelo e backtest). Falta tudo o que depende da API-Football: Liga 2, Liga 3, Campeonato de Portugal e taças.
>
> **Feito:**
> - Europa 1.ª fase: Championship, 2. Bundesliga, Serie B, LaLiga 2, Ligue 2, Eredivisie, Bélgica, Turquia, Grécia, Escócia (4 divisões) e mais três divisões inglesas.
> - Cada liga tem o seu modelo, escolhido no backtest.
> - O Totobola escolhe o modelo pela competição que a Santa Casa indica, e sem essa informação só usa uma liga se os dois clubes jogaram lá na época passada.
>
> **Por fazer:**
> - Fora da Europa (Brasil, Argentina, EUA, México, Japão) e a 2.ª fase da Europa (Suécia, Noruega, Dinamarca, Áustria, Suíça, Polónia): os ficheiros existem, mas têm outro formato e outra lógica de época (ano civil).
> - Tudo o que precisa da chave da API-Football. Complementa o `plano-competicoes.md` (separador "Futebol", mercados de golos, boletim). Este plano trata da **cobertura**: que ligas, de onde vêm os dados e como se modelam, reaproveitando o que já foi feito para o Totobola.

## Porque é prioritário
Os concursos do Totobola incluem muitas vezes jogos da **Liga 2, Liga 3 e Campeonato de Portugal**. Hoje esses jogos caem no método "pouco fiável" (probabilidades perto de 1/3). Cobrir estas ligas melhora já o Totobola, antes de existir o separador "Futebol".

## O que já existe e se reaproveita
- **Motor de previsão por "domínios"** (`app/services/trained_model.py`): cada liga é uma entrada `DomainSpec`, com dados, modelo e sinónimos. Hoje há seleções + P1, E0, SP1, I1, D1 e F1.
- **Backtest cronológico** (`app/research/backtest.py`): 1X2 e golos, escolhe o melhor modelo por liga.
- **Estado guardado** (`FeatureState`): previsões em milissegundos.
- **Reconhecimento de nomes** (sinónimos + aproximação), **pop-up de critérios** com pesos, **fixos e duplas**, **registo de previsões** (BigQuery; plano 4 para a base de dados).

## Cobertura proposta
### Portugal (todas as divisões nacionais)
| Divisão | Equipas | Fonte de dados proposta |
|---|---|---|
| Liga Portugal (1.ª) | 18 | football-data.co.uk (já em uso) |
| Liga Portugal 2 | 18 | API-Football |
| Liga 3 (FPF) | 24 (2 séries + fases finais) | API-Football; confirmar com o portal de resultados da FPF |
| Campeonato de Portugal (FPF) | 56 (4 séries) | API-Football (cobertura anunciada pelo fornecedor); confirmar com a FPF |
| Taça de Portugal / Taça da Liga | todas as divisões | API-Football |

- **API-Football:** o plano gratuito dá **100 pedidos/dia** com todas as competições. Chega para uma sincronização diária incremental: ~1 pedido por competição e dia, e o histórico carregado ao longo de alguns dias. Confirmar no endpoint `/leagues` os ids, as épocas disponíveis no plano gratuito e a cobertura real da Liga 3 e do Campeonato de Portugal.
- **Portal de resultados da FPF:** fonte oficial para validar a Liga 3 e o Campeonato de Portugal. Usar só se os termos do site permitirem a recolha automática.
- **zerozero.pt e Transfermarkt:** não usar. Os termos proíbem, em regra, a recolha automática.

### Internacional
| Grupo | Ligas | Fonte |
|---|---|---|
| Já cobertas | Premier League, LaLiga, Serie A, Bundesliga, Ligue 1 | football-data.co.uk |
| Europa, 1.ª fase de alargamento | Championship, 2.ª Bundesliga, Serie B, LaLiga 2, Ligue 2, Eredivisie, Bélgica, Turquia, Grécia, Escócia | football-data.co.uk (mesmo formato; próximos jogos em `fixtures.csv`) |
| Europa, 2.ª fase | Suécia, Noruega, Dinamarca, Áustria, Suíça, Polónia | football-data.co.uk, ficheiros "new" (confirmado: existem, com odds de fecho) |
| Fora da Europa | Brasil, Argentina, EUA (MLS), México, Japão | football-data.co.uk, ficheiros "new" (confirmado) |
| Competições europeias | Liga dos Campeões, Liga Europa, Conference League | API-Football ou football-data.org (chave gratuita) |

## Modelação
1. **Mesma receita por liga:** carregar o histórico, calcular o Elo cronológico, correr o backtest e escolher o modelo (Elo calibrado ou Poisson, com a regra "o mais simples quando a diferença é < 0,002"). É o processo já aplicado às 6 ligas atuais.
2. **Divisões inferiores portuguesas: um Elo português único, das 4 divisões.**
   - **Ligação entre divisões:** as subidas e descidas levam o rating da equipa consigo, e os jogos da Taça de Portugal entre divisões diferentes calibram a diferença de nível entre elas.
   - **Equipas novas** (vindas dos distritais) entram com o rating médio das equipas que desceram para essa divisão.
   - **Modelo e empates por divisão:** a vantagem de casa e a taxa de empates estimam-se por divisão, porque o empate é mais frequente nas divisões baixas.
   - **Modelo mais simples:** esperam-se menos dados por equipa e mais mudanças de plantel. O Elo calibrado deve ganhar nestas divisões; o backtest decide.
3. **Sem odds nas divisões baixas:** não há comparação com casas de apostas. A validação é contra as frequências históricas e o "motor anterior".
4. **Competições europeias e taças:** um Elo comum a todas as ligas europeias, ligado pelos jogos europeus, e só depois as taças. Validar apenas nos jogos de taça.
5. **Nomes das equipas:**
   - **Registo único de equipas:** o id do fornecedor mais um nome canónico.
   - **Tabela de sinónimos editável** (`team_aliases`, plano 4), com os nomes usados pela Santa Casa ("Vitória SC", "Belenenses", equipas B, …).
   - **Equipas B e sub-23:** tratadas como equipas diferentes da principal.

## Análise de cada jogo (o que a página do jogo mostra)
Tudo vem de dados que já calculamos ou que a API fornece:
- probabilidades 1X2 e palpite, com fixos e duplas como no Totobola;
- golos (golos esperados, mais/menos de 2,5, ambas marcam), **só nas ligas onde passaram o backtest**;
- forma: últimos 5 resultados de cada equipa (V/E/D), golos marcados e sofridos;
- Elo das duas equipas e a sua evolução na época (gráfico pequeno);
- confrontos diretos (últimos 5);
- classificação atual (API-Football);
- odds de referência das casas, onde existirem (ligas do football-data.co.uk).

## Fases
| Fase | Entrega | Efeito |
|---|---|---|
| 1 | **Liga 2, Liga 3, Campeonato de Portugal**: sincronização API-Football, Elo português das 4 divisões, backtest por divisão, sinónimos Santa Casa | O Totobola deixa de ter jogos "pouco fiáveis" nas divisões portuguesas |
| 2 | Alargamento europeu (1.ª fase) + fora da Europa | Mais jogos do Totobola e do separador "Futebol" cobertos |
| 3 | Página de análise de jogo + API `GET /api/futebol/jogos/{id}` | A análise do jogo fica disponível para o utilizador |
| 4 | Competições europeias e taças (Elo entre ligas) | Liga dos Campeões e Taça de Portugal passam a ter modelo |
| 5 | Tudo gravado na base de dados (plano 4) + tarefa diária | Acerto medido por liga e divisão, arranque rápido no Vercel |

## Medida de sucesso
- **Cobertura do Totobola:** % de jogos dos concursos que usam modelo treinado. Medir nos últimos concursos disponíveis. Objetivo ≥ 95%.
- **Por liga ou divisão:** log loss do modelo escolhido < frequências históricas e ≤ motor anterior.
- **Nas ligas com odds:** diferença para as casas de apostas medida e publicada nos critérios (sem esconder que as casas preveem melhor).

## Riscos e custos
- **API-Football:**
  - o plano gratuito pode limitar as épocas antigas: confirmar antes da fase 1;
  - se não chegar, há planos pagos (preço a confirmar, a página de preços não abriu na pesquisa).
  - Alternativa para Liga 2 e Liga 3: `football-data.org`, que só cobre a Primeira Liga no plano gratuito, portanto não resolve as divisões baixas.
- **Termos de uso das fontes:** confirmar se os dados podem ser usados num site público com donativos ou anúncios (football-data.co.uk, API-Football, FPF).
- **Qualidade nas divisões baixas:** menos jogos e muitas equipas novas por época. As previsões serão menos precisas do que na 1.ª divisão, e o pop-up deve dizê-lo (ex.: "Campeonato de Portugal: histórico curto").
