# Javis Local Interface — Roadmap Técnico

Data: 2026-06-10  
Status: Protótipo v0 — CLI funcional, frontend estático

---

## 1. O que é a interface local do Javis

A **Javis Local Interface** é uma camada de execução local que complementa o Open WebUI.

Enquanto o Open WebUI cuida da conversa com o LLM, a interface local cuida de **ações no computador de Murillo**: abrir apps, tocar música, registrar ideias, consultar status do sistema.

Ela não substitui nada que já existe. Adiciona uma camada nova e segura por cima.

```
[Murillo]
    │
    ├── texto/voz
    │       │
    │       ▼
    │   [Command Router]  ← classifica intenção por regras
    │       │
    │       ├── conversa → Open WebUI / Ollama
    │       ├── ação segura → Actions executor → log
    │       └── ação perigosa → pede aprovação → log
    │
    └── resultado + log → frontend / terminal
```

---

## 2. Conexão com Open WebUI e Ollama

- Ações classificadas como `conversa` são **encaminhadas ao Open WebUI** via http://localhost:3000.
- Em fases futuras, o Command Router pode fazer chamadas diretas à API do Ollama (http://localhost:11434) para intenções que precisam de LLM.
- Na v0, não há chamada de LLM no Command Router — só regras por palavra-chave.

---

## 3. Conexão futura com o sandbox de voz

- O sandbox de voz (Open-LLM-VTuber, porta 12393) hoje faz: voz → faster-whisper → texto → Ollama → fala.
- Na próxima fase, o texto transcrito pelo faster-whisper pode ser enviado ao Command Router **antes** de ir ao Ollama.
- Fluxo futuro:

```
Voz → faster-whisper → texto
                          │
                          ▼
                   [Command Router]
                          │
                ┌─────────┴──────────┐
                │                    │
           ação local            conversa
                │                    │
          Actions executor      Ollama / Open WebUI
                │                    │
                └──────── log ───────┘
```

- **Não ativar ainda.** O sandbox de voz é separado por segurança.

---

## 4. Command Router

Arquivo: `backend/command_router.py`

Recebe texto livre, classifica em uma das seguintes intenções:

| Intent | Exemplos |
|--------|---------|
| `conversa` | "como vai?", "me explica X" |
| `abrir_navegador` | "abre o chrome", "navegar" |
| `abrir_youtube` | "abre o youtube" |
| `tocar_musica` | "toca música", "coloca uma playlist" |
| `abrir_openwebui` | "abre o open webui", "abre o javis" |
| `abrir_javis` | "abre a pasta do javis" |
| `abrir_vscode` | "abre o vscode", "abre o código" |
| `abrir_terminal` | "abre o terminal", "abre o powershell" |
| `abrir_projeto` | "abre o projeto X" |
| `registrar_ideia` | "anota isso", "captura ideia" |
| `status_sistema` | "status", "tá tudo funcionando?" |
| `acao_perigosa` | "apaga", "deleta", "formata", "instala" |
| `desconhecido` | qualquer outra coisa |

Retorna JSON:
```json
{
  "intent": "abrir_youtube",
  "confidence": "high",
  "risk_level": "low",
  "requires_approval": false,
  "action": "open_url",
  "reason": "palavra-chave 'youtube' detectada"
}
```

**Regras:**
- Sem LLM na v0 — só palavras-chave.
- Dúvida → `conversa` ou `desconhecido`.
- Ação perigosa sempre `requires_approval: true`.

---

## 5. Sistema de aprovação

Fluxo no CLI:

```
[Router] → requires_approval: true
    │
    ▼
"⚠️  Ação: [descrição]. Confirmar? (s/N): "
    │
    ├── s → executa + loga (approved: true)
    └── N → cancela + loga (approved: false)
```

No frontend futuro: botão "Aprovar / Cancelar" substituirá o prompt.

---

## 6. Sistema de logs

Arquivo: `logs/actions.jsonl` — uma linha JSON por evento.

```json
{
  "timestamp": "2026-06-10T22:00:00.000Z",
  "source": "cli",
  "user_text": "abre o youtube",
  "intent": "abrir_youtube",
  "risk_level": "low",
  "requires_approval": false,
  "approved": null,
  "action_result": "ok",
  "error": null,
  "duration_ms": 120
}
```

Tudo é logado: sucesso, erro, aprovação recusada, ação desconhecida.

---

## 7. O que executa sem aprovação

| Ação | Motivo |
|------|--------|
| Abrir navegador/YouTube | Só abre URL, não altera nada |
| Abrir Open WebUI | Só abre URL local |
| Abrir pasta do Javis | Só abre explorer |
| Abrir VS Code | Só abre editor |
| Tocar música (YouTube) | Só abre URL |
| Status do sistema | Só lê, não escreve |
| Registrar ideia | Escreve em `_ideias/` — baixo risco |

---

## 8. O que precisa de aprovação

| Ação | Motivo |
|------|--------|
| Abrir terminal | Pode executar comandos |
| Fechar aplicativos | Pode interromper trabalho |
| Mover/copiar arquivos | Risco de perda |
| Criar pastas fora do Javis | Pode poluir sistema |

---

## 9. O que fica proibido

- Deletar arquivos
- Instalar pacotes
- `git push` / `git reset` / `git force`
- Mexer em Docker
- Enviar mensagens (e-mail, WhatsApp, Slack)
- Automação de login
- Compras
- Executar shell arbitrário
- Qualquer ação fora do escopo do Javis

---

## Próximos passos previstos

1. v0 ✅ — CLI + Command Router + Actions + Logger + Frontend estático
2. v1 — Servir frontend via `python -m http.server`, conectar ao backend via FastAPI (com aprovação prévia)
3. v2 — Conectar sandbox de voz ao Command Router
4. v3 — Adicionar LLM ao Command Router para intenções ambíguas
5. v4 — Memória de ações + sugestões proativas
