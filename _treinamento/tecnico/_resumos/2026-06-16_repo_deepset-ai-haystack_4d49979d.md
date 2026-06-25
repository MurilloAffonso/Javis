# Resumo: 2026-06-16_repo_deepset-ai-haystack_4d49979d

Área: tecnico
Resumido em: 2026-06-25 (Javis / Claude assinatura)
Origem: _entrada/2026-06-16_repo_deepset-ai-haystack_4d49979d.md

## Resumo — deepset-ai/haystack

Haystack é um framework open-source de orquestração de IA para construir aplicações LLM prontas para produção. A ideia central é montar **pipelines modulares** e **workflows de agentes** com controle explícito sobre cada etapa: recuperação de informação (retrieval), roteamento, memória e geração de texto. Serve para RAG, busca semântica, sistemas conversacionais e agentes que escalam. É a alternativa "engenharia séria" para quem não quer um chatbot improvisado, e sim um fluxo controlável e auditável.

## Aprendizados aplicáveis ao negócio

- **Pipeline > prompt solto.** Tanto Vem Passear quanto Javis ganham se cada tarefa virar um fluxo com etapas explícitas (buscar → rotear → responder), em vez de um único prompt fazendo tudo. Isso é exatamente o que você já vem fazendo com squads/command_router.
- **RAG é o caminho para respostas confiáveis.** Para a Vem Passear, um agente de atendimento que busca em base própria (passeios, preços, roteiros de João Pessoa) responde sem inventar — Haystack mostra o padrão "recuperar antes de gerar".
- **Memória e roteamento como peças separadas.** O Javis já tem cérebro + memória Obsidian; Haystack valida a arquitetura de tratar memória e roteamento como componentes plugáveis, não embutidos no modelo.
- **Modularidade = trocar de modelo sem reescrever.** Combina com sua dor de OpenRouter/free volátil: pipeline modular deixa você trocar o cérebro (Gemini, gpt-oss, Claude) sem refazer a aplicação.

## Ações concretas

1. **Avaliar Haystack como referência de arquitetura** para um pipeline RAG de atendimento da Vem Passear (base de roteiros/preços → busca → resposta), comparando com o que o Javis já faz hoje no backend.
2. Cumprir o próximo passo do material: **subir no NotebookLM** e colar o resumo processado em `_resumos/`.
