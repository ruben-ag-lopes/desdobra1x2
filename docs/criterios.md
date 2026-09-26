# Como o desdobra1X2 calcula as previsões

> **Aviso:** as previsões são meramente estatísticas e **não garantem qualquer resultado**. Nos nossos testes com jogos passados, as casas de apostas previram melhor do que este modelo em todas as ligas. Usa-as como referência e joga com responsabilidade (+18).

## Em resumo
1. Para cada equipa mantemos uma **nota de força** (rating Elo) que sobe quando ganha e desce quando perde, e a **forma recente** (golos marcados e sofridos nos últimos 8 jogos).
2. Com isso estimamos **quantos golos cada equipa deve marcar** e, a partir daí, a probabilidade de cada resultado exato (1-0, 1-1, 2-1, …).
3. Somando os resultados exatos em que ganha a casa, empata ou ganha o visitante, obtemos as probabilidades de **1, X e 2**.
4. Cada liga tem o seu modelo, escolhido por ser o que **menos falhou** em jogos passados, testados por ordem cronológica e só com informação anterior a cada jogo.
5. Quando não há histórico das equipas, usamos um método de recurso **pouco fiável**, assinalado com "*" na app.

Cada critério mostrado no pop-up "Critérios e pesos" tem um peso: a parte da variação das probabilidades que se deve a esse critério, medida nos jogos mais recentes da liga. Podes alterá-los no mesmo pop-up (ver [Critérios personalizados](#critérios-personalizados)).

## 1. De onde vêm os dados
| Uso | Fonte | Histórico |
|---|---|---|
| Ligas de clubes | [football-data.co.uk](https://www.football-data.co.uk) (resultados e odds) | últimas 8 épocas |
| Seleções | [martj42/international_results](https://github.com/martj42/international_results) | últimos 10 anos |
| Próximos jogos do separador "Futebol" | football-data.co.uk, `fixtures.csv` | atualizado algumas vezes por semana |
| Concursos e jogos do Totobola | site oficial da Santa Casa | no momento |
| Recurso para clubes/seleções sem histórico | eloratings.net e clubelo.com | ratings publicados |

Os ficheiros ficam em cache: 12 horas para os que ainda mudam (época atual), e as previsões usam um modelo já treinado guardado em memória durante 12 horas.

## 2. Rating Elo (força de cada equipa)
Todas as equipas começam com **1500** pontos. Depois de cada jogo, o vencedor ganha pontos e o vencido perde os mesmos, na proporção da surpresa do resultado:

- **Resultado esperado da casa** = `1 / (1 + 10^(−(Elo casa − Elo fora + vantagem) / 400))`.
- **Vantagem de casa:** 60 pontos nos clubes, 100 nas seleções, 0 em campo neutro.
- **Variação** = `K × multiplicador × (resultado − esperado)`, com resultado 1, 0,5 ou 0.
  - `K` = 25 nos clubes e 40 nas seleções (os jogos das seleções são menos frequentes, por isso cada um pesa mais).
  - O multiplicador dá mais peso a goleadas: 1 (diferença de 0 ou 1 golo), 1,5 (2 golos) e `(11 + diferença) / 8` (3 ou mais).
- **Início de época** (clubes): cada rating recua 25% para os 1500. Isto reflete transferências e a entrada de equipas promovidas.

Código: `app/research/features.py`, `FeatureState`.

## 3. Forma recente e confronto direto
- **Ataque recente:** média de golos marcados nos últimos 8 jogos da equipa, em qualquer campo.
- **Defesa recente:** média de golos sofridos nos últimos 8 jogos.
- **Confronto direto:** média da diferença de golos (do ponto de vista da casa) nos últimos 5 jogos entre as duas equipas. É 0 se nunca se defrontaram.
- Sem histórico, usamos 1,3 golos por jogo (a média típica).
- Só se prevê um jogo se as duas equipas têm **pelo menos 5 jogos** anteriores na liga.

## 4. Os dois modelos
### Elo calibrado (modelo mais simples)
Converte a diferença de Elo em probabilidades por um *logit ordenado*, com três parâmetros ajustados aos resultados históricos da liga (peso do Elo, peso do fator casa e largura da zona do empate). Não usa golos nem forma.

### Poisson (modelo de golos)
- Estima os golos esperados da casa (λ) e do visitante (μ) por regressão de Poisson com o Elo, o fator casa, o ataque da equipa, a defesa do adversário e, opcionalmente, o confronto direto.
- Calcula a probabilidade de cada resultado exato de 0-0 a 10-10.
- **Ajuste Dixon–Coles (opcional):** corrige a probabilidade de 0-0, 1-0, 0-1 e 1-1, que a distribuição de Poisson costuma estimar mal. O parâmetro ρ é ajustado aos dados.
- Somando a grelha obtemos P(1), P(X) e P(2), **mais de 2,5 golos**, **ambas marcam** e os resultados mais prováveis.

Código: `app/research/models.py`.

## 5. Que modelo é usado em cada liga
Para cada liga, o backtest compara os modelos e fica com o de menor erro. Se a diferença for inferior a 0,002 de log loss, fica o mais simples (Elo calibrado). As tabelas completas estão em [plano-competicoes.md](plano-competicoes.md) e os dados brutos em `docs/backtests/`.

**No Totobola**, a competição que a Santa Casa indica para cada jogo decide o modelo. Se não indicar, usa-se a primeira liga em que as duas equipas jogaram na última época, para os clubes promovidos ou despromovidos serem previstos na divisão onde jogam agora. Se nenhum modelo conhecer as equipas, recorre-se ao Elo publicado e, por fim, aos critérios antigos.

**Nomes das equipas:** as equipas são reconhecidas por uma tabela de sinónimos (ex.: "Sporting" → "Sp Lisbon", "Bayern Munique" → "Bayern Munich") e por aproximação de texto.

## 6. Critérios antigos (recurso "pouco fiável")
Usados só quando não há histórico. Combinam, com estes pesos: forma recente (40%), ranking UEFA do país (30%), últimos 2 jogos na competição (15%), confronto direto (10%) e classificação no campeonato (5%), com um bónus de 10% à equipa da casa. Sem dados, quase tudo fica neutro e as probabilidades ficam perto de um terço cada.

## 7. Como se calculam os pesos do pop-up
Para cada critério, neutralizamos o seu efeito (por exemplo, pomos o Elo das duas equipas iguais) e medimos o quanto mudam as probabilidades, em média, nos 1000 jogos mais recentes. Os valores são normalizados para somarem 100%. Critérios abaixo de 0,5% não aparecem.

Um critério com peso alto **não** quer dizer que acerte mais, só que move mais as probabilidades.

## 8. Fixos, duplas e desdobramento
- **Fixo:** o resultado escolhido entra em todas as apostas.
- **Dupla:** escolhes dois resultados. O modelo calcula 1, X e 2 e depois reparte a probabilidade do resultado excluído pelos dois escolhidos, na proporção de cada um. Exemplo: 33% / 28% / 38% com dupla 1X fica 54% / 46%.
- **Desdobramento:** para N apostas, cada jogo recebe cada resultado um número de vezes proporcional à sua probabilidade (arredondando pelos maiores restos).
  - Se o resultado mais provável tem menos de 50%, os dois mais prováveis recebem sempre pelo menos uma aposta.
  - Numa dupla, os dois resultados escolhidos aparecem sempre pelo menos uma vez (com 2 ou mais apostas).
  - As sequências de cada jogo são rodadas para as apostas não ficarem todas iguais.

Código: `app/services/totobola_engine.py`.

## 9. Golos
"Mais de 2,5 golos" e "ambas marcam" vêm da grelha de resultados do modelo de Poisson. **Só mostramos o valor do modelo nas ligas em que, no backtest, ele bateu a média histórica da liga** por pelo menos 0,002 de log loss. Nas outras, mostramos essa média, identificada como "média da liga".

## 10. Como validámos
- **Backtest cronológico:** o modelo é reajustado de 4 em 4 semanas e cada jogo de teste só vê dados anteriores. Testámos as duas últimas épocas de cada liga.
- **Métricas:** log loss (a principal, quanto mais baixo melhor), RPS, Brier e erro de calibração.
- **Referências:** prever sempre as frequências históricas, o método anterior da app e as odds das casas de apostas (sem a margem).
- **Resultado principal:** os modelos treinados batem as frequências e o método anterior em quase todas as ligas, mas **ficam atrás das casas de apostas em todas**, por 0,006 a 0,05 de log loss.

Para repetir:
```
cd backend
python -m app.research.backtest --league P1
python -m app.research.backtest --league P1 --goals
python -m app.research.backtest --international
```

## 11. Limitações
- Não sabemos de lesões, castigos, motivação, mudanças de treinador nem do tempo.
- Nas divisões baixas há menos jogos por equipa e mais mudanças de plantel, por isso as previsões são menos precisas.
- As divisões portuguesas abaixo da 1.ª Liga, as taças e as competições europeias ainda não têm modelo (ver [plano-ligas.md](plano-ligas.md)).
- Os mercados de golos têm ganho modesto sobre a média da liga.

## Critérios personalizados
No pop-up "Critérios e pesos", cada critério tem um cursor de 0% a 200%:
- **100%** é o modelo predefinido, sem alterações.
- **0%** ignora o critério: as suas variáveis passam para o valor "sem informação".
- **200%** duplica o efeito do critério.

Formalmente, cada variável `x` do critério passa a `neutro + m × (x − neutro)`, onde `m` é o multiplicador e o valor neutro é a média dos jogos de treino (ou 0 para o Elo, o fator casa e o confronto direto). Os multiplicadores aplicam-se a todos os jogos com modelo treinado. A escolha fica guardada no teu navegador, e "Repor predefinidos" volta sempre ao modelo original.

**Os critérios alterados não foram validados.** Os predefinidos são os que tiveram o menor erro nos testes.
