# Plano — Resumo gerado por IA do desdobramento

> **Feito (27/09/2026):** toda a canalização está implementada — `app/services/resumo_ia.py` (chama a API da
> Anthropic diretamente por `httpx`, sem SDK novo), `POST /api/totobola/resumo` e `GET /api/totobola/resumo-disponivel`,
> cache de 24h por conteúdo, botão "Explicar este desdobramento" no Totobola (só aparece se a funcionalidade
> estiver ativa). **Falta só uma coisa: não existe chave `ANTHROPIC_API_KEY` configurada**, por isso a
> funcionalidade está desligada (o botão fica escondido, sem erros). Cria a chave em console.anthropic.com e
> põe-na em `backend/.env` para ativar.

## Objetivo
Depois de calcular um desdobramento, mostrar um **resumo em linguagem simples**, escrito por um modelo de IA (Claude ou ChatGPT), que explica em poucas frases porque é que as probabilidades saíram assim — sem inventar dados, só a reformular o que o motor já calculou.

## Princípio: a IA explica, não decide
A IA **nunca calcula probabilidades nem escolhe apostas** — isso continua a ser feito pelo motor estatístico (Elo, Poisson, critérios). A IA só recebe os números já calculados e escreve um texto a explicá-los. Isto evita dois problemas:
- **Alucinações:** um modelo de linguagem não deve inventar estatísticas; ao dar-lhe só os números certos como contexto, o trabalho dele é só reescrever, não descobrir.
- **Custo e latência:** um resumo de texto é muito mais barato e rápido do que pedir à IA para "pensar" na previsão.

## O que a IA recebe (exemplo de contexto por jogo)
```json
{
  "casa": "Benfica", "fora": "Porto",
  "modelo": "p1-elo-logit-v1",
  "prob": [0.42, 0.28, 0.30],
  "criterios_principais": [
    {"nome": "Força das equipas (Elo)", "peso": 0.65},
    {"nome": "Fator casa", "peso": 0.20}
  ],
  "confianca": "média",
  "fixo_ou_dupla": null
}
```
E, para o conjunto: nº de apostas, nº de fixos/duplas, se algum jogo é "pouco fiável".

## O que a IA deve (e não deve) escrever
**Deve:**
- Resumir em 3–6 frases, em português simples, os jogos mais decisivos do boletim (maior confiança, jogos mais equilibrados, duplas escolhidas).
- Mencionar sempre que é uma previsão estatística, sem garantia.
- Referir-se aos critérios que pesam mais nesse boletim (ex.: "no Benfica-Porto o fator decisivo foi a diferença de Elo").

**Não deve:**
- Inventar números que não estão no contexto fornecido.
- Sugerir "apostar mais" ou dar conselhos financeiros.
- Garantir ou insinuar que vai acertar.

Isto define-se com um *system prompt* fixo e testado, não editável pelo utilizador.

## Arquitetura técnica
- **Novo endpoint:** `POST /api/totobola/resumo`, recebe a resposta do `/desdobramento` (ou o `id` de uma previsão já guardada, quando existir base de dados) e devolve `{ "resumo": "..." }`.
- **Fornecedor:** Claude (Anthropic) ou a API da OpenAI — ambos servem; a escolha pode ficar por preço/qualidade nesse momento. Usar o modelo mais pequeno/barato disponível (o resumo é uma tarefa simples).
- **Chave de API:** nova variável de ambiente (`ANTHROPIC_API_KEY` ou `OPENAI_API_KEY`), como as outras chaves já usadas (`API_FOOTBALL_KEY`).
- **Cache:** o resumo de um boletim com os mesmos jogos e critérios pode ficar em cache (mesma previsão = mesmo resumo), para não pagar duas vezes pelo mesmo pedido.
- **Custo:** cada resumo é uma chamada curta (poucas centenas de tokens de entrada e saída) — o custo por pedido é baixo, mas soma-se com o tráfego. Ligar isto a um limite (ex.: só para utilizadores Premium, ver plano de contas pagas) se o volume justificar.
- **Falha do fornecedor de IA:** a app **nunca deve depender disto para funcionar**. Se a chamada à IA falhar ou demorar, a app mostra o desdobramento na mesma, só sem o resumo (ou com um resumo simples gerado localmente, sem IA, como recurso).

## Frontend
- Botão "Explicar este desdobramento" por baixo da tabela de probabilidades.
- Mostra "a gerar resumo..." e depois o texto, com uma nota pequena "Resumo gerado por IA, pode conter imprecisões".

## Passos (quando decidires avançar)
1. Escolher o fornecedor (Claude ou OpenAI) e criar a conta/chave de API.
2. Escrever e testar o *system prompt* com vários boletins reais, incluindo casos extremos (todos os jogos "pouco fiáveis", um boletim só com fixos).
3. Endpoint `POST /api/totobola/resumo` com cache.
4. Botão no frontend.
5. Medir custo real por pedido e decidir se fica gratuito ou exclusivo Premium.

## Verificação
- O resumo nunca contradiz os números mostrados na tabela (teste manual com vários boletins).
- Se a chave de API não estiver definida, a app continua a funcionar, só sem o botão de resumo.
- O texto nunca sugere uma aposta "garantida" ou dá conselhos financeiros — rever com uma checklist manual antes de publicar.

## Decisões que só tu podes tomar
- Qual o fornecedor de IA (Claude ou ChatGPT) e a conta a criar.
- Se o resumo é gratuito para todos ou exclusivo de contas Premium (plano de utilizadores pagos).
- Quanto estás disposto a gastar por mês nesta funcionalidade.
