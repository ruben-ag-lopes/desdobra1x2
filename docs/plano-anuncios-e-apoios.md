# Plano 5 — Anúncios e apoios (Buy Me a Coffee)

## Donativos — ✅ feito
O rodapé tem o botão **"☕ Apoiar o projeto"**, a apontar para buymeacoffee.com/desdobra1x2 (`VITE_BUYMEACOFFEE_URL` em `frontend/.env.local`). Decidido usar só Buy Me a Coffee, sem PayPal. Falta só pôr a mesma variável nas variáveis de ambiente do Vercel quando publicares (plano 3).

## O que condiciona os anúncios
1. **Vercel:** o plano gratuito (Hobby) proíbe anúncios, porque contam como uso comercial. Donativos são permitidos. Com anúncios é preciso o plano **Pro** (pago). Confirmado nas regras de uso justo do Vercel (29/09/2026), citação exata: *"Hobby teams are restricted to non-commercial personal use only... [commercial usage includes] the inclusion of advertisements, including but not limited to online advertising platforms like Google AdSense"*. Donativos ficam explicitamente fora disto ("Asking for Donations does not fall under commercial usage"). Não há forma de contornar isto ficando no Vercel Hobby.
2. **Google AdSense e conteúdo de jogo:** o Google só deixa monetizar páginas com conteúdo de jogo e apostas a editores de uma lista de países, e **Portugal não está nessa lista**. Uma app de desdobramentos do Totobola e números de lotaria será muito provavelmente vista como conteúdo de jogo, com risco de recusa ou de anúncios limitados. Tratar o AdSense como experiência, não como receita garantida.
3. **Consentimento de cookies (RGPD):** para mostrar anúncios do Google a utilizadores no Espaço Económico Europeu é obrigatório um banner de consentimento certificado pelo Google. ✅ **Política de Privacidade e Termos de Uso já escritos** (`frontend/public/privacidade.html` e `termos.html`, ligados no rodapé) — a política já avisa que falta o banner de consentimento antes de os anúncios aparecerem a visitantes na UE.
4. **Publicidade a jogo em Portugal:** anúncios ou links de casas de apostas estão sujeitos às regras de publicidade a jogos e apostas (Código da Publicidade) e à supervisão do SRIJ. Isso inclui não se dirigir a menores e incluir mensagens de jogo responsável. **Confirmar com um jurista antes** de qualquer acordo de afiliação.

## Alternativa ao Vercel Pro (pesquisa de 29/09/2026)
Perguntaste se há forma de teres anúncios sem pagar o Vercel Pro. Há, mas com um custo diferente: mais complexidade, não dinheiro.

- **A Netlify não proíbe anúncios.** Verifiquei os Termos de Uso e o Self-Serve Subscription Agreement da Netlify: não têm nenhuma cláusula "só uso não comercial" nem qualquer menção a publicidade/AdSense. O plano gratuito deles permite monetizar com anúncios.
- **Mas a Netlify não corre backends em Python.** As Netlify Functions só suportam JavaScript/TypeScript, Go e Rust — o FastAPI (com numpy/scipy) não corre lá. Só serviria para o frontend.
- **Arquitetura alternativa:** frontend na Netlify (grátis, com anúncios) + backend FastAPI noutro serviço que aceite Python de graça — Render, Railway ou Fly.io (já eram a "opção B" no `plano-publicacao-vercel.md` para evitar arranques a frio no Vercel). **Não confirmei se o plano gratuito de nenhum destes proíbe anúncios** (a Render bloqueou a minha pesquisa automática) — precisa de confirmação antes de contar com isto. Nenhum deles corre Python nativo tão bem quanto o Vercel para este caso sem alguma configuração extra.
- **Não tentar um "meio-termo"** de manter só o backend no Vercel Hobby (sem anúncios) e pôr os anúncios só no frontend na Netlify: a definição do Vercel de uso comercial é ampla ("qualquer parte da produção do projeto" com fins lucrativos), por isso um backend a alimentar um frontend com anúncios pode continuar a contar como uso comercial aos olhos do Vercel, mesmo que o anúncio em si não apareça lá. Não é uma leitura testada — se quiseres seguir por aqui, o mais seguro é perguntar diretamente ao suporte do Vercel (como os próprios documentos sugerem).

**Comparação de custo:** Vercel Pro ≈ 20 US$/mês (~240 US$/ano) vs. Netlify + Render/Railway/Fly grátis, mas com dois serviços para gerir em vez de um, e sem a garantia de que o backend gratuito não tem as suas próprias restrições de uso comercial. **Recomendação:** não vale a pena migrar já — a fase 1 (só donativos) não precisa de nada disto. Só decidir entre pagar o Pro ou migrar quando chegares mesmo à fase 3 (anúncios a sério).

## Estratégia recomendada, por fases
| Fase | Quando | O quê | Custo |
|---|---|---|---|
| 1 | Lançamento | Só donativos. Vercel Web Analytics (sem cookies) para medir as visitas. | 0 € |
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
- Aceitar ou não publicidade de apostas (decisão de posicionamento e jurídica).
- Nome e domínio próprios, sem "Santa Casa" (ver o plano 7).
