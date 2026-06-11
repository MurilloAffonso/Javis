# Retomar após sessão de robustez (ECC)

Data: 2026-06-11

---

## Onde o projeto estava antes do ECC

**Tarefa em andamento:**
Conectar transcrição real do Open-LLM-VTuber ao voice_bridge.py em dry-run,
revisar logs e só depois liberar execução por voz para risk_level low.

**Estado do voice_bridge:**
- Criado em `_apps/javis-local-interface/backend/voice_bridge.py`
- dry_run = True (permanente até aprovação de Murillo)
- 5/5 testes de classificação passando
- Logs gravados em `logs/actions.jsonl` com source: "voice"

**Estado do Open-LLM-VTuber:**
- Pipeline validado (voz → transcrição → LLM → fala)
- Não conectado ao voice_bridge ainda
- Iniciado com: `cd _ferramentas/voz-sandbox && uv run run_server.py`

---

## O que foi feito na sessão de ECC

1. Checkpoint criado: `_logs/checkpoint-before-ecc.md`
2. ECC clonado: `_referencias/ECC/` (shallow, não instalado)
3. Análise criada: `_ferramentas/ecc/ANALISE-ECC-PARA-JAVIS.md`
4. Plano de importação: `_ferramentas/ecc/PLANO-DE-IMPORTACAO-SELETIVA.md`
5. AGENTS.md atualizado: seção "Regras de Operação Segura do Javis" (guardrails ECC)
6. 3 skills melhoradas: `executar-com-aprovacao`, `analisar-arquivo`, `revisar-plano`
7. 5 skills novas: `checkpoint-antes-de-mudar`, `auditar-seguranca-local`,
   `testar-antes-de-integrar`, `research-first`, `quality-gate`
8. 2 arquivos de teste criados: `tests/test_command_router.py` (27/27), `tests/test_voice_bridge.py` (21/21)
9. `_docs/JAVIS-ARQUITETURA-ATUAL.md` criado (visão geral completa)

---

## Próximo passo exato após o ECC

**Tarefa:** Conectar transcrição real do Open-LLM-VTuber ao voice_bridge.py em dry-run.

**Sequência:**
1. Iniciar o sandbox de voz:
   ```powershell
   cd _ferramentas/voz-sandbox
   uv run run_server.py
   ```
2. Usar a interface normalmente — falar comandos reais (ex: "abre o youtube", "status")
3. Em paralelo, rodar voice_bridge manualmente com os mesmos comandos:
   ```powershell
   cd _apps/javis-local-interface
   python backend/voice_bridge.py "abre o youtube"
   python backend/voice_bridge.py "status do sistema"
   ```
4. Revisar `logs/actions.jsonl` — confirmar que intents batem com o que foi falado
5. Somente após revisão e aprovação explícita de Murillo: liberar execução (dry_run → False)
6. Integrar ao `single_conversation.py` do Open-LLM-VTuber (requer checkpoint antes)

**Arquivos a tocar na integração:**
- `_ferramentas/voz-sandbox/src/open_llm_vtuber/conversations/single_conversation.py`
  (adicionar chamada ao voice_bridge antes de enviar ao Ollama)
- `_apps/javis-local-interface/backend/voice_bridge.py`
  (remover dry_run fixo, aceitar flag de execução)

**Antes de tocar esses arquivos:**
- Criar checkpoint: `_logs/checkpoint-YYYY-MM-DD_voice-bridge-integration.md`
- Rodar testes: `python tests/test_voice_bridge.py` — deve ser 21/21
- Obter aprovação explícita de Murillo

---

## Prompt para continuar

```
Você é o Arquiteto de Integração do Javis.

Contexto: a sessão de robustez (ECC) foi concluída.
Próximo passo: conectar transcrição real do Open-LLM-VTuber ao voice_bridge.py.

Antes de qualquer integração:
1. Criar checkpoint em _logs/
2. Rodar todos os testes (tests/test_command_router.py + tests/test_voice_bridge.py)
3. Mostrar resultado a Murillo e pedir aprovação
4. Somente após aprovação: editar single_conversation.py

Regras de segurança vigentes:
- Não instalar nada
- Não mexer no Open WebUI
- Não mexer no Docker
- Não alterar Ollama
- Não fazer commit
- Não fazer push
- Não liberar dry_run sem aprovação explícita
```
