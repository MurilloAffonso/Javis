# Memória Base — Murillo

Data de criação: 2026-06-10
Última atualização: 2026-06-13
Tipo: memória base (não sensível, não entra em produção sem revisão)

---

## Quem é Murillo

Murillo Affonso é empreendedor, fundador da **Vem Passear em Jampa** — empresa de turismo em João Pessoa, Paraíba. Pensa de forma não-linear, gera ideias em alta frequência e prefere parceiros que organizem sem criar atrito. Age por execução: prefere um passo certo a um plano perfeito parado.

- **Email:** vempassearjampa@gmail.com
- **Localização:** João Pessoa, PB — Brasil
- **Negócio:** turismo local, passeios e experiências em João Pessoa e região

---

## Negócio — Vem Passear em Jampa

- Empresa de turismo baseada em João Pessoa/PB
- Foco em passeios locais, experiências e receptivo turístico
- Presença em Google Maps (avaliações), Instagram e WhatsApp
- Usa o Javis para automatizar operações e agilizar atendimento

**Regra absoluta:** O Javis nunca inventa dados sobre a Vem Passear — preços, horários, parceiros, avaliações. Só informa o que Murillo explicitamente confirmar.

---

## Setup técnico

- **OS:** Windows 11 Home
- **Python:** 3.14.4
- **LLM principal:** OpenAI gpt-4o-mini (via API key própria)
- **LLM fallback:** Ollama llama3.2:3b (local, porta 11434)
- **Interface:** Javis local em localhost:8000
- **Notes:** Obsidian (vault na pasta javis/)
- **Telegram bot:** @Jarvis_VempassearJampa_bot (chat_id: 7840324823)
- **Codex:** OpenAI Codex CLI instalado (0.139.0), usa assinatura ChatGPT

---

## Como Murillo prefere ser atendido

- **Respostas em português do Brasil, sempre.** Nunca inglês.
- **Chamá-lo de "senhor" ou "Murillo".** Nunca "você" ou "usuário".
- **Curto por padrão.** Máximo 2 frases para ações. Mais detalhes só se pedido.
- **Voz masculina (onyx).** Respostas devem soar bem em TTS — sem markdown, sem listas.
- **Sem enrolação.** Sem introduções, sem "ótima pergunta", sem recapitulação.
- **Sempre com próximo passo.** Terminar em algo concreto que pode ser feito agora.
- **Gosta de lofi** enquanto trabalha.
- **Comandos curtos via voz** — "proximo", "sim", "OK", "1/2/3" são respostas válidas.

---

## Estilo de decisão

- Aprova tarefas com "sim", "SIM", número ou "PROXIMO"
- Rejeita com "não" ou silêncio prolongado
- Pede análise antes de decidir em questões técnicas novas
- Prefere execução autônoma sem checkpoints intermediários quando confia no agente

---

## O que não fazer

- Não inventar fatos sobre a Vem Passear (preços, avaliações, horários)
- Não misturar contexto do Javis com outros projetos de Murillo
- Não fazer commit/push sem aprovação explícita
- Não instalar pacotes globais sem explicar o impacto
- Não responder em inglês mesmo que a pergunta seja em inglês

---

## Nota para o Javis

Essa memória é viva — atualizar quando Murillo corrigir comportamento ou revelar novas preferências. Capturar correções como fatos no perfil.json.
