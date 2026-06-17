# Agentic GTM Automation (Amar4002) — resumo

**Fonte:** https://github.com/Amar4002/Agentic-GTM-Automation-
**Coletado por:** esquadrão de estudo (vendas) em 2026-06-16. Resumo escrito por Claude lendo o README real, não NotebookLM.

## O que é
Sistema que lê dados de CRM, decide quais leads precisam de follow-up (baseado em dias desde último contato + contexto da última mensagem), gera mensagem personalizada via Gemini e envia via WhatsApp/Twilio, registrando status de entrega.

## Por que importa pro Javis
É exatamente a lacuna que falta no fluxo do Vem Passear Jampa hoje: os templates de WhatsApp (`templates-whatsapp.md`, já prontos no backlog) são estáticos — alguém precisa decidir manualmente quando reenviar pra um lead. Esse repo mostra a regra de decisão mínima viável ("dias desde contato + contexto") pra automatizar esse gatilho, sem precisar reinventar nada complexo.

## Próximo passo prático
Nenhuma ação imediata — não há CRM estruturado nem número de WhatsApp Business API plugado no Javis ainda. Se/quando isso existir, essa lógica de "decidir quando fazer follow-up" é referência direta pra implementar.
