# Repositórios Avaliados para o Javis

Data de avaliação: 2026-06-10

---

## 1. CodeGraph
**Repositório:** https://github.com/colbymchenry/codegraph  
**Status:** ✅ Aprovado para teste  
**Versão instalada:** 0.9.9 (já instalada globalmente)  
**Estado no projeto:** Não inicializado (precisa de `codegraph init`)

### O que faz
CodeGraph indexa o código do projeto em um grafo de símbolos, permitindo que Claude Code navegue a base de código por semântica em vez de ler arquivos inteiros. Complementa o LeanCTX ao nível de estrutura — LeanCTX reduz tokens por compressão, CodeGraph reduz tokens por navegação seletiva.

### Por que faz sentido para o Javis
- Quando o Javis crescer (skills, agentes, prompts), Claude precisará entender relações entre arquivos sem ler tudo.
- Perguntas do tipo "o que chama essa função?" ou "quais arquivos dependem desse módulo?" se tornam baratas.
- Integra como MCP server — mesmo modelo de uso que LeanCTX.

### Próximo passo (aguardando aprovação)
Inicializar no projeto com:
```bash
cd C:\Users\noteacer\Desktop\javis
codegraph init
```
Depois verificar:
```bash
codegraph status
codegraph index
```

### Riscos
- Nenhum risco alto. `codegraph init` cria um índice local (`.codegraph/`), sem dependências externas.
- Adicionar `.codegraph/` ao `.gitignore` antes de inicializar (evita commitar o índice).
- Não altera Open WebUI, Ollama, nem LeanCTX.

---

## 2. agent-skills
**Repositório:** https://github.com/addyosmani/agent-skills  
**Status:** ✅ Aprovado como referência de metodologia  
**Instalação:** NÃO instalar agora

### O que faz
Coleção de skills para Claude Code com fluxo estruturado de desenvolvimento:
`/spec` → `/plan` → `/build` → `/test` → `/review`

Cada skill é um arquivo `.md` ou `.yaml` que instrui o Claude a seguir um processo definido. Útil para criar features de forma disciplinada.

### Por que faz sentido para o Javis
- O Javis terá skills próprias em `_skills/`.
- A metodologia do agent-skills serve de modelo para criar skills do Javis.
- Pode selecionar skills individuais relevantes no futuro (ex: `/spec`, `/plan`).

### Próximo passo
Estudar o repositório. Selecionar skills relevantes individualmente quando necessário.
Não importar o repositório completo.

### Riscos
- Nenhum risco se usado apenas como referência.
- Risco se instalado completo: pode sobrescrever configurações globais do Claude Code.

---

## 3. ai-engineering-from-scratch
**Repositório:** https://github.com/rohitg00/ai-engineering-from-scratch  
**Status:** 📚 Referência de estudo — não instalar agora  
**Instalação:** NÃO instalar

### O que faz
Curso/guia progressivo de engenharia de IA do zero. Cobre fundamentos, RAG, agentes, etc.

### Por que NÃO instalar agora
- Javis não está na fase de estudo de fundamentos — está em fase de construção.
- Instalar agora traria dependências desnecessárias (Python notebooks, libs pesadas).
- Conflito potencial com Python 3.14 (mesmo problema do Headroom).

### Quando revisar
Quando o Javis precisar implementar RAG próprio, agentes avançados ou integração com fontes de dados.

---

## Resumo de Decisões (2026-06-10 v1)

| Ferramenta | Status | Ação |
|---|---|---|
| LeanCTX | ✅ Ativo | Já funcionando como MCP |
| CodeGraph | ✅ Aprovado | Aguardando `codegraph init` |
| agent-skills | ✅ Referência | Selecionar skills individualmente |
| ai-engineering-from-scratch | 📚 Estudo | Consultar quando necessário |
| Headroom | ⏸ Pendente | Aguardando workaround Python 3.14 |

---

# Avaliação GitHub Trending — 2026-06-10

Análise do GitHub Trending (diário, semanal, mensal) com foco na visão do Javis como superassistente pessoal local.

---

## 4. agentmemory
**Repositório:** https://github.com/rohitg00/agentmemory  
**Stars:** ~22k  
**Status:** ✅ APROVADO — Introduzir agora  
**Stack:** TypeScript, SQLite, embeddings locais

### O que faz
Memória persistente de 4 camadas para agentes AI. Plugin nativo para Claude Code com hooks automáticos. 95% recall, 92% redução de tokens. Funciona com Ollama para embeddings (gratuito, local). Sem banco externo.

