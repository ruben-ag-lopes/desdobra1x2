# Plano — Contas de utilizador e acesso pago às previsões

> Só plano, sem implementação.

## Objetivo
Permitir contas de utilizador e um nível de acesso pago que desbloqueia funcionalidades avançadas de previsão, mantendo uma oferta gratuita útil (a app de hoje continua a funcionar sem conta).

## Modelo de negócio proposto
| Nível | Preço | O que inclui |
|---|---|---|
| **Gratuito** (sem conta) | 0 € | Tudo o que existe hoje: Totobola, Futebol, lotarias, critérios com multiplicadores. |
| **Registado** (conta grátis) | 0 € | Guardar critérios personalizados e histórico de desdobramentos na conta em vez de só no navegador; sincronizar entre dispositivos. |
| **Premium** | assinatura mensal (valor a decidir, ex.: 2,99–4,99 €/mês) | Ligas adicionais (Liga 2/3, Campeonato de Portugal, competições europeias — plano 13), resumo com IA de cada desdobramento (plano 8), "avaliar o meu perfil" com backtest (plano 12), sem qualquer anúncio (se estes existirem no plano gratuito, plano 5), acesso antecipado a modelos novos. |

**Princípio:** as previsões 1X2 e os desdobramentos de base do Totobola **nunca ficam fechados atrás de pagamento** — é o núcleo da app e o que já demonstrámos que tem valor. O pago é para funcionalidades avançadas e conveniência, não para a previsão em si.

## Aspetos legais e éticos a resolver antes de cobrar
- **Isto não é uma casa de apostas** nem vende "informação privilegiada": os termos de serviço devem deixar claro que são previsões estatísticas, sem garantia, e que pagar não aumenta as hipóteses de ganhar.
- **Faturação em Portugal:** se houver receita recorrente de utilizadores, confirmar com um contabilista as obrigações fiscais (abertura de atividade, IVA sobre serviços digitais, faturas eletrónicas).
- **RGPD:** contas implicam dados pessoais (e-mail, pagamento). Precisa de política de privacidade, base legal para o tratamento, e um responsável pelo cumprimento se a escala justificar.
- **Jogo responsável:** manter o aviso em destaque mesmo para utilizadores Premium; nunca ligar o pagamento a "mais garantia de ganhar".

## Arquitetura técnica
- **Autenticação:** um serviço gerido (ex.: Clerk, Auth0 ou Supabase Auth) em vez de gerir passwords à mão — menos risco de segurança e menos trabalho. Login por e-mail/password e, opcionalmente, Google.
- **Base de dados:** a mesma do plano 4 (Postgres/Neon), com tabelas novas:
  - `users` (id, email, criado_em, nível de subscrição, id do cliente no processador de pagamentos);
  - `user_criteria` (user_id, multiplicadores, pesos_antigos, nome do perfil) — substitui o `localStorage` para utilizadores com conta;
  - `subscriptions` (user_id, estado, próxima cobrança, processador).
- **Pagamentos:** Stripe (suporta assinaturas, período de teste, faturas automáticas, e tem presença em Portugal). Webhook do Stripe atualiza `subscriptions` quando o pagamento é confirmado ou falha.
- **Backend:** middleware de autenticação nas rotas que exigem conta (ex.: `GET/POST /api/user/criterios`), e um decorador/dependência FastAPI que verifica o nível de subscrição antes de responder a rotas Premium (ex.: previsões da Liga 2).
- **Frontend:** página de login/registo, indicador do nível de conta no cabeçalho, páginas de gestão da assinatura (ligadas ao portal de faturação do Stripe, que já trata cancelamentos e faturas sem termos de construir nada).

## Passos (quando decidires avançar)
1. Confirmar o modelo de preços e o que fica gratuito vs. pago (decisão de negócio, não técnica).
2. Escolher o serviço de autenticação e criar a conta.
3. Criar conta Stripe (ou equivalente) e configurar o produto de assinatura.
4. Tabelas na base de dados (depende do plano 4 estar feito).
5. Backend: autenticação, rotas protegidas, webhook do Stripe.
6. Frontend: login, registo, página de conta, indicador de nível.
7. Termos de serviço e política de privacidade revistos por um jurista antes de cobrar seja o que for.

## Verificação
- Um utilizador sem conta continua a usar a app exatamente como hoje.
- Um utilizador Premium perde o acesso automaticamente se cancelar ou se o pagamento falhar (webhook do Stripe testado com o modo de teste).
- Os dados de pagamento nunca tocam nos nossos servidores diretamente (usar Stripe Checkout ou Elements, nunca guardar números de cartão).

## Decisões que só tu podes tomar
- Se queres mesmo cobrar, e quanto.
- Que funcionalidades ficam exclusivas do Premium (a lista acima é uma proposta).
- Se aceitas os custos fixos de um serviço de autenticação e do Stripe antes de teres receita.
