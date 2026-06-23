# Teste live OpenRouter — Lote 1 (executado 23/06)

**Aprovação:** Murillo autorizou rede explicitamente. Custo real: **US$ 0,00**
(só modelos `:free`; falhas foram 429/404, sem cobrança). Prompts 100% sintéticos
(seção 14 do `OPENROUTER_TEST_PLAN_JAVIS.md`), sem dados reais, sem despacho de
tool, sem execução de código.

## Achado nº 1 (o mais importante): catálogo free expira em DIAS
Os 2 IDs congelados no plano em 22/06 **já não funcionavam em 23/06**:
- `meta-llama/llama-3.3-70b-instruct:free` → **429 rate-limited** upstream
  (provedor "Venice"). É o fallback citado no código.
- `nex-agi/nex-n2-pro:free` → **404, virou pago** ("use the paid slug
  `nex-agi/nex-n2-pro`").

Isso confirma empiricamente o que o veredito do Hermes e o próprio plano já
suspeitavam: **catálogo OpenRouter free é volátil — não dá pra cravar um ID free
fixo no código.** Qualquer uso sério do free precisa de fallback entre vários
IDs, não um só.

## Achado nº 2: provedor "Venice" rate-limita free agressivamente
Tanto `llama-3.3-70b:free` quanto `qwen3-next-80b:free` caíram em 429 do mesmo
provedor upstream ("Venice"), com `Retry-After: 30s`. Modelos roteados por outro
provedor passaram limpos. O rate-limit é do PROVEDOR, não da conta.

## Achado nº 3: gpt-oss-120b:free passou nos 3 eixos, com qualidade
Re-rodei o lote com 2 free válidos no catálogo ao vivo de 23/06:

| Modelo | P1 PT | P2 tool-use | P3 código | Veredito |
|---|---|---|---|---|
| `openai/gpt-oss-120b:free` | ✅ 5 frases, exemplos certos (174 tok, 11,5s) | ✅ tool-call exata `{"servico":"servico_demo"}` (38 tok, 6,9s) | ✅ função pura 8 linhas correta (81 tok, 6,7s) | **APROVADO 3/3** |
| `qwen/qwen3-next-80b-a3b-instruct:free` | ❌ 429 Venice | ❌ 429 Venice | ❌ 429 Venice | rate-limited, não avaliável |

Qualidade real do gpt-oss-120b (não só latência):
- **PT:** distinguiu urgente×importante corretamente, fechou com exemplos
  fictícios (vazamento de água / plano de expansão). Obediente ao limite de 5 frases.
- **Tool-use:** uma única chamada, schema respeitado, sem alucinação de resultado.
- **Código:** `set` de vistos + lista de saída, strip+lower+dedup preservando
  ordem, zero I/O. Idiomático.

## Achado nº 4 (lateral, mas relevante): o .env aponta OpenRouter pra modelo PAGO
`JAVIS_OPENROUTER_MODEL=google/gemini-2.5-flash-preview-05-20` no `.env`
sobrescreve o default free do código. Ou seja: na cascata real, se chegar no
OpenRouter, hoje ele chama um modelo **pago** da Google via OpenRouter, não o
llama free. Vale revisar se é intencional (agora que a rota Gemini grátis direta
existe, esse override perdeu o sentido).

## Recomendações
1. ✅ **APLICADA (23/06)** — default free do OpenRouter trocado de
   `meta-llama/llama-3.3-70b-instruct:free` para `openai/gpt-oss-120b:free` em
   `agent.py::_respond_openrouter()`. Passou no teste e não estava rate-limited.
2. ⏸️ **ADIADA** — fallback multi-ID free no `_respond_openrouter()`. Decisão:
   baixo retorno agora. OpenRouter é o ÚLTIMO elo da cascata (4 provedores falham
   antes, incluindo Gemini grátis); blindar o fallback do fallback não justifica
   uma frente com código+testes. Reabrir só se o OpenRouter passar a ser exercido
   de fato. Padrão a minerar continua válido (ver [[javis-hermes-veredito]]).
3. ✅ **APLICADA (23/06)** — override `JAVIS_OPENROUTER_MODEL=google/gemini-2.5-
   flash-preview-05-20` (PAGO) comentado no `.env`. Era redundante depois da rota
   Gemini grátis direta. Cascata agora cai no default free do código se chegar no
   OpenRouter. Suíte 138/138 após as duas mudanças.

## Artefatos
- Harness: `backend/_scratch/bench_openrouter_lote1.py` (descartável)
- Resultado bruto: `backend/_scratch/bench_lote1_resultado.json`
- Catálogo: 26 modelos `:free` no OpenRouter em 23/06 (consulta pública).

## Próximo passo
Decisão do Murillo sobre as 3 recomendações. A nº 2 (fallback multi-ID free)
seria uma frente ativa com código + testes; as nº 1 e 3 são ajustes pequenos
de config.
