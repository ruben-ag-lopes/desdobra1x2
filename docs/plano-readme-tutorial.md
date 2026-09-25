# Plano — README, tutorial e critérios completos de previsão

> Só plano: os documentos ainda não foram escritos.

## Objetivo
Documentação para dois públicos diferentes:
1. **Utilizadores** (não técnicos): como usar o desdobra1X2 passo a passo e o que significam os números.
2. **Quem quer perceber ou verificar o método** (curiosos, e tu no futuro): todos os critérios, fórmulas, dados e resultados da validação, sem ter de ler o código.

## Estrutura
| Ficheiro | Público | Conteúdo |
|---|---|---|
| `README.md` (reescrito, curto) | Todos | O que é, aviso de jogo responsável, ligação para o site, instalação local em 5 comandos, ligações para os outros documentos |
| `docs/tutorial.md` | Utilizadores | Guia passo a passo com imagens |
| `docs/criterios.md` | Curiosos / técnicos | Método completo de previsão |
| `docs/desenvolvimento.md` | Programadores | Estrutura do código, testes, backtest, variáveis de ambiente, publicação (conteúdo que hoje está no README) |
| Página "Como funciona" na app | Utilizadores | Versão curta do tutorial e dos critérios, com ligação para os documentos completos |

## Conteúdo do tutorial (`docs/tutorial.md`)
1. **O que a ferramenta faz e o que não faz.** Não submete apostas e não garante acertos. Mesmo aviso da app.
2. **Totobola passo a passo**, com uma imagem por passo:
   1. Abrir o separador: o concurso, o prazo e os 13 jogos carregam sozinhos (e o que fazer se falhar: colar os jogos).
   2. Ler as probabilidades: 1, X e 2, e o palpite.
   3. Fixar resultados e fazer duplas: exemplo completo com números (33/28/38 → dupla 1X → 54/46).
   4. Escolher o nº de apostas e calcular o desdobramento.
   5. Ler a tabela do desdobramento (colunas = apostas) e copiá-la ("jogo a jogo" para preencher o boletim).
   6. Abrir "Critérios e pesos" e perceber o que pesa em cada jogo.
   7. (Quando existir) personalizar os critérios e repor os predefinidos.
3. **Totoloto, Euromilhões, EuroDreams:** gerar chaves, copiar, e porque é que nenhum método aumenta a probabilidade de ganhar.
4. **Perguntas frequentes:**
   - porque aparece "pouco fiável";
   - porque é que um favorito com 80% às vezes perde;
   - diferença entre fixo e dupla;
   - quantas apostas fazer (custo);
   - de onde vêm os dados.
5. **Jogo responsável:** +18, limites, linha de apoio SICAD (confirmar contacto atual).

**Imagens:** capturas automáticas com o script Playwright já usado nos testes da interface (`scratchpad/ui_check.py` → passa para `scripts/capturas.py`), guardadas em `docs/img/`. Assim são refeitas com um comando sempre que o visual mudar (plano 7).

## Conteúdo dos critérios (`docs/criterios.md`)
Começa com um **resumo em linguagem simples** (meia página) e depois o detalhe:

1. **Fontes de dados:** football-data.co.uk (ligas, 8 épocas), martj42/international_results (seleções, 10 anos), eloratings.net / clubelo.com (recurso de reserva) e site da Santa Casa (concursos e jogos). Frequência de atualização e cache (12 h).
2. **Rating Elo:**
   - valor inicial 1500;
   - K = 25 (clubes) ou 40 (seleções);
   - vantagem de casa de 60 ou 100 pontos (0 em campo neutro);
   - multiplicador pela diferença de golos (1; 1,5; (11+d)/8);
   - regressão de 25% à média no início de cada época (só clubes);
   - fórmula do resultado esperado.
3. **Forma recente:** golos marcados e sofridos nos últimos 8 jogos (valor por omissão 1,3 sem histórico).
4. **Confronto direto:** média da diferença de golos nos últimos 5 jogos entre as duas equipas.
5. **Modelo Elo calibrado** (logit ordenado): fórmula de P(1), P(X) e P(2) a partir da diferença de Elo, do fator casa e do limiar de empate; parâmetros estimados por máxima verosimilhança.
6. **Modelo Poisson:**
   - golos esperados λ (casa) e μ (fora) por regressão log-linear (Elo, fator casa, ataque, defesa, H2H);
   - grelha de resultados exatos 0–10;
   - ajuste Dixon–Coles (fórmula de τ e estimação de ρ);
   - soma da grelha para obter 1X2, mais de 2,5 e ambas marcam.
7. **Que modelo se usa em cada jogo:**
   - ordem de preferência: seleções → ligas → Elo direto → critérios antigos;
   - reconhecimento de nomes (sinónimos e aproximação);
   - mínimo de 5 jogos de histórico por equipa.
8. **Critérios antigos** (recurso "pouco fiável"): 40 / 30 / 15 / 10 / 5 % + 10 % casa, e porque ficam quase sempre perto de 1/3.
9. **Pesos mostrados no pop-up:** como são calculados (neutralizar um critério e medir quanto as probabilidades mudam) e o que significam.
10. **Duplas e fixos:** fórmula da redistribuição proporcional.
11. **Desdobramento:**
    - repartição das apostas pelos resultados (maiores restos);
    - regra "sem resultado abaixo de 50% como único";
    - duplas com os dois resultados sempre presentes;
    - rotação entre jogos para as apostas não serem iguais.
12. **Validação:**
    - backtest cronológico (reajuste de 4 em 4 semanas, só com dados anteriores);
    - métricas: log loss, RPS, Brier, calibração;
    - tabelas por liga, incluindo a comparação com as casas de apostas (que continuam melhores);
    - como repetir: comandos do backtest.
13. **Limitações conhecidas:**
    - não sabe de lesões, castigos, motivação nem mudanças de treinador;
    - ligas sem dados;
    - taças e competições europeias;
    - clubelo em baixo.
14. **Versões dos modelos:** tabela com os identificadores (ex.: `selecoes-poisson-h2h-dc-v1`) e o que mudou em cada versão.

**Números sempre atuais:** as tabelas de resultados são geradas a partir de `backtest --json` por um script (`scripts/gerar_tabelas.py`) que atualiza blocos marcados no markdown. Evita números desatualizados escritos à mão.

## Página "Como funciona" na app
- Rota ou separador `Como funciona`, que mostra o resumo simples e as secções principais do tutorial.
- Ligação a partir do pop-up "Critérios e pesos" ("Saber mais") e do rodapé.
- O texto vem de `docs/criterios.md` (importado no build do Vite como markdown). Assim há uma só fonte e a app e o repositório nunca divergem.

## Passos
1. Escrever `docs/criterios.md` (a parte mais longa; o conteúdo já existe no código e nos planos).
2. Script de capturas + `docs/tutorial.md`.
3. Reescrever o `README.md` e mover o conteúdo técnico para `docs/desenvolvimento.md`.
4. Script de tabelas automáticas.
5. Página "Como funciona" na app (depois do novo visual, plano 7, para as capturas já mostrarem o design final).

## Verificação
- Uma pessoa sem conhecimentos técnicos segue o tutorial e faz um desdobramento com um fixo e uma dupla sem ajuda.
- As fórmulas do `criterios.md` batem com o código: cada secção indica o ficheiro e a função de onde vem (ex.: `app/research/features.py`, `FeatureState.update`).
- `python scripts/gerar_tabelas.py` volta a gerar as mesmas tabelas que estão nos documentos.
