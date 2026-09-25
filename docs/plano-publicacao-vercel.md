# Plano 3 — Publicação no Vercel

## Objetivo
Pôr a app online num endereço público (frontend React + backend FastAPI), com o mínimo de custo no arranque e sem perder funcionalidades.

## Arquitetura recomendada
Um único projeto Vercel com **Services** (em beta): o frontend (Vite) serve `/` e o backend (FastAPI) serve `/api/*`. Ficam no mesmo domínio, por isso não há problemas de CORS nem é preciso configurar o URL da API.

```json
// vercel.json (na raiz do repositório)
{
  "services": {
    "web": { "root": "frontend/" },
    "api": { "root": "backend/", "entrypoint": "app.main:app" }
  },
  "rewrites": [
    { "source": "/api/(.*)", "destination": { "service": "api" } },
    { "source": "/(.*)", "destination": { "service": "web" } }
  ]
}
```

**Plano B**, se os Services não estiverem disponíveis na conta: dois projetos Vercel (frontend e backend), com `VITE_API_URL` a apontar para o backend e `CORS_ORIGINS` com o domínio do frontend. O backend pode também ir para o Render ou o Railway, que correm um servidor sempre ligado, sem arranques a frio.

## Limites do Vercel que nos afetam
| Limite | Valor | Impacto |
|---|---|---|
| Tamanho do bundle Python | 500 MB descomprimido | numpy + scipy cabem. Tirar o `google-cloud-bigquery` se não for usado. |
| Duração máxima | 300 s (Hobby) | Suficiente para o 1.º treino (~5–15 s num arranque a frio). |
| Disco | só leitura, exceto `/tmp` | Definir `DATA_DIR=/tmp/data` (já suportado). |
| Memória | 2 GB (Hobby) | Suficiente. |
| Uso comercial | Hobby = **só não comercial** | Donativos são permitidos. Anúncios ou afiliados obrigam ao plano **Pro** (pago, por membro). |

## Alterações ao código
Já feitas:
- `VITE_API_URL` configurável no frontend. Vazio = mesmo domínio.
- `CORS_ORIGINS` configurável no backend.
- `DATA_DIR` configurável para a cache de CSV.
- `<html lang="pt-PT">` e título da página.

Também já feitas:
- ✅ `vercel.json` na raiz com os Services (`web` + `api`), região `fra1` (Frankfurt), `maxDuration` de 120 s e `excludeFiles` (tests, data, venv).
- ✅ `backend/.python-version` = 3.12 e versões fixas no `requirements.txt`. O BigQuery passou para `requirements-optional.txt`, para o pacote ficar mais leve.
- ✅ Em produção o frontend usa a API no mesmo domínio por omissão (`VITE_API_URL` só é preciso no plano B).
- ✅ Cabeçalhos `Cache-Control` nas respostas de concursos, jogos, sorteios e critérios. O CDN do Vercel guarda-as 15 min (critérios: 1 h), o que evita repetir pedidos ao site da Santa Casa em cada instância.
- ✅ Limites contra abusos: no máximo 500 apostas e 20 jogos por pedido (422 acima disso).
- ✅ Arranque mais rápido: as ligas só são carregadas quando um jogo precisa delas, e as previsões saem de um estado guardado (0,03 s depois do treino).

A fazer antes da publicação:
1. **Repositório Git:** o projeto ainda não está em git. `git init`, garantir que o `.gitignore` exclui `backend/venv/`, `backend/data/`, `.env*` e `node_modules/`, depois publicar no GitHub (privado).
2. **Arranque a frio:** cada instância nova descarrega os CSV (~4 MB) e treina os modelos precisos (~5–15 s). Aceitável na fase 1.
   - Fase 2: uma tarefa agendada (Vercel Cron, diária) treina os modelos e guarda um "artefacto" pequeno (ratings Elo + coeficientes, em JSON) na base de dados ou no Vercel Blob. Os pedidos passam a só ler esse artefacto, com resposta em menos de 1 s mesmo a frio. Ver o plano 4.
3. **Confirmar a configuração dos Services** no 1.º preview deploy. Estão em beta, e as chaves `framework`, `entrypoint` e `functions` por serviço seguem a documentação de 09/2026.

## Riscos a testar numa pré-visualização (preview deploy)
- **Scraping a partir de IPs de datacenter:** o jogossantacasa.pt pode bloquear ou limitar pedidos vindos do Vercel. Testar `/api/totobola/draws` e `/api/lotteries/*/draw`.
  - Se bloquear, a app continua a funcionar com a colagem manual de jogos. Alternativa: uma tarefa agendada fora do Vercel (ex.: GitHub Actions) que obtém os dados e os guarda.
- **clubelo.com:** está em baixo desde que o testámos. Não é crítico, porque a Primeira Liga e as seleções têm modelo próprio.
- **Tempo do 1.º pedido** depois de um período sem tráfego.

## Variáveis de ambiente
| Variável | Onde | Valor |
|---|---|---|
| `DATA_DIR` | api | `/tmp/data` |
| `CORS_ORIGINS` | api | só no plano B |
| `FOOTBALL_DATA_API_KEY` | api | opcional |
| `GCP_PROJECT`, `BQ_DATASET` | api | opcional (BigQuery) |
| `DATABASE_URL` | api | plano 4 |
| `VITE_API_URL` | web | vazio (mesmo domínio) ou o URL do backend |
| `VITE_BUYMEACOFFEE_URL`, `VITE_PAYPAL_URL` | web | links reais |

## Domínio e aspetos legais
- **Domínio próprio** (ex.: `.pt` num registador da DNS.pt). **Não usar "santacasa"** no domínio nem no nome, por ser uma marca de terceiros.
- **Antes de abrir ao público:**
  - página de Termos de uso;
  - Política de privacidade;
  - aviso de jogo responsável (+18, já no rodapé);
  - "não afiliado à Santa Casa".
  - Com anúncios, será também preciso um banner de consentimento de cookies (ver o plano 5).
- **Análise de tráfego** para decidir sobre anúncios: Vercel Web Analytics (sem cookies).

## Passos
1. Git + GitHub.
2. Criar o `vercel.json` (Services), `.python-version` e `excludeFiles`.
3. Importar o repositório no Vercel (plano Hobby) e definir as variáveis de ambiente.
4. Preview deploy e checklist de verificação (abaixo).
5. Domínio próprio e deploy de produção.
6. Fase 2: Cron de treino + artefacto do modelo (com o plano 4).

## Verificação
- `GET /api/health` → `{"status":"ok"}`.
- Separadores Totobola e Totobola Extra carregam o concurso e os 13 jogos.
- Totoloto, Euromilhões e EuroDreams mostram o próximo sorteio.
- Calcular um desdobramento com fixos e duplas; o pop-up de critérios abre com os pesos.
- Botões de copiar e rodapé de apoio funcionam no telemóvel.
- 1.º pedido a frio: medir o tempo. Objetivo < 15 s na fase 1 e < 2 s na fase 2.
