# agents_catalog/selected — PLANO (proposta, não ativo)

Objetivo: conectar o repo externo `agency-agents` ao Javes como **catálogo de
especialistas por registro**, sem instalar os 232 agentes e sem tocar o runtime.

## Estrutura
```
agents_catalog/
  selected/
    JAVES_AGENT_REGISTRY.yaml   # 5 agentes iniciais + permissões
    PLAN.md                     # este arquivo
```

## Selecionados (5)
Minimal Change Engineer · Reality Checker · Software Architect ·
Voice AI Integration Engineer · SEO Specialist.

## Permissões (default)
- `can_execute: false` (nunca executa sozinho)
- `requires_approval: true` para qualquer ESCRITA (usa a confirmação forte já existente)
- scopes separados: `javes_core` / `vp_project` / `validation` (não misturar contexto)

## Fora de escopo agora
- Não instalar `agency-agents`.
- Não carregar o YAML no runtime.
- Não executar scripts externos.
- SEO Specialist é do projeto conectado Vem Passear Jampa, não do núcleo.

## Próxima fase (sob aprovação)
1. Ler as SKILL/descrições dos 5 no repo externo.
2. Mapear cada um para uma entrada real no backend (só quando aprovado).
3. Ativar 1 agente por vez, leitura/validação primeiro (Reality Checker).
