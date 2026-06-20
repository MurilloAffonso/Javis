# Remover Ollama — Claude (assinatura) como base de TUDO — 19/06

## Decisão do Murillo

"Não quero subir nada do Ollama. Deixa todo o Claude como base de tudo, tira
tudo o que for do Ollama." Concordei: o Ollama vivia offline, nunca foi reserva
real — só transformava "sem cota" num erro técnico confuso ("Ollama fora do ar").
Sem ele, a falha fica HONESTA: o Javis diz "estou sem cota, senhor" e pronto.

## O que foi feito (todas as chamadas de Ollama arrancadas)

- **`llm_providers.py`**: removido `_call_ollama` e as constantes OLLAMA_*. Sem
  `import requests`. `call_claude`/`stream_claude`: se a assinatura faltar/zerar,
  devolvem mensagem clara (`_SEM_CEREBRO`) em vez de cair no Ollama. `call_openai`
  segue alias de `call_claude`. `embed()` (OpenAI) mantido — não é cérebro.
- **`agents/specialized.py`**: `BaseAgent.execute()` (os ~14 agentes/specialists)
  agora chama `claude_brain.answer(content, system=persona)` em vez de POST no
  Ollama. `DEFAULT_MODEL="claude"`, sem `import requests`.
- **`agents/meta.py`**: `AIOSMaster.plan()` agora usa `claude_brain.answer` +
  json.loads (mantido o fallback-dict se vier inválido). Sem Ollama/requests.
- **`agent_runner.py`**: removidos os níveis 2 (OpenAI) e 3 (Ollama) — eram
  redundantes (todos viram assinatura agora). Só Claude; se faltar, erro claro.
- **`orchestrator.py`** / **`conclave.py`**: removidas constantes OLLAMA_* e
  `import requests` (mortos — `_main_brain`/`_call` já usavam call_claude/openai).
  `DEFAULT_MODEL="claude"` só como rótulo.
- **`server.py`**: tirado "Ollama" do monitor `SERVICES`; defaults de request body
  `"llama3.2:3b"` → `"claude"`; comentários do passo 5/_brain atualizados (sem
  "fallback Ollama").
- **`actions.py`**: status do sistema não checa mais a porta 11434.
- **`agent.py`**: descrição da ferramenta `status_sistema` sem citar Ollama.
- **`claude_brain.py`**: docstring atualizada (cérebro único, sem fallback local).

## Arquitetura final do cérebro

TUDO no Claude pela assinatura, caminho único:
- Voz/chat/ação (`agent.respond`), conversa (`_brain`), raciocínio profundo
  (`claude_brain`), Conclave, agentes da mente (specialized/meta), squads,
  analyzers, orchestrator — todos batem no `claude_brain` (subprocess `claude -p`).
- Único OpenAI restante: voz I/O (`/transcribe` Whisper, TTS `tts-1`) e
  `embed()` (busca semântica) — não há equivalente na assinatura, mantidos.
- Sem cota / Claude Code deslogado → mensagem clara, não erro técnico, não Ollama.

## Verificação

- `py_compile` de 10 módulos editados — OK.
- `pytest tests/ -q` → 71 passed.
- Sem `requests.`/`OLLAMA_URL`/`11434` sobrando no backend (grep limpo).
- Fiação provada com monkeypatch (custo zero de cota): agente Architect →
  chama a assinatura; Conclave → 3 chamadas na assinatura (Crítico/Advogado/
  Sintetizador). Zero Ollama.

## Custo conhecido (aceito pelo Murillo)
Sem modo offline. Quando a cota semanal da assinatura zera (aconteceu hoje), o
Javis fica sem cérebro até o reset — mas agora avisa isso com clareza.

**Sem commit/push — Murillo revisa e decide.**
