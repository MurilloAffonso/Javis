# codex-rotina-treinamento

Rotina automática que processa o material novo em `_treinamento/<area>/_entrada/`
e gera resumos densos em PT-BR via **Gemini 2.5 Flash** (rodando pelo Open Notebook),
salvando o resultado em `_treinamento/<area>/_resumos/` — pronto pra ser indexado
pelo RAG do Javis (`knowledge.py`).

## O que faz, em uma frase

> Para cada arquivo `.md`/`.txt` em `_entrada/`, cria a fonte no Open Notebook,
> dispara "Resumo Denso (PT-BR)" com Gemini, e escreve o resumo final em
> `_resumos/`. Idempotente — arquivos já feitos são pulados.

## Pré-requisitos

1. **Open Notebook no ar** em `localhost:5055`:
   ```powershell
   cd _ferramentas/integracoes/open-notebook
   docker compose up -d
   ```
2. **Ollama no ar** (pra embeddings — usado pelo Open Notebook em paralelo):
   ```powershell
   ollama serve
   ```
3. **Gemini configurado** no painel de Models (já está, validado em 2026-06-21).
4. **Transformação `resumo_denso_pt_br` existe** (criada via API; nome de objeto:
   `transformation:5n5eb7sgn2gie565v68s`).

## Uso

**Rodada normal** (só os arquivos novos):
```powershell
python _skills/codex-rotina-treinamento.py
```

**Reprocessar tudo** (ex.: depois de mudar o prompt da transformação):
```powershell
python _skills/codex-rotina-treinamento.py --force
```

**Só uma área específica** (vendas / conteudo / tecnico / estrategia):
```powershell
python _skills/codex-rotina-treinamento.py --areas vendas tecnico
```

## Onde fica o quê

| Arquivo | Função |
|---------|--------|
| `_treinamento/<area>/_entrada/*.md` | Material bruto que você joga |
| `_treinamento/<area>/_resumos/*.md` | Resumo PT-BR gerado pelo Gemini |
| `_treinamento/.processed.json` | Fingerprints dos arquivos já processados |
| `_logs/YYYY-MM-DD_codex-treinamento.md` | Log da rodada (sucesso/falhas) |

## Agendar a rotina noturna (Task Scheduler do Windows)

Cria uma tarefa que dispara o script todo dia às 03:00:

```powershell
$action = New-ScheduledTaskAction -Execute "python.exe" `
    -Argument "_skills\codex-rotina-treinamento.py" `
    -WorkingDirectory "C:\Users\noteacer\Desktop\javis"
$trigger = New-ScheduledTaskTrigger -Daily -At 3am
Register-ScheduledTask -TaskName "Javis-Codex-Treinamento" `
    -Action $action -Trigger $trigger -Description "Rotina noturna do Javis"
```

## Dispara pelo Codex CLI (se preferir)

```powershell
codex exec "rode o script _skills/codex-rotina-treinamento.py e me reporte o resultado"
```

> O Codex em si **não escreve os resumos** nesta versão — quem escreve é o
> Gemini, via Open Notebook. O Codex pode entrar quando quisermos uma camada de
> decisão (ex.: "esse conteúdo é off-topic, deveria ignorar?").

## Limitações conhecidas

- Conteúdo curto (só metadado de vídeo) gera resumo curto — esperado.
- Sem transcrição automática de vídeo: os arquivos de vídeo em `_entrada/` são
  só metadados; transcrição precisa entrar por outro fluxo (NotebookLM manual,
  Whisper, etc).
- Tier grátis do Gemini tem rate limit; processar muitos arquivos de uma vez
  pode dar HTTP 429. O script registra a falha e na próxima rodada tenta de novo.

## Arquitetura

```
_treinamento/<area>/_entrada/*.md
        │
        │  POST /api/sources/json  (cria fonte no Open Notebook)
        ▼
   [Open Notebook (Surreal)]
        │
        │  POST /api/transformations/execute
        │   (transformation = "resumo_denso_pt_br", model = gemini-2.5-flash)
        ▼
     [Google Gemini]
        │
        │  resumo PT-BR
        ▼
_treinamento/<area>/_resumos/<mesmo-nome>.md
        │
        │  (indexado por knowledge.py do Javis no próximo start)
        ▼
RAG do Javis pode responder sobre o conteúdo (buscar_conhecimento)
```
