# Plano — Critérios editáveis pelo utilizador

> Só plano, sem implementação.

## Objetivo
O utilizador pode **alterar livremente os critérios** das previsões num pop-up semelhante ao "Critérios e pesos". Pode desligar, reduzir ou reforçar cada critério e juntar o seu próprio ajuste por jogo. Os **critérios predefinidos mantêm-se sempre**: não podem ser apagados nem alterados e ficam a um clique ("Repor predefinidos").

## Como funciona (para o utilizador)
1. No pop-up "Critérios e pesos" aparece o botão **"Personalizar"**, que abre o editor.
2. Para cada modelo usado no concurso atual (ex.: Seleções, Primeira Liga) há uma lista de critérios, cada um com:
   - um **cursor de 0% a 200%** (100% = predefinido, com uma marca visível nessa posição);
   - um **interruptor** para ligar ou desligar (desligar = 0%);
   - o **peso resultante**, atualizado ao mover o cursor (a mesma barra do pop-up atual).
3. **Nos critérios antigos** (jogos sem dados), os pesos 40/30/15/10/5% e o bónus de casa editam-se diretamente e são reajustados para somar 100%.
4. **Ajuste manual por jogo** (fase 2): em cada linha do boletim, um pequeno controlo "inclinar para a casa ou para fora" (−3 a +3) serve para informação que o modelo não tem, como lesões, castigos ou motivação. Há também um ajuste opcional da tendência para o empate.
5. **Perfis:**
   - "Predefinido" (bloqueado);
   - perfis próprios com nome ("Conservador", "O meu", …);
   - escolher o perfil ativo, duplicar, apagar;
   - exportar ou importar (ficheiro JSON ou link para partilhar).
6. **Com um perfil personalizado ativo:**
   - a tabela de probabilidades mostra a etiqueta **"critérios personalizados"**;
   - o pop-up avisa que os critérios alterados **não foram validados**;
   - as probabilidades do modelo predefinido podem ser mostradas ao lado para comparação.
7. **"Avaliar o meu perfil"** (fase 3): corre o backtest da última época com o perfil do utilizador e mostra o erro (log loss) comparado com o predefinido. Tem sobretudo valor educativo e mostra o efeito real das alterações.

## Como funciona (técnico)
- **Transformação única para todos os modelos:** cada critério é um grupo de variáveis (já definido em `app/research/importance.py`, `CRITERIA`, com um valor "neutro" por variável). Um multiplicador *m* aplica-se assim:
  `x' = neutro + m · (x − neutro)`, antes de `model.predict`.
  - *m* = 1: exatamente o modelo predefinido (garantido por teste);
  - *m* = 0: o critério deixa de contar (é a mesma operação usada hoje para calcular os pesos);
  - *m* = 2: o efeito do critério duplica.
  - Funciona igual para o Elo calibrado e para o Poisson, sem reescrever os modelos.
- **Ajuste manual por jogo:** soma em log-odds (inclinação ×0,15 por passo) aplicada às probabilidades finais e renormalizada, antes de fixos e duplas.
- **Critérios antigos:** os pesos passam a ser argumentos da função (hoje são constantes em `totobola_engine.py`), com os valores atuais como predefinição.
- **API:**
  - `GET /api/totobola/criterios` passa a devolver um `id` estável por critério (`elo`, `casa`, `ataque`, `defesa`, `h2h`) e o valor predefinido;
  - `POST /desdobramento` aceita `criterios: {modelo: {id: multiplicador}}` e `ajustes: {match_id: inclinação}`. Os valores são validados (0–2; −3 a +3) e ids desconhecidos são rejeitados;
  - a resposta indica, por jogo, `personalizado: true` e as probabilidades predefinidas para comparação.
- **Onde se guarda:**
  - no navegador (`localStorage`), sem conta;
  - partilha por link (perfil codificado no URL);
  - com contas (futuro) na base de dados do plano 4.
- **Registo:** as previsões personalizadas são gravadas com o perfil (plano 4), para comparar o acerto dos perfis com o predefinido.
- **Cache:** a chave da cache inclui o perfil. O perfil predefinido continua a usar a cache do CDN, e os personalizados não.

## Regras para manter os predefinidos seguros
- **Imutável:** o perfil "Predefinido" não é editável nem apagável. É definido no servidor e versionado com o modelo (ex.: `p1-elo-logit-v1`).
- **Modelo novo:** quando o modelo muda de versão, os perfis do utilizador continuam a funcionar, porque os multiplicadores são relativos. O pop-up avisa que o predefinido foi atualizado.
- **Sem perfil válido** (ex.: link corrompido): volta-se ao predefinido, com um aviso.

## Passos
1. Backend: ids estáveis nos critérios; função `apply_multipliers(rows, multipliers)`; teste "*m* = 1 dá exatamente o predefinido"; validação na API.
2. Critérios antigos parametrizáveis.
3. Frontend: editor no pop-up (cursores, interruptores, pesos ao vivo), perfis no `localStorage`, etiqueta "personalizados".
4. Exportar, importar e partilhar por link.
5. Ajuste manual por jogo.
6. "Avaliar o meu perfil" (backtest com limite de pedidos e cache).

## Verificação
- Com todos os multiplicadores a 100% as probabilidades são **idênticas** às predefinidas (teste automático).
- Um critério desligado (0%) dá o mesmo resultado que o cálculo de pesos atual para esse critério.
- "Repor predefinidos" volta sempre ao estado inicial, mesmo depois de importar um perfil.
- Pedido com valores fora dos limites ou ids desconhecidos → erro 422.
