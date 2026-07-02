# Arquitetura Javes — Linhagem do Projeto

> Data: 2026-07-01 · Complementa [`GLOSSARIO-NOMES.md`](GLOSSARIO-NOMES.md) (nomes) e
> [`JAVIS-ARQUITETURA-ATUAL.md`](JAVIS-ARQUITETURA-ATUAL.md) (histórico técnico v0).
> Regra de ouro: **IA sugere, humano aprova.**

---

## Módulos (linhagem)

| Módulo | O que é | Onde vive |
|---|---|---|
| **A. Javes Core** | Orquestrador central: backend, cérebros (Claude/Codex via assinatura), command router, gates, telemetria | `_apps/javis-local-interface/backend/` |
| **B. Command Center** | Interface principal (dark SaaS): Chat, Operação, Missões, Vem Passear, Config | `_apps/javis-local-interface/frontend/command-center/` |
| **C. Vem Passear operacional** | Telas de operação da agência (projeto conectado): Resumo, Atendimento, Funil, Reservas, Voucher, Agenda, Pós-venda, Marketing, Resultados, Gates | abas VP dentro do Command Center (`viewVempassear` + `vp*`/`at*` em `app.js`) |
| **D. Agentes** | Apoio sob gate: sugestões, alertas, checklists. Persona via SKILL.md + cérebro forte | `_skills/`, registries + `/agents/run` |
| **E. Dados/registries** | Registries de UI (projetos, squads, agentes, skills); dados reais VP são locais/gitignored | `_apps/javis-local-interface/data/` |
| **F. Docs** | Glossário, arquitetura, roadmap, visão operacional | `_docs/`, `docs/` |
| **G. Legado/arquivo** | Interfaces e experimentos antigos (revisar antes de deletar) | `_arquivo/`, abas "· legado" na área VP |

Fronteira: **Javes ≠ Vem Passear.** A VP é projeto conectado por registro (via Cérebro Jampa);
o painel geral do Javes não se mistura com a operação da agência.

Nomenclatura: **Javes** em prosa/rótulo visível. **"Javis"** permanece só em id técnico,
path, arquivo, import e wake-word de voz (renomear é tarefa separada, não autorizada).

---

## Fluxo Javes (orquestração)

```
comando → classificar (intent) → missão → agente → sugestão/execução → gate (aprovação humana) → log → próximo passo
```

## Fluxo Vem Passear (operação)

```
lead → atendimento → proposta → reserva → voucher → agenda → passeio → pós-venda → avaliação
```

---

## Estado do MVP visual VP (2026-07-01)

- **Pronto (visual, dados sintéticos):** Resumo/Dashboard do dia, Atendimento 3 colunas
  (+checklist briefing), Funil Kanban, Reservas (tabela), Voucher (prévia), Agenda/Manifesto,
  Pós-venda, Marketing, Resultados, Gates.
- **Escrita real:** desligada — toda ação abre modal "fase visual — sem gravação real"
  ou está desabilitada com "em breve".
- **Leitura real (iniciada 2026-07-01):** Resumo, Atendimento e Funil leem leads locais via
  GET `/vp/clientes` quando o backend está online (marcados com 🔗 "leitura real", telefone
  mascarado, fallback sintético offline). Nenhum botão escreve.
- **Backend depois (nesta ordem):** testar MVP visual → corrigir bugs → ampliar leitura dos
  JSONs VP (passeios/pauta) → só então integrações (WhatsApp, voucher PDF, envio a parceiro).
- **Continua só visual:** publicar conteúdo, enviar mensagem, rodar agente com escrita.

## Checklist de validação manual

- [ ] `/command-center` carrega sem erro no console
- [ ] Aba Vem Passear abre; 10 abas operacionais + legado aparecem
- [ ] Resumo mostra dashboard do dia + prioridades + botões navegam
- [ ] Atendimento: 3 colunas, checklist briefing, alerta de briefing incompleto (lead Rafael & Bia)
- [ ] Funil: 9 colunas, cards com próxima ação, "Ver atendimento" navega
- [ ] Reservas/Voucher: nenhum dado real, telefone mascarado, voucher é prévia
- [ ] Agenda: filtros funcionam, "Copiar manifesto" copia texto dummy
- [ ] Pós-venda: copiar mensagem funciona, "marcar solicitado" só em memória
- [ ] Marketing: aviso "apoio" visível, aprovar/reprovar só abre modal
- [ ] Gates: 10 ações listadas, botões só simulam
- [ ] Nenhum POST/PATCH/DELETE novo disparado pelas telas VP novas
