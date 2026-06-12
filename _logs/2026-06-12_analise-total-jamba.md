# Análise Total — Jamba (Auditoria de Arquitetura)

**Data:** 2026-06-12 · **Auditor:** Claude Code (Opus)
**Estado:** 54/54 testes passando · sistema funcional em produção local

---

## 1. Raio-X do código (5.611 linhas)

| Arquivo | Linhas | Veredito |
|---|---|---|
| frontend/app.js | 1.311 | 🔴 MONOLITO — precisa dividir |
| backend/server.py | 605 | 🟡 rotas + lógica misturadas |
| backend/agent.py | 385 | 🟢 saudável (cérebro novo) |
| backend/orchestrator.py | 212 | 🔴 LEGADO PARCIAL — agent.py o substituiu |
| backend/actions.py | 203 | 🟢 ok |
| backend/knowledge.py | 194 | 🟢 ok (RAG novo) |
| backend/main.py | 92 | 🔴 LEGADO — candidato a remoção |
| backend/conclave.py | 103 | 🟡 usado só com checkbox ⚔️ |
| demais módulos | <160 cada | 🟢 ok |

## 2. Problemas encontrados (por gravidade)

### P1 — Dois cérebros convivendo (dívida técnica principal)
`orchestrator.py` (classify→brain→process) era o cérebro v2. O `agent.py`
(tool-use) o substituiu em /chat/stream e /voice, mas o orchestrator ainda é
chamado: no /chat legado, no conclave e no _classify morto. **Risco:** dois
caminhos de decisão = comportamento inconsistente entre endpoints.

### P2 — app.js monolito (1.311 linhas)
Contém: chat streaming + 4 engines de voz (VoiceEngine legado, WhisperRecorder,
AutoWhisperEngine, WakeWordEngine) + VoiceOrb + ReservoirChart + lembretes.
O VoiceEngine (Web Speech) virou código quase morto após o Whisper.

### P3 — Lógica duplicada no server.py
FAST_PATH + _looks_like_question duplicados em /chat/stream e /voice.
O /chat (não-stream) ainda usa o fluxo antigo do orchestrator — terceiro caminho.

### P4 — Duas camadas de provedor LLM
`llm_providers.py` (call_claude/call_openai/ollama) e `agent.py` (_respond_claude/
_respond_openai) não se conversam. Consolidar em uma só.

### P5 — Higiene
- ~~requirements.txt ausente~~ ✅ criado nesta auditoria
- .env protegido no .gitignore ✅
- CORS `*` + bind 0.0.0.0 — ok para uso local, MAS se expor na rede, qualquer
  dispositivo controla o PC. Falta trava (token simples) se um dia expor.
- Muitas mudanças sem commit — fazer commit de checkpoint (com aprovação).

## 3. Plano de Reestruturação (executar na próxima janela)

**Fase A — Unificar o cérebro (maior valor, ~1h de agente)**
1. /chat, /chat/stream e /voice → todos passam pelo `agent.respond()`
2. Extrair FAST_PATH p/ função única `try_fast_path(text)`
3. Orchestrator vira só o módulo do Conclave (renomear consciência disso)
4. Fundir lógica de provedores: agent usa llm_providers
5. Rodar os 54 testes após cada passo

**Fase B — Modularizar o frontend**
1. app.js → `chat.js`, `voice.js` (só Whisper+Wake), `orb.js`, `widgets.js`
2. Deletar VoiceEngine legado (Web Speech para captura)
3. index.html carrega os 4 módulos

**Fase C — Robustez**
1. Trava de acesso por token quando exposto na rede
2. Logging estruturado dos tool-calls do agente (auditoria do que ele executa)
3. Commit de checkpoint + tag `v2.1-jamba`

## 4. Estudo de concorrentes (consolidado do RESERVATORIOS.md)

| Projeto | O que o Jamba já tem igual/melhor | O que vale roubar de ideia |
|---|---|---|
| rezaulhreza/jarvis | voz+orbe+Ollama ✅ | criação de skills em runtime |
| Srijan-D/Jarvis | play música ✅, hotword ✅ | automação WhatsApp profunda |
| isair/jarvis | — | tools via MCP (padrão aberto, encaixa c/ Claude) |
| OpenJarvis (Stanford) | — | digest matinal ✅ (já temos rotina_matinal); skill discovery |
| Leon AI (leon-ai/leon) | — | arquitetura de skills instaláveis |

**Conclusão honesta:** o Jamba já cobre 80% do que esses repositórios fazem.
O diferencial deles que falta aqui: (1) skills plugáveis em runtime,
(2) MCP como protocolo de ferramentas. Ambos entram bem APÓS a Fase A.

## 5. Sobre o "repositório disco midi"
Nome veio embolado na transcrição de voz. Murillo: confirmar o nome exato do
repositório para eu avaliar o encaixe.

## 6. Próximo passo imediato
Executar Fase A na próxima janela de quota (sessão reseta ~21h00 de 12/06).
