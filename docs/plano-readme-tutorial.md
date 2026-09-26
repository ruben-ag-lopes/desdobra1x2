# Plano 11 — Documentação: o que falta

Já escritos: [README](../README.md), [tutorial](tutorial.md), [critérios de previsão](criterios.md) e [desenvolvimento](desenvolvimento.md).

## Falta fazer
1. **Capturas de ecrã no tutorial**, uma por passo, geradas com um script Playwright (`scripts/capturas.py`) para se refazerem com um comando sempre que o visual mudar. Ficam em `docs/img/`. Fazer depois do novo visual (plano 7).
2. **Tabelas automáticas:** o script `scripts/gerar_tabelas.py` gera as tabelas de resultados de `docs/backtests/README.md` a partir dos ficheiros `.json`, para os números nunca ficarem desatualizados.
3. **Página "Como funciona" na app:** um separador com o resumo simples e as secções principais do tutorial, ligado ao pop-up "Critérios e pesos" ("Saber mais") e ao rodapé. O texto vem de `docs/criterios.md`, importado no build do Vite, para haver uma só fonte.
4. **Tabela de versões dos modelos** em `criterios.md` (ex.: `selecoes-poisson-h2h-dc-v1`) e o que mudou em cada uma.
5. **Rever com um utilizador real:** alguém sem conhecimentos técnicos segue o tutorial e faz um desdobramento com um fixo e uma dupla sem ajuda.

## Verificação
- As fórmulas de `criterios.md` batem com o código: cada secção indica o ficheiro de onde vêm.
- `python scripts/gerar_tabelas.py` volta a gerar as mesmas tabelas que estão nos documentos.
