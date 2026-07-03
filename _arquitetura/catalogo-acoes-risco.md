# Catálogo de Ações & Risco — endpoints de escrita do Javis

> Origem: tela "Ações" do command-center (removida da UI em 2026-07-03 por ser
> estática/bloqueada — decisão de minimalismo). O conteúdo vive aqui como referência
> de arquitetura. Código original: `_arquivo/command-center-views/acoes.js`.
> **Uso principal:** guia pra fase de conectar endpoints órfãos na UI — cada ação já
> tem risco classificado e regra de confirmação definida.

## Níveis de risco
| Nível | Significado |
|---|---|
| leitura | não altera dado |
| leve | escrita leve (cadastros simples) |
| op | escrita operacional (muda status/fluxo) |
| pesado | processo caro (LLM em lote, download) |
| alto | alto risco (exclusão, publicação, execução de agente) |
| bloqueado | sem endpoint exposto ainda |

## Núcleo Javes · Chat & Voz
| Ação | Endpoint | Risco | UI? | Confirmação | Próxima fase |
|---|---|---|---|---|---|
| Conversar (streaming) | POST /chat/stream | leve | sim | não | já em uso; grava histórico |
| Transcrever voz | POST /transcribe | leve | sim | não | validar com microfone real |
| Falar resposta (TTS) | POST /tts | leitura | sim | não | gera áudio, sem escrita de dado |

## Operação · Kanban & Gates
> 🧪 Piloto de escrita segura: ações de escrita da Operação já passam por confirmação
> forte (digitar CONFIRMAR). Só devem rodar em task descartável.

| Ação | Endpoint | Risco | UI? | Confirmação | Próxima fase |
|---|---|---|---|---|---|
| Mover status (Kanban) | POST /tasks/{id}/status | op | sim | sim | testar com task descartável |
| Aprovar/Rejeitar gate | POST /approvals/{id}/decide | alto | sim | sim | decisão humana; task descartável |
| Rodar Estúdio (Gate 2) | POST /tasks/{id}/run-studio | op | sim | sim | gera criativos (modo seguro) |
| Preparar Distribuição (G3) | POST /tasks/{id}/prepare-distribution | op | sim | sim | gera pacote (modo seguro) |
| Concluir entidade | POST /tasks/{id}/complete | op | **não** | sim | encerra task + digest |

## Missões
| Ação | Endpoint | Risco | UI? | Confirmação | Próxima fase |
|---|---|---|---|---|---|
| Marcar node como done | POST /missions/{id}/nodes/{node}/done | op | **não** | sim | altera backlog real |

## Rotina · Lembretes
| Ação | Endpoint | Risco | UI? | Confirmação | Próxima fase |
|---|---|---|---|---|---|
| Criar lembrete | (sem endpoint exposto) | bloqueado | não | sim | falta endpoint de criação |

## Treino / Scout
| Ação | Endpoint | Risco | UI? | Confirmação | Próxima fase |
|---|---|---|---|---|---|
| Scout por área | POST /treinamento/scout/{area} | pesado | **não** | sim | processo pesado; aviso de tempo |
| Scout geral | POST /treinamento/scout-all | pesado | **não** | sim | processo pesado |
| Resumir área | POST /treinamento/resumir/{area} | pesado | **não** | sim | LLM em lote |
| Treinar do YouTube | POST /train/youtube | alto | **não** | sim | download + processamento |

## Projeto conectado · Vem Passear Jampa
| Ação | Endpoint | Risco | UI? | Confirmação | Próxima fase |
|---|---|---|---|---|---|
| Cadastrar passeio | POST /vp/passeios | leve | não* | sim | dado do projeto conectado |
| Remover passeio | DELETE /vp/passeios/{id} | alto | não | sim | exclusão de dado real |
| Cadastrar cliente/lead | POST /vp/clientes | leve | não* | sim | dado sensível |
| Mudar status cliente | PATCH /vp/clientes/{id} | op | não | sim | altera lead real |
| Remover cliente | DELETE /vp/clientes/{id} | alto | não | sim | exclusão de dado real |
| Gerar conteúdo (LLM) | POST /vp/conteudo | pesado | não | sim | chama o cérebro/LLM |
| Salvar conteúdo | POST /vp/conteudos | leve | não* | sim | grava na biblioteca |
| Criar pauta | POST /vp/pauta | leve | não* | sim | linha editorial |
| Publicar/replanejar pauta | PATCH /vp/pauta/{id} | op | não | sim | muda status de publicação |
| Remover pauta | DELETE /vp/pauta/{id} | alto | não | sim | exclusão de dado real |
| Rodar agente VP | POST /vp/agents/run | alto | não | sim | execução de agente do projeto |

\* tinha form nas abas "legado" da VP, removidas da UI em 2026-07-03 junto com esta tela.

## Upload
| Ação | Endpoint | Risco | UI? | Confirmação | Próxima fase |
|---|---|---|---|---|---|
| Upload de arquivo | POST /upload | op | não | sim | fase própria; validar tipo/tamanho |

## Conclave / Agentes
| Ação | Endpoint | Risco | UI? | Confirmação | Próxima fase |
|---|---|---|---|---|---|
| Rodar Conclave | POST /debate | pesado | sim | sim | já em uso; 1–3 min |
| Chat com Conclave | POST /chat/stream (use_conclave) | pesado | sim | não | toggle ⚔️ no Chat |
