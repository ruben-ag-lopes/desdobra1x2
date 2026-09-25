# Plano 5 — Anúncios e apoios (Buy Me a Coffee / PayPal)

## Já feito
Rodapé com o botão **"☕ Apoiar o projeto"**. Ao clicar abre as duas opções, Buy Me a Coffee e PayPal, cada uma numa nova janela (`frontend/src/components/SupportFooter.tsx`).
- Os links vêm de `VITE_BUYMEACOFFEE_URL` e `VITE_PAYPAL_URL` (ver `frontend/.env.example`). Sem eles, apontam para as páginas iniciais dos serviços.
- **A fazer por ti:**
  - criar a página no buymeacoffee.com;
  - no PayPal, criar um link PayPal.Me (mais simples) ou um botão "Donate";
  - pôr os dois links em `frontend/.env.local` (local) e nas variáveis do Vercel (produção).

## O que condiciona os anúncios
1. **Vercel:** o plano gratuito (Hobby) proíbe anúncios, porque contam como uso comercial. Donativos são permitidos. Com anúncios é preciso o plano **Pro** (pago).
2. **Google AdSense e conteúdo de jogo:** o Google só deixa monetizar páginas com conteúdo de jogo e apostas a editores de uma lista de países, e **Portugal não está nessa lista**. Uma app de desdobramentos do Totobola e números de lotaria será muito provavelmente vista como conteúdo de jogo, com risco de recusa ou de anúncios limitados. Tratar o AdSense como experiência, não como receita garantida.
3. **Consentimento de cookies (RGPD):** para mostrar anúncios do Google a utilizadores no Espaço Económico Europeu é obrigatório um banner de consentimento certificado pelo Google. Também é preciso uma Política de privacidade.
4. **Publicidade a jogo em Portugal:** anúncios ou links de casas de apostas estão sujeitos às regras de publicidade a jogos e apostas (Código da Publicidade) e à supervisão do SRIJ. Isso inclui não se dirigir a menores e incluir mensagens de jogo responsável. **Confirmar com um jurista antes** de qualquer acordo de afiliação.

## Estratégia recomendada, por fases
| Fase | Quando | O quê | Custo |
|---|---|---|---|
| 1 | Lançamento | Só donativos (feito). Vercel Web Analytics (sem cookies) para medir as visitas. | 0 € |
| 2 | Tráfego regular (ex.: alguns milhares de visitas/mês) | Patrocínio direto de marcas desportivas que não sejam de apostas, num espaço fixo do rodapé ou da página. Sem cookies nem banner de consentimento. | 0 € |
| 3 | Se a fase 2 justificar | Plano Pro no Vercel, banner de consentimento certificado e candidatura ao AdSense (ou uma rede alternativa). Medir se a receita paga o Pro. | Pro + tempo |
| Opcional | Só com parecer jurídico | Afiliação com operadores licenciados pelo SRIJ. É o mais rentável, mas também o mais regulado e o que mais afeta a imagem de ferramenta independente. | — |

## Onde pôr anúncios (quando existirem)
- **Nunca** dentro do fluxo principal: lista de jogos, botões 1/X/2, "Calcular", botões de copiar e pop-up de critérios.
- Lugares propostos:
  - um bloco depois da tabela do desdobramento;
  - um bloco no fundo dos separadores de lotaria;
  - uma barra lateral em ecrãs largos.
- No telemóvel, no máximo um bloco por ecrã. Carregamento diferido (lazy load) para não atrasar a página.
- Nenhum anúncio para quem não deu consentimento, se a rede o exigir.

## Implementação técnica (fase 3)
1. Componente `<AdSlot id="..."/>` que só aparece quando `VITE_ADS_ENABLED=true` **e** há consentimento.
2. Ficheiro `frontend/public/ads.txt` com o ID de editor.
3. Script do banner de consentimento carregado antes do script da rede de anúncios.
4. Página "Privacidade e cookies" e ligação no rodapé.
5. Medir o impacto na velocidade (Core Web Vitals no Vercel Analytics) antes e depois.

## Decisões pendentes (tuas)
- Links reais do Buy Me a Coffee e do PayPal.
- Aceitar ou não publicidade de apostas (decisão de posicionamento e jurídica).
- Nome e domínio próprios, sem "Santa Casa" (ver o plano 7).
