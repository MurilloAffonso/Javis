# Audit R5 - RAG embedder quality eval

Atualizado: 2026-07-09 15:06:09

Objetivo: comparar, no mesmo golden set, os providers `openai`, `local` e `ollama` para decidir o default do RAG por evidencia. O default continua `openai` ate haver evidencia melhor.

## Como rodar o baseline completo

Este bench e one-shot: nao e o servidor, nao muda o default e nao liga adaptador em runtime. Ele apenas respeita as variaveis de ambiente ja exportadas.

```powershell
ollama pull nomic-embed-text
$env:JAVIS_ENABLE_EXTERNAL_ADAPTERS = "true"
$env:JAVIS_OLLAMA_EMBED_MODEL = "nomic-embed-text"
$env:OPENAI_API_KEY = "..."  # opcional, so para baseline pago OpenAI
python scripts/rag_embedder_bench.py
```

Notas:
- `JAVIS_RAG_EMBEDDER` e irrelevante aqui; o bench itera `openai`, `local` e `ollama`.
- Se OpenAI, Ollama ou o gate `external_adapters` nao estiverem acessiveis, o provider fica `skipped` com motivo.
- O bench nao sobrescreve `_memoria/knowledge_index.json`.

Golden set: `_memoria/rag_eval_golden.json`  
K: 5

## Resultado

| Provider | Status | hit_rate | recall@5 | precision@5 | MRR | n | Nota |
|---|---:|---:|---:|---:|---:|---:|---|
| openai | skipped | - | - | - | - | - | OPENAI_API_KEY ausente; provider openai pulado. |
| local | ok | 0.5000 | 0.3542 | 0.1375 | 0.3802 | 16 | char 3-gram offline, dep-free |
| ollama | ok | 0.8750 | 0.7292 | 0.3125 | 0.7208 | 16 | - |

## Recomendacao

Ollama e candidato a default local: superou local em recall@k/MRR, sujeito a latencia e gate.

## Observacoes

- O provider `local` agora usa char 3-gram offline e sem dependencia externa.
- Baseline R5 anterior do hash puro: recall@5 0.2708, MRR 0.2021.
- A linha `local` acima e sempre re-medida pelo bench atual.

## JSON bruto

```json
{
  "status": "ok",
  "k": 5,
  "embedders": {
    "openai": {
      "status": "skipped",
      "note": "OPENAI_API_KEY ausente; provider openai pulado."
    },
    "local": {
      "k": 5,
      "n": 16,
      "hit_rate": 0.5,
      "recall@k": 0.3542,
      "precision@k": 0.1375,
      "mrr": 0.3802,
      "status": "ok"
    },
    "ollama": {
      "k": 5,
      "n": 16,
      "hit_rate": 0.875,
      "recall@k": 0.7292,
      "precision@k": 0.3125,
      "mrr": 0.7208,
      "status": "ok"
    }
  },
  "recommendation": "Ollama e candidato a default local: superou local em recall@k/MRR, sujeito a latencia e gate."
}
```
