# Plano 7 — Novo visual: cores, tipo de letra e apresentação

## Objetivo
Trocar o tema escuro genérico (azul, preto e branco) por um visual próprio, em que **cada jogo tem a sua identidade** (cores dos logótipos oficiais) sem parecer uma página oficial da Santa Casa. Inclui tipo de letra, estrutura das páginas e componentes.

## Princípios
1. **Reconhecível, mas independente:** usamos as cores de cada jogo para orientar o utilizador, mas com **nome, logótipo e tipografia próprios**. Nada de logótipos da Santa Casa, e a indicação "não afiliado" fica visível.
2. **Tema claro por omissão**, a lembrar o papel do boletim, com tema escuro opcional. Escolha automática pelo sistema e botão para mudar.
3. **Legível no telemóvel primeiro:** a maioria das apostas é preenchida no telemóvel.
4. **Acessível:** contraste WCAG AA (4,5:1 no texto normal), foco visível e botões com `aria-pressed` (já existe).
5. **Aviso sempre visível** (pedido explícito, já implementado): no topo de todas as páginas, em destaque, diz que as previsões são estatísticas, que os números das lotarias são aleatórios e que não há garantia de acerto. O novo visual pode mudar-lhe o estilo, mas nunca o esconder nem o reduzir a texto pequeno.

## Cores (tokens por jogo)
Amostradas dos logótipos do site oficial, com o contraste medido:

| Jogo | Principal | Texto sobre a principal | Acento | Notas de contraste |
|---|---|---|---|---|
| Totobola / Extra | `#008058` verde | branco (4,97:1 ✓) | rosa do boletim `#ff4b79`, só em marcas e bordas; texto rosa usa `#d6275a` (4,56:1 ✓) | O rosa claro não serve para texto. |
| Totoloto | `#0088d0` azul | preto (4,88:1) ou azul escurecido `#0070ad` com branco (5,36:1 ✓) | laranja `#f04820` (decorativo) | O azul original com branco falha AA (3,87:1). |
| Euromilhões | `#202058` azul-marinho | branco (14,9:1 ✓) | dourado `#e8c850` com texto escuro (11,5:1 ✓) | Estrelas em dourado. |
| EuroDreams | `#7818a0` roxo | branco (8,62:1 ✓) | — | — |
| Futebol (plano 6) | a definir (ex.: um neutro "relvado") | — | — | Não pode colidir com o verde do Totobola. |

Cada jogo define os mesmos tokens em CSS: `--brand`, `--brand-contrast`, `--brand-strong` (texto), `--brand-tint` (fundos suaves), `--accent`. Hoje só existem `--game-accent` e `--game-accent-soft`, que passam a estes. Neutros comuns: fundo `#f6f7f9`, superfície `#ffffff`, texto `#14171c`, texto secundário `#5b6472`, bordas `#e3e6ea`. O tema escuro redefine só os neutros e os `--brand-tint`.

## Maquete
Proposta navegável (privada até a partilhares): https://claude.ai/artifact/K1C5CQPMKxTyRo3Koe2dD5
- Totobola no computador (interativo: clicar nos 1/X/2 cria fixos e duplas e atualiza o desdobramento).
- Totobola no telemóvel.
- Euromilhões (interativo: gera chaves).
- Folha de cores e tipografia.

Nome decidido: **desdobra1X2** (logótipo ainda por desenhar).

## Tipografia
- **Títulos e números grandes:** *Barlow Condensed* (600–700). Condensada e desportiva, lembra marcadores e boletins.
- **Texto e interface:** *Source Sans 3* (400–700), muito legível em tamanhos pequenos e menos genérica do que Inter ou Roboto. Na maquete substituiu o Inter proposto inicialmente.
- **Números** (probabilidades, apostas, números da lotaria): `font-variant-numeric: tabular-nums`, para as colunas ficarem alinhadas.
- **Alojamento:** ficheiros servidos pela própria app (pacotes `@fontsource/barlow-condensed` e `@fontsource/source-sans-3`), não pelo CDN do Google. Evita enviar o IP dos visitantes a terceiros (RGPD) e é mais rápido. A maquete usa o CDN só por simplicidade.
- **Escala:** 14 / 16 / 18 / 22 / 28 / 36 px, com line-height 1,45 no texto.

## Apresentação geral
**Cabeçalho**
- Nome e logótipo próprios (a definir), com uma frase curta.
- **Seletor de jogos em "fichas"**: cada jogo é um cartão pequeno com a sua cor e o nome no tipo de letra dos títulos. No telemóvel, fila deslizante na horizontal.

**Página de cada jogo**
1. **Faixa do jogo:** fundo `--brand`, nome do jogo, concurso e **contagem decrescente** até ao fecho das apostas ("fecha em 2 d 4 h").
2. **Totobola como boletim:** as 13 linhas imitam o boletim em papel, com o nº do jogo, as equipas e três "quadrados" 1, X e 2 em rosa.
   - Clicar num quadrado fixa o resultado; clicar em dois faz uma dupla (mesma lógica de hoje).
   - Depois de calcular, cada quadrado mostra a probabilidade com cor mais intensa quanto maior for (mapa de calor).
   - Assim a escolha e o resultado ficam no mesmo sítio, em vez de duas tabelas.
3. **Desdobramento em "colunas de boletim":** cada aposta é uma coluna estreita com os 13 símbolos, como no papel. Os jogos fixos e as duplas ficam marcados.
4. **Lotarias:** os números aparecem em **bolas** (círculos com a cor do jogo) e as estrelas do Euromilhões em estrelas douradas. Cada chave é um cartão com "copiar".
5. **Barra de ações fixa no fundo**, só no telemóvel: "Calcular" e "Copiar" sempre à mão.
6. **Pop-up de critérios:** mantém-se, com as barras de peso na cor do jogo.

**Rodapé**
- Jogo responsável, "não afiliado à Santa Casa", ligações legais e o botão "Apoiar o projeto" (já feito).

## Arquitetura do CSS
- Hoje tudo está em `App.css` e `index.css` (este último vem do modelo inicial do Vite e está parcialmente sem uso).
- **Nova organização:**
  - `styles/tokens.css`: neutros, temas e tokens por jogo, através de `[data-game]` (já usado);
  - `styles/base.css`: tipografia e elementos base;
  - um ficheiro por componente (`*.module.css`).
- **Componentes novos:** `GameSwitcher`, `GameHero` (faixa + contagem), `CouponGrid` (boletim), `BetColumns`, `LotteryBall`, `ThemeToggle`, `StickyActions`.

## Passos
1. **Maquetes:** um protótipo navegável com os 5 jogos, no telemóvel e no computador, para aprovares antes de mexer no código. Pode ser uma página HTML partilhável.
2. **Nome e logótipo** do projeto (decisão tua). O domínio depende disto (plano 3).
3. Tokens + tipografia + tema claro/escuro.
4. Cabeçalho, seletor de jogos, faixa do jogo e rodapé.
5. Boletim do Totobola (`CouponGrid`) e colunas do desdobramento.
6. Bolas e estrelas das lotarias.
7. Revisão de acessibilidade (contraste, teclado, leitor de ecrã) e desempenho (tamanho das fontes, Lighthouse).

## Verificação
- Contraste de todos os pares texto/fundo ≥ 4,5:1, medido com uma ferramenta automática no browser.
- Testar em 360 px (telemóvel), 768 px e 1280 px, sem deslocação horizontal.
- Mudar de jogo muda cores e faixa sem recarregar. Temas claro e escuro corretos em todos os jogos.
- Preencher um Totobola completo só com o teclado.
