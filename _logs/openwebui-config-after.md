# Open WebUI — Estado Após a Configuração

**Data/hora:** 2026-06-10

---

## Modelos criados/atualizados

| Modelo | ID | Base | Temperatura | num_predict | Stop |
|--------|-----|------|-------------|-------------|------|
| Javis Geral | javis-geral | llama3.2:3b | 0.3 | 500 | Acompanhamento |
| Javis Ideias | javis-ideias | llama3.2:3b | 0.1 | 280 | Acompanhamento |
| Javis Projetos | javis-projetos | llama3.2:3b | 0.2 | 400 | Acompanhamento |
| Javis Próximo Passo | javis-proximo-passo | llama3.2:3b | 0.1 | 250 | Acompanhamento |
| Javis Decisões | javis-decisoes | llama3.2:3b | 0.1 | 220 | Acompanhamento |
| Javis Revisor | javis-revisor | llama3.2:3b | 0.2 | 350 | Acompanhamento |

---

## Capacidades configuradas

| Capacidade | Estado |
|-----------|--------|
| Visão | ✅ ON |
| Upload de arquivo | ✅ ON |
| Contexto do arquivo | ✅ ON |
| Citações | ✅ ON |
| Atualizações de estado | ✅ ON |
| Pesquisa na Web | ❌ OFF |
| Geração de Imagem | ❌ OFF |
| Interpretador de Código | ❌ OFF |
| Terminal | ❌ OFF |
| Ferramentas Integradas | ❌ OFF |

---

## Conexões

| Conexão | Estado |
|---------|--------|
| API OpenAI | ❌ DESLIGADA |
| Ollama API | ✅ LIGADA |
| URL Ollama | http://host.docker.internal:11434 |

---

## Testes realizados

### Javis Ideias
- Mensagem: "Tive uma ideia: criar um sistema simples para organizar minhas ideias, projetos e próximos passos."
- Primeira linha: `💡 IDEIA CAPTURADA` ✅
- "Acompanhamento" presente: NÃO ✅
- Todos os campos presentes: Resumo, Categoria, Valor potencial, Próximo passo mínimo, Destino ✅

### Javis Próximo Passo
- Mensagem: "Estou com muitas ideias e não sei por onde começar."
- Primeira linha: `🎯 PRÓXIMO PASSO` ✅
- "Acompanhamento" presente: NÃO ✅
- Todos os campos presentes: Situação atual, Prioridade principal, O que fazer agora, O que deixar para depois, Ação de 15 minutos ✅

### Javis Decisões
- Mensagem: "Decidi que o Javis vai começar simples, focado em ideias, projetos e próximos passos."
- Primeira linha: `📌 DECISÃO REGISTRADA` ✅
- "Acompanhamento" presente: NÃO ✅
- Todos os campos presentes: Decisão, Motivo, Contexto, Consequência, Próxima ação ✅

---

## O que funcionou

- Todos os 6 modelos criados com sucesso via API `/api/v1/models/create`
- System prompts aplicados corretamente via `/api/v1/models/model/update`
- Capabilities perigosas desabilitadas (web, terminal, código, imagem)
- Sequência de parada "Acompanhamento" configurada em todos
- API OpenAI desligada no painel Admin

## O que precisa ajustar no futuro

- O modelo llama3.2:3b às vezes ignora a lista de categorias definida no prompt — isso é limitação do modelo pequeno, não de configuração
- Os modelos Javis Projetos e Javis Revisor não foram testados nesta sessão — testar manualmente na próxima
- O modelo original "Javis" (id: javis-) foi mantido sem alterações — pode ser desativado ou renomeado futuramente
