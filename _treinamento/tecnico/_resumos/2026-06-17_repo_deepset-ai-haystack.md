# Haystack (deepset-ai/haystack) — resumo

**Fonte:** https://github.com/deepset-ai/haystack (25.6k estrelas)
**Coletado por:** esquadrão de estudo (técnico) em 2026-06-16. Resumo escrito por Claude lendo o README real do repositório, não NotebookLM.

## O que é
Framework open-source de orquestração de IA focado em RAG (retrieval-augmented generation) e agentes prontos para produção — pipelines modulares com controle explícito sobre retrieval, roteamento, memória e geração.

## Por que importa pro Javis
O Javis já tem RAG próprio (`knowledge.py` indexando `_treinamento`, `_memoria` etc.). O Haystack é referência direta de como estruturar RAG de forma mais robusta — pipelines com retrieval+roteamento explícitos, em vez do que hoje é mais simples. Não é "trocar o RAG do Javis por isso", é "se o RAG do Javis crescer e precisar de roteamento mais sofisticado entre fontes (_treinamento por área, _memoria, projetos externos), olhar como o Haystack resolve isso".

## Próximo passo prático
Nenhuma ação imediata — é referência de arquitetura. Revisitar se o RAG do Javis precisar de roteamento multi-fonte mais sofisticado do que hoje.
