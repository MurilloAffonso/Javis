# Veredito — agiresearch/AIOS faz sentido pro Javes?

Data: 2026-07-02
Decisão: **minerar conceitos, NÃO adotar como substrato** (mesmo veredito do Hermes, 23/06).

## O que é
Kernel de agentes em Python (3.10/3.11, ~6k ⭐): Scheduler, Context Manager, Memory
Manager, Storage Manager, Tool Manager (com VM/MCP isolado). Agentes falam com o
kernel via "syscalls" agendadas. SDK = Cerebrum. Suporta AutoGen, MetaGPT, OpenAGI.

## Por que NÃO adotar (bloqueios duros)
1. **LLM só via API** — Anthropic entra por API key paga; o Javes roda 100% via
   assinatura Claude (CLI headless). Alternativa seria Ollama local (GTX 1650 4GB =
   llama3.2:3b fraco). Mesmo bloqueio do OpenRouter/Hermes.
2. **Porta 8000** — colide com o server.py do Javes.
3. **Linux-first** (launch via bash script) — Windows incerto.
4. Adotar = trocar substrato inteiro; decisão vigente é `_brain` intocado.
5. Frameworks dele (AutoGen/MetaGPT) ≠ modelo do Javes (SKILL.md + cérebro forte).

## O que MINERAR (faz sentido)
1. **Syscall de agente** — toda ação de agente vira chamada padronizada que passa
   por scheduler/gate antes de executar = formalização exata dos gates do Javes.
2. **Context Manager** — snapshot/restore de contexto entre execuções (evoluir
   `_estado/` e `_sessoes/` nessa direção).
3. **Scheduler de missões** — fila com prioridade em vez de disparo manual.
4. **Tool Manager isolado (VM/MCP)** — modelo pra "política central de segurança"
   (camada única citada no glossário, ainda a definir).

## Próximo passo
Quando formos desenhar o kernel de orquestração do Javes, usar o AIOS como
referência de desenho (syscall + scheduler + gates), não como dependência.
Material de estudo já em `_treinamento/tecnico/_entrada/` (repo + vídeo Alan Nicolas).