### Instalação
```bash
npm install -g @agentmemory/agentmemory
agentmemory connect claude-code
```

### Por que faz sentido
O Javis não lembra nada entre sessões do Claude Code. Com agentmemory, padrões de trabalho, decisões e contexto de projetos ficam disponíveis automaticamente.

### Riscos
Projeto novo (22k). Runtime próprio (`iii`). Monitorar estabilidade.

---

## 5. markitdown
**Repositório:** https://github.com/microsoft/markitdown  
**Stars:** ~150k  
**Status:** ✅ APROVADO — Introduzir agora  
**Stack:** Python

### O que faz
Converte PDFs, Word, Excel, PowerPoint, imagens, áudio, HTML, CSV para Markdown. Feito para LLMs. CLI + biblioteca Python.

### Instalação
```bash
pip install 'markitdown[all]'
```

### Por que faz sentido
Habilita a skill `analisar-arquivo` — Murillo joga qualquer documento e o Javis processa. 150k stars, Microsoft, zero risco.

---

## 6. Open-LLM-VTuber
**Repositório:** https://github.com/Open-LLM-VTuber/Open-LLM-VTuber  
**Stars:** ~10k  
**Status:** B — Testar em sandbox  
**Stack:** Python, Docker

### O que faz
Interface de voz bidirecional com avatar Live2D. STT + TTS local. Suporte nativo ao Ollama, Docker, Windows. Interrupção de voz sem headphone.

### Como entraria no Javis
Camada de voz — Murillo fala, Javis responde em voz. Avatar é opcional. Pode rodar paralelo ao Open WebUI.

### Riscos
Dependências de áudio no Windows são instáveis. Testar em sandbox antes de integrar ao ambiente principal.

---

## 7. tinyhumansai/openhuman
**Repositório:** https://github.com/tinyhumansai/openhuman  
**Stars:** ~31k  
**Status:** B — Sandbox (benchmarking de arquitetura)  
**Stack:** Rust/Tauri, TypeScript

### O que faz
Assistente pessoal desktop completo — memória local, cofre Markdown, 118 integrações, STT/TTS, compressão de tokens, mascote.

### Por que NÃO integrar
Visão similar ao Javis mas arquitetura diferente. Usa serviços gerenciados para partes críticas. Serve como benchmark de o que o Javis pode se tornar.

---

## 8. NousResearch/hermes-agent
**Repositório:** https://github.com/NousResearch/hermes-agent  
**Stars:** ~189k  
**Status:** C — Inspiração de arquitetura  

### O que faz
Agente auto-melhorável. Loop de aprendizado: cria skills a partir da experiência, pesquisa conversas passadas, constrói modelo persistente do usuário.

### O que aproveitar como inspiração
- Ideia de `wakeup` de memória ao iniciar sessão (Javis já tem via `ctx_knowledge`)
- Loop: executar tarefa → registrar aprendizado → disponibilizar na próxima sessão

---

## Resumo de Decisões Atualizado (2026-06-10 v2)

| Ferramenta | Status | Ação |
|---|---|---|
| LeanCTX | ✅ Ativo | Já funcionando como MCP |
| CodeGraph | ✅ Aprovado | Aguardando `codegraph init` |
| **agentmemory** | ✅ **Aprovado** | **Instalar agora** |
| **markitdown** | ✅ **Aprovado** | **Instalar agora** |
| MCP Filesystem (oficial) | ✅ Explorar | Explorar servidores MCP oficiais |
| Open-LLM-VTuber | 🧪 Sandbox | Testar voz separado |
| faster-whisper | 🧪 Sandbox | Testar STT dentro do VTuber |
| Kokoro TTS | 🧪 Sandbox | Testar TTS local |
| openhuman | 🔍 Benchmark | Referência de arquitetura |
| hermes-agent | 💡 Inspiração | Padrões de memória e aprendizado |
| lfnovo/open-notebook | 📅 Futuro | Knowledge base quando necessário |
| browser-use | 📅 Futuro | Automação web com aprovação |
| agent-skills | ✅ Referência | Selecionar skills individualmente |
| ai-engineering-from-scratch | 📚 Estudo | Consultar quando necessário |
| Headroom | ⏸ Pendente | Aguardando workaround Python 3.14 |
| CopilotKit | ❌ Fora | Frontend complexo sem necessidade |
| HiveMind | ❌ Fora | Imaturo (782 stars) |
