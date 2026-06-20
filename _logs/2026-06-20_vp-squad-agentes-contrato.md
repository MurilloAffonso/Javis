# Squad de marketing da Vem Passear no backend — 5 agentes com contrato — 20/06

## O que foi feito
Implementei os 5 contratos revisados (`agentes-contratos.md`) como agentes reais
no backend, cada um com Input/Output/**Não faz**/Ferramentas no system prompt.

- **`backend/vp_squad.py`** (novo): dict `AGENTS` com os 5 (olheiro, nova, estudio,
  midas, analista). `_system_prompt()` monta o contrato como prompt (com a linha
  "O que você NÃO FAZ — NUNCA cruze esta linha") + Regra Ouro (não inventar
  preço/maré/vaga → [CONFIRMAR COM MURILLO]) + grounding dos arquivos LOCAIS
  (`_projetos/cerebro-jampa/`: linha-editorial pra Nova, templates-whatsapp pro
  Midas). Roda no cérebro único (claude_brain/assinatura). Self-contained: NÃO
  depende do vault externo CEREBRO.JAMPA (ao contrário do jampa_squad.py).
  - Midas tem a REGRA DE SEGURANÇA extra: resposta com preço/maré/vaga sai como
    RASCUNHO; ele não dá o envio final (decisão do Murillo na revisão).
- **`backend/server.py`**: endpoints `GET /vp/agents` (lista) e `POST /vp/agents/run`.

## Por que módulo novo (e não jampa_squad.py)
`jampa_squad.py` já tem Nova/Midas/Atlas, MAS carrega personas de SKILL.md do
vault em `Documents\CEREBRO.JAMPA` — frágil se o vault não estiver lá, e as
personas não são os contratos que fechamos. `vp_squad` embute o contrato inline e
aterra nos arquivos do próprio repo Javis → funciona sempre e reflete exatamente
o que foi revisado.

## Verificação (real)
- `py_compile` vp_squad.py + server.py — OK.
- `vp_squad.list_agents()` → 5 agentes; system prompt do Midas tem "NÃO FAZ" e
  "RASCUNHO"; system da Nova carrega a linha editorial.
- `GET /vp/agents` no servidor rodando → total 5.
- **Execução AO VIVO do Midas** (mensagem de cliente pedindo preço+vaga não
  confirmados): respeitou o contrato 100% — NÃO inventou preço, entregou RASCUNHO
  rotulado "não enviei, envio é seu", usou o template de primeiro contato, pediu
  os dados antes de cravar valor. O "Não faz" funcionou de verdade.
- `pytest tests/ -q` → 71 passed.

## Estado da amarração
| Camada | Status |
|---|---|
| Visual (Fluxo VP) | ✅ |
| Tarefas (Pipeline no Quadro, Raia 1 rodada) | ✅ |
| Contratos (agentes-contratos.md, 5 revisados) | ✅ |
| **Backend (vp_squad, 5 agentes executáveis)** | ✅ agora |
| UI mostrando o squad VP | ⚠️ endpoint pronto; falta plugar numa view |

## Próximo passo possível
Plugar `GET /vp/agents` numa view da interface (ex.: aba do Fluxo VP ou um painel
"Time da Vem Passear") pra você ver/acionar Nova, Midas etc. com o contrato à mostra.

**Sem commit/push — Murillo revisa e decide.**
