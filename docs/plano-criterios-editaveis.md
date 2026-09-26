# Plano 12 — Critérios editáveis: o que falta

Já existe: no pop-up "Critérios e pesos", um cursor de 0% a 200% por critério, com "Aplicar e recalcular" e "Repor predefinidos". A escolha fica guardada no navegador e a tabela mostra "critérios personalizados". Como funciona: [criterios.md](criterios.md).

Hoje há um único conjunto de multiplicadores, válido para todos os modelos.

## Falta fazer
1. **Perfis com nome:** além do "Predefinido" (bloqueado), perfis próprios ("Conservador", "O meu", …). Escolher o ativo, duplicar e apagar.
2. **Exportar, importar e partilhar por link** (perfil codificado no URL). Um link corrompido volta ao predefinido, com aviso.
3. **Multiplicadores por modelo:** poder alterar só a Primeira Liga, por exemplo, sem mexer nas seleções.
4. **Ajuste manual por jogo** (−3 a +3 na linha do boletim), para informação que o modelo não tem: lesões, castigos, motivação.
   - Aplica-se em log-odds (×0,15 por passo) às probabilidades finais e renormaliza, antes de fixos e duplas.
   - Opcional: ajuste da tendência para o empate.
5. **Critérios antigos editáveis** (jogos sem histórico): os pesos 40/30/15/10/5% e o bónus de casa passam a ser argumentos da função (hoje são constantes em `totobola_engine.py`) e editam-se diretamente, reajustados para somar 100%.
6. **"Avaliar o meu perfil":** corre o backtest da última época com o perfil do utilizador e mostra o log loss comparado com o predefinido. Precisa de limite de pedidos e cache.
7. **Comparação:** mostrar as probabilidades do modelo predefinido ao lado das personalizadas.
8. **Registo** das previsões personalizadas com o perfil (plano 4), para comparar o acerto dos perfis com o predefinido.
9. **Cache:** a chave inclui o perfil. O predefinido continua a usar a cache do CDN e os personalizados não.

## Regras de segurança dos predefinidos
- O perfil "Predefinido" não é editável nem apagável. É definido no servidor e versionado com o modelo.
- Quando o modelo muda de versão, os perfis do utilizador continuam a funcionar (os multiplicadores são relativos) e o pop-up avisa que o predefinido foi atualizado.

## Verificação
- Com todos os multiplicadores a 100% as probabilidades são idênticas às predefinidas (já testado).
- "Repor predefinidos" volta ao estado inicial mesmo depois de importar um perfil.
- Pedido com valores fora dos limites ou ids desconhecidos: erro 422 (já testado).
