# Plano de testes de modelos e ferramentas para o Javis

**Data da análise:** 22/06/2026  
**Escopo:** planejamento e organização; nenhuma implementação ou chamada de API foi realizada.  
**Teto futuro proposto:** US$ 0,10 no total, somente após aprovação humana explícita.

## 1. Restrições desta fase

- Não executar OpenRouter, Gemini, OpenAI, Claude ou qualquer outro provedor externo.
- Não usar Fusion, não rodar benchmark D–E e não criar `model_router.py`.
- Não ler `.env` real, não expor chaves e não usar dados reais de cliente, CRM ou vendas.
- Não alterar produção, cascata, voz ou rotas atuais.
- Qualquer teste live futuro deve usar prompts sintéticos e receber aprovação humana específica.

## 2. Estado real do Javis que orienta o plano

| Componente | Estado atual | Consequência para os testes |
|---|---|---|
| `_apps/javis-local-interface/backend/agent.py` | Contém `_respond_openrouter()` e a cascata Claude subscription → OpenAI API → Anthropic API → OpenRouter. O modelo OpenRouter padrão é `meta-llama/llama-3.3-70b-instruct:free`. | OpenRouter já pode servir futuramente como baseline de texto e tool-use, sem rota nova. |
| `agent.py::stream_text()` | Tem somente Claude subscription → OpenAI. | O streaming não representa a cascata completa; não deve entrar no primeiro teste live do OpenRouter. |
| `_apps/javis-local-interface/backend/llm_providers.py` | Centraliza parte do acesso Claude; Ollama/local está explicitamente desativado. | Não incluir Ollama no benchmark atual. |
| `_apps/javis-local-interface/backend/server.py` | Mantém caminhos diretos, inclusive de voz, fora da cascata principal. | Voz deve ficar fora do benchmark inicial. |
| `_apps/javis-local-interface/tests/test_llm_fallback_offline.py` | Possui nove testes offline, mocks e bloqueio de socket/rede. | É a base segura do bloco A. |
| `_apps/javis-local-interface/backend/_scratch/_test_openrouter.py` | Bloqueado por padrão, mas referencia `meta-llama/llama-3.1-8b-instruct:free` e `mistralai/mistral-7b-instruct:free`. | Não usar ainda: os modelos não coincidem com a shortlist abaixo nem com o fallback atual. |
| Telemetria OpenRouter | Sanitizada e cobre modelo solicitado/resolvido, provedor, custo, tokens, latência, erro e fallback. | Adequada para um teste live pequeno, após aprovação. |
| Gemini | Não existe `_respond_gemini()` nem rota Gemini ativa. | Qualquer teste Gemini via API exige implementação futura de adaptador/rota. |
| `model_router.py` | Não existe. | Não é necessário para comparar o fallback OpenRouter existente; só deve ser discutido após corrigir a fragmentação da cascata. |

## 3. Critérios para decidir o que vale testar

1. **Encaixe:** aproveita rota e telemetria existentes?
2. **Capacidade:** mede texto, ferramenta, código, voz, imagem ou Conclave/Fusion com objetivo concreto?
3. **Segurança:** permite prompt sintético, provedor com política aceitável e aprovação humana?
4. **Custo:** é gratuito ou cabe em um envelope previsível de US$ 0,10?
5. **Ação:** o resultado pode mudar uma decisão do Javis, em vez de apenas alimentar curiosidade?

OpenRouter Rankings e Apps são sinais de uso e descoberta, não provas de qualidade. A seleção deve combinar esses sinais com os requisitos do Javis e um teste controlado.

## 4. Inventário e prioridade

| O que testar/analisar | Onde | Por que | Risco | Custo estimado | Precisa API? | Pode ser offline? | Aprovação humana? | Prioridade |
|---|---|---|---|---:|---|---|---|---|
| Contratos de fallback, timeout, erro, tool-use, telemetria e zero rede | Testes locais do Javis | Garante segurança antes de qualquer live | Baixo | US$ 0 | Não | Sim | Não para reexecução local | **Agora** |
| Catálogo e filtros de modalidade, preço, tool-use e privacidade | [OpenRouter Models](https://openrouter.ai/models) | Formar shortlist rastreável | Baixo | US$ 0 | Não | Parcial: consulta pública | Não, se apenas leitura pública | **Agora** |
| Tendências por período e categoria | [OpenRouter Rankings](https://openrouter.ai/rankings) | Descobrir candidatos recentes | Baixo; popularidade não é qualidade | US$ 0 | Não | Parcial | Não, se apenas leitura pública | **Agora** |
| Padrões de uso de Hermes, Kilo, Cline, Descript e SillyTavern | [OpenRouter Apps](https://openrouter.ai/apps) e sites oficiais | Comparar memória, aprovação, código, mídia e UX | Baixo; viés de adoção opt-in | US$ 0 | Não | Parcial | Não, se apenas leitura pública | **Agora** |
| Categorias, grupos de modelos, anexos, memória e ferramentas | [OpenRouter Chat](https://openrouter.ai/chat) | Entender a UX sem alterar o Javis | Baixo se nenhum prompt for enviado | US$ 0 | Não para inspeção | Parcial | Sim para login ou envio de prompt | **Agora, somente leitura** |
| Modelo atual `meta-llama/llama-3.3-70b-instruct:free` | Rota OpenRouter existente | Baseline fiel ao código atual | Médio: provedor e disponibilidade podem variar | US$ 0 de modelo; verificar política antes | Sim no live | Metadados, sim; inferência, não | **Sim** para live | **Agora como candidato; live depois da aprovação** |
| `nex-agi/nex-n2-pro:free` | OpenRouter | Comparar texto, visão, função e saída estruturada | Médio: modelo novo/free e disponibilidade variável | US$ 0 de modelo | Sim no live | Metadados, sim | **Sim** para live | **Agora como candidato** |
| `cohere/north-mini-code:free` | OpenRouter | Comparar código, agentic terminal, JSON schema e tool-use | Médio; pode não representar conversa geral | US$ 0 de modelo | Sim no live | Metadados, sim | **Sim** para live | **Agora como candidato de código** |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | OpenRouter | Comparar orquestração, código e contexto longo | Médio: modelo novo e grande | US$ 0 de modelo | Sim no live | Metadados, sim | **Sim** para live | **Depois do baseline** |
| `deepseek/deepseek-v4-flash` | OpenRouter | Comparador pago barato para chat, código e agente | Médio: provedor pode registrar/treinar dados; exigir filtro de privacidade | Cerca de US$ 0,000126 para 1.000 tokens de entrada + 200 de saída, pela tarifa pública consultada | Sim | Metadados, sim | **Sim** para live | **Depois do baseline gratuito** |
| Modelos Gemini e condições de dados/preço | [Gemini models](https://ai.google.dev/gemini-api/docs/models) e [pricing](https://ai.google.dev/gemini-api/docs/pricing) | Definir futuro adaptador Gemini sem implementar | Baixo na leitura | US$ 0 | Não | Parcial | Não, se apenas leitura pública | **Agora como análise** |
| Gemini AI Studio, somente com prompt sintético | [Google AI Studio](https://aistudio.google.com/) | Comparar resposta/modelos antes de criar rota | Médio: exige conta; dados do free tier podem ser usados para melhoria de produtos | US$ 0 onde disponível | Não para UI | Não | **Sim** antes de login/envio | **Depois** |
| Gemini API: Gemini 3.5 Flash / Gemini 3.1 Flash-Lite | Nova rota futura | Comparar um provedor que hoje não existe no Javis | Médio: chave, rota, erro e telemetria novos | Verificar preço oficial imediatamente antes do teste | Sim | Não | **Sim** | **Depois de implementar e testar offline o adaptador** |
| Gemini Live/TTS | Nova rota de voz futura | Avaliar latência e voz em tempo real | Alto: áudio, streaming, privacidade e custo | Não estimado nesta fase | Sim | Não | **Sim** | **Depois** |
| Nano Banana 2 / Gemini image | Nova rota de imagem futura | Avaliar criação/edição visual | Médio/alto: mídia e custo por imagem | Não estimado nesta fase | Sim | Não | **Sim** | **Depois** |
| OpenRouter Fusion | [OpenRouter Fusion](https://openrouter.ai/fusion) | Possível referência futura para Conclave/julgamento | Alto: várias chamadas, juiz, web e custo somado | Variável; soma das conclusões usadas | Sim para executar | Não | **Sim** | **Evitar agora** |

Os nomes, disponibilidade e preços de modelos são temporais. Eles devem ser reconfirmados na página oficial imediatamente antes de qualquer aprovação live.

## 5. Bloco A — Testes offline já seguros

### A1. Reexecutar a suíte existente

- Arquivo: `_apps/javis-local-interface/tests/test_llm_fallback_offline.py`.
- Cobertura já preparada: ausência de chave, ordem de fallback, timeout, erro de provedor, tool-use, sanitização e bloqueio de rede.
- Rede: bloqueada por socket e por mocks.
- Custo: US$ 0.
- Aprovação adicional: não, desde que seja apenas a suíte local existente.

### A2. Casos que podem ser especificados antes do live

- orçamento esgotado impede a chamada antes do SDK;
- modelo solicitado e resolvido nunca incluem segredo ou headers;
- provedor ausente/desconhecido gera telemetria sanitizada;
- resposta com tool-call inválida falha fechada;
- `stream_text()` não é confundido com a cascata completa;
- o script `_test_openrouter.py` permanece opt-in e não é usado enquanto sua lista de modelos divergir do plano.

Esses itens são planejamento de cobertura, não autorização para alterar os testes nesta fase.

## 6. Bloco B — Testes via site/UI sem gastar crédito

| Site/área | Ação permitida nesta fase | Resultado esperado | Limite de segurança |
|---|---|---|---|
| OpenRouter Models | Filtrar texto, código, tool-use, multimodalidade, preço e privacidade; registrar IDs | Shortlist de 2–4 modelos | Não clicar para executar; não inserir prompt |
| OpenRouter Rankings | Consultar semana/mês e categorias de programação/tool calls/imagem | Sinal de descoberta | Não tratar ranking de uso como benchmark de qualidade |
| OpenRouter Apps | Ler descrições e categorias | Referências de produto/arquitetura | Não instalar nem autorizar apps |
| OpenRouter Chat | Inspecionar grupos e recursos visíveis | Referência de UX | Sem login, memória, upload, microfone ou envio de mensagem |
| Gemini docs | Conferir modelos estáveis, preview, depreciação e política de dados | Shortlist Gemini futura | Não gerar chave |
| Gemini AI Studio | Apenas página pública nesta fase | Entender opções disponíveis | Não entrar na conta nem enviar prompt sem nova aprovação |
| OpenRouter Fusion | Nenhuma execução; somente manter a referência documental já coletada | Registrar por que fica fora | Não selecionar painel, juiz, web ou botão de execução |

## 7. Bloco C — Testes live pequenos com teto de US$ 0,10

**Status: planejado, não autorizado e não executado.**

Primeiro lote recomendado, após aprovação explícita:

1. Baseline: `meta-llama/llama-3.3-70b-instruct:free`, porque é o fallback real de `agent.py`.
2. Segundo modelo: `nex-agi/nex-n2-pro:free`, escolhido para comparar português geral, tool-use e código no mesmo lote; detalhes na seção 14.
3. Comparador pago opcional: `deepseek/deepseek-v4-flash`, somente depois dos gratuitos e com limite de tokens/provedor de privacidade explícito.

Escopo mínimo por modelo:

- uma pergunta curta de português geral;
- um caso sintético de tool-use sem executar ação local;
- um caso curto de código sem escrever arquivo;
- no máximo uma repetição por falha transitória;
- nenhum dado de cliente, CRM, vendas, memória pessoal ou projeto privado.

Critérios de saída: conteúdo útil, tool-call válido, latência, tokens, custo, modelo resolvido, provedor, erro e fallback. O lote para imediatamente se houver custo inesperado, modelo diferente, ausência de provedor aceitável, erro de sanitização ou tentativa de rede fora do cliente mockado/esperado.

### Pacote obrigatório de aprovação live

Antes de qualquer chamada, apresentar a Murillo, em uma única mensagem:

1. objetivo e prompt sintético exato;
2. modelo e provedor exatos;
3. número máximo de chamadas e retentativas;
4. limites máximos de tokens de entrada e saída;
5. preço oficial consultado, fórmula e custo máximo estimado;
6. teto acumulado da sessão, nunca superior a US$ 0,10;
7. política de privacidade/retenção aplicável;
8. comando completo que será usado, diretório de execução e variáveis **apenas por nome**, nunca seus valores;
9. arquivos/logs que serão produzidos;
10. pedido explícito de aprovação.

Nenhum comando live foi aprovado ou definido como executável neste documento. O `_scratch/_test_openrouter.py` atual **não deve ser usado** antes de alinhar sua lista de modelos, limites e critérios com este plano e repetir os testes offline.

## 8. Bloco D — Testes que devem ficar para depois

- **Gemini API:** exige `_respond_gemini()` ou adaptador equivalente, configuração sanitizada, telemetria e testes offline próprios.
- **Voz Gemini Live/TTS:** exige desenho separado para streaming, consentimento, retenção de áudio, timeout e fallback; não deve passar pelo benchmark de texto atual.
- **Imagem/Nano Banana:** exige rota de mídia, armazenamento/expiração, moderação e orçamento por imagem.
- **Descript:** útil como referência para fluxo de gravação, transcrição e edição; não encaixa na cascata LLM atual.
- **Hermes Agent:** útil para estudar memória persistente, skills, separação de ferramentas e aprovação de comandos; não instalar nem adotar como runtime.
- **Cline/Kilo Code:** úteis para estudar seleção de provedor, checkpoints e aprovação de edições/comandos; o Javis já tem Codex/Claude Code, então uma adoção agora duplicaria o stack.
- **Nemotron 3 Ultra:** testar somente se os modelos menores não cobrirem orquestração/tool-use.
- **Modelo de content safety separado:** considerar apenas se a política atual não bastar e houver ameaça concreta mensurável.

## 9. Bloco E — Testes que devemos evitar agora

- Fusion/Conclave live: custo composto, múltiplos provedores, juiz e possível web search.
- Flagships caros de Claude/OpenAI via OpenRouter: duplicam rotas já existentes e adicionam custo sem hipótese específica.
- Computer-use, agentes gerenciados, OpenClaw ou automação ampla: conflito com aprovação humana e whitelist do Command Router.
- SillyTavern como runtime: foco em roleplay/persona não resolve a fragmentação atual; serve apenas como referência de UI/provedor.
- Modelos de imagem/vídeo com preço dinâmico ou alto, como Riverflow/Veo, antes de existir rota e orçamento de mídia.
- Auto-router ou seleção automática opaca antes de haver métricas e política de fallback centralizada.
- Qualquer teste com dados reais de CRM, vendas, cliente, voz pessoal, anexos privados ou memória do Javis.
- Qualquer tentativa de ativar Ollama/local, criar `model_router.py` ou alterar produção nesta fase.

## 10. Referências de apps: o que aproveitar e o que não adotar

| Referência | Ideia útil para o Javis | Decisão agora |
|---|---|---|
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | Aprovação de comandos, memória, skills, ferramentas e troca de provedor | Estudar padrões; não instalar |
| [Kilo Code](https://kilocode.ai/) | UX de agente de código e múltiplos provedores | Referência futura; não duplicar Codex/Claude Code |
| [Cline](https://github.com/cline/cline) | Checkpoints, aprovação de terminal/browser e provider abstraction | Referência futura; não integrar |
| [Descript](https://www.descript.com/) | Fluxo de voz, transcrição, edição e conteúdo | Depois, quando existir projeto de mídia/voz |
| [SillyTavern](https://github.com/SillyTavern/SillyTavern) | UI de persona, presets e seleção de provedor | Apenas referência; evitar adoção agora |

## 11. Cruzamento com o código atual

| Área | Encaixa hoje? | Rota nova? | Usa OpenRouter existente? | Exige Gemini novo? | Exige `model_router.py`? | Voz | CRM/vendas | Segurança/aprovação |
|---|---|---|---|---|---|---|---|---|
| OpenRouter texto curto | Sim, em `_respond_openrouter()` | Não | Sim | Não | Não | Não | Sem dados reais | Aprovação live + teto |
| OpenRouter tool-use | Sim, com mocks já existentes; live a validar | Não | Sim | Não | Não | Não | Somente cenário sintético | Nunca executar ferramenta local no benchmark |
| OpenRouter código | Parcial; resposta textual cabe, execução não | Não | Sim | Não | Não | Não | Não | Sem escrita/terminal no live |
| OpenRouter imagem/áudio | Não | Sim | Possivelmente, mas não pela rota atual | Não necessariamente | Não neste estágio | Sim para áudio | Não | Aprovação, retenção e orçamento próprios |
| Gemini texto | Não | **Sim** | Não | **Sim** | Não para um primeiro adaptador isolado | Não | Sem dados reais | Chave, telemetria e mocks novos |
| Gemini voz/imagem | Não | **Sim, especializada** | Não | **Sim** | Não é o primeiro bloqueio | **Sim** | Não | Consentimento, mídia e custo |
| Rankings/Models/Apps/Chat | Sim como pesquisa | Não | Não executa API | Não | Não | Não | Não | Leitura pública apenas |
| Fusion/Conclave | Não na cascata atual | Provavelmente sim no futuro | Sim | Não obrigatório | Uma política central ajudaria, mas não criar agora | Não | Não | Alto risco/custo; evitar |

### Onde `model_router.py` entraria no futuro

Se aprovado depois, ele entraria entre os chamadores (`respond()`, `stream_text()` e rotas de `server.py`) e os adaptadores de provedor (`_respond_openrouter()`, Claude/OpenAI/Anthropic e futuro Gemini). Seu papel seria centralizar política, orçamento, capacidades e fallback. Criá-lo antes de mapear todos os chamadores apenas mudaria a fragmentação de lugar.

## 12. Parecer

### Entra na lista agora

- suíte offline existente e especificação dos casos adicionais;
- leitura pública de Models, Rankings, Apps, Chat e documentação Gemini;
- shortlist de metadados: Llama 3.3 70B free, North Mini Code free, Nex-N2-Pro free e DeepSeek V4 Flash como comparador pago opcional;
- Hermes, Cline e Kilo como referências de segurança/provider UX, não como dependências.

### Fica para depois

- qualquer chamada live, mesmo gratuita;
- Gemini API/AI Studio com prompt, voz, imagem, Descript e Nemotron;
- centralização de cascata e eventual `model_router.py`.

### Não vale a pena agora

- Fusion, flagships caros duplicados, SillyTavern/OpenClaw como runtime, computer-use e mídia de preço dinâmico.

### Próximo passo seguro

Submeter o pacote congelado da seção 14 para aprovação ou rejeição. Mesmo se aprovado em escopo, ainda será necessário reconfirmar preço/provedor, apresentar o comando exato, alinhar o script live e reexecutar a suíte offline antes de pedir autorização de execução.

## 13. Fontes públicas consultadas

Consulta somente leitura em 22/06/2026, sem login, envio de prompt ou execução:

- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter Rankings](https://openrouter.ai/rankings)
- [OpenRouter Apps](https://openrouter.ai/apps)
- [OpenRouter Chat](https://openrouter.ai/chat)
- [OpenRouter Fusion](https://openrouter.ai/fusion)
- [Llama 3.3 70B Instruct free no OpenRouter](https://openrouter.ai/meta-llama/llama-3.3-70b-instruct:free)
- [DeepSeek V4 Flash no OpenRouter](https://openrouter.ai/deepseek/deepseek-v4-flash)
- [Gemini models](https://ai.google.dev/gemini-api/docs/models)
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Hermes Agent](https://github.com/NousResearch/hermes-agent)

## 14. Pacote de aprovação do primeiro lote OpenRouter

**Status:** pacote documental congelado; não autoriza execução.  
**Escopo:** três prompts sintéticos aplicados igualmente aos dois modelos escolhidos.  
**Máximo do lote:** seis chamadas, sem retentativa automática e sem comparador pago.  
**Custo estimado do lote:** US$ 0,00 pela tarifa dos dois IDs `:free`; qualquer previsão ou registro de custo maior que zero reprova e interrompe o lote.

### 14.1 Modelos congelados

| Papel | ID exato | Motivo da escolha | Decisão |
|---|---|---|---|
| Baseline | `meta-llama/llama-3.3-70b-instruct:free` | É o fallback OpenRouter real configurado em `agent.py`; mede o comportamento atual sem criar rota. | **Incluído** |
| Segundo modelo | `nex-agi/nex-n2-pro:free` | É generalista/agentic e cobre português, função estruturada e código no mesmo lote, permitindo comparação direta nos três prompts. | **Incluído** |
| Especialista de código | `cohere/north-mini-code:free` | Seria útil para código e terminal, mas estreitaria o primeiro lote e produziria uma comparação menos equilibrada no prompt geral. | **Adiado para lote específico de código** |
| Comparador pago | `deepseek/deepseek-v4-flash` | Pode servir como controle barato se os dois gratuitos forem insuficientes. | **Opcional e excluído desta aprovação** |

Os IDs estão congelados para o desenho do teste, mas disponibilidade, tarifa e provedores precisam ser reconfirmados sem inferência imediatamente antes de uma futura aprovação de execução.

### 14.2 Contexto comum congelado

Mensagem de sistema para os três casos:

> Você está em um benchmark sintético e isolado. Siga somente a tarefa apresentada. Não tente acessar rede, arquivos, shell ou ferramentas fora do schema fornecido. Não use nem solicite dados reais.

Regras comuns:

- executar cada prompt uma vez em cada modelo: 3 × 2 = no máximo 6 chamadas;
- zero retentativas automáticas; falha transitória fica registrada como falha do lote;
- usar conversa nova e sem histórico em cada chamada;
- não carregar memória, anexos, CRM, dados de vendas, voz ou conteúdo do workspace;
- não usar `stream_text()`, Fusion, Gemini, produção ou o `_scratch/_test_openrouter.py` atual;
- não despachar tool-call e não executar código retornado;
- abortar antes da primeira chamada se o modelo resolvido, provedor, política de privacidade ou custo não corresponder ao pacote aprovado.

### 14.3 Prompt P1 — Português geral

**Texto congelado:**

> Explique em português do Brasil, em no máximo cinco frases, a diferença entre uma tarefa urgente e uma tarefa importante. Termine com um exemplo fictício de cada uma. Não use nomes de pessoas, empresas ou dados reais.

| Campo | Definição |
|---|---|
| Objetivo | Medir compreensão, clareza, concisão e obediência em português geral. |
| Modelos | `meta-llama/llama-3.3-70b-instruct:free` e `nex-agi/nex-n2-pro:free`. |
| Limite de input | Até 512 tokens, incluindo mensagem de sistema e serialização. Se ultrapassar, não chamar. |
| Limite de output | `max_tokens=180`. |
| Máximo de chamadas | Uma por modelo; duas no total; zero retentativas. |
| Custo estimado | US$ 0,00 com os dois IDs `:free`; custo previsto/registrado maior que zero interrompe o lote. |
| Privacidade/provedor | Prompt totalmente sintético. Provedor deve estar fixado e identificado no pré-voo, com política que não permita treino nem retenção de conteúdo; se nenhum estiver disponível, reprovar sem chamar. |
| Logs esperados | Um evento sanitizado por chamada: modelo solicitado, modelo resolvido, provedor, tokens de entrada/saída, custo estimado/relatado, latência, erro e fallback usado. Não registrar prompt, resposta, headers ou credencial. |
| Aprovação | Responde em português do Brasil, em até cinco frases, diferencia corretamente urgente/importante e fornece os dois exemplos fictícios. |
| Reprovação | Idioma inadequado, mais de cinco frases, distinção incorreta, ausência de exemplo, dado aparentemente real, modelo/provedor divergente, erro ou custo não zero. |

### 14.4 Prompt P2 — Tool-use sem execução

**Texto congelado:**

> Para responder, solicite exatamente uma chamada da ferramenta `consultar_status_ficticio` com o argumento `servico` igual a `servico_demo`. Não invente o resultado, não execute nada e não escreva uma resposta final antes do retorno da ferramenta.

**Schema sintético congelado:**

```json
{
  "type": "function",
  "function": {
    "name": "consultar_status_ficticio",
    "description": "Retorna o status de um serviço inteiramente sintético de teste.",
    "parameters": {
      "type": "object",
      "properties": {
        "servico": { "type": "string", "enum": ["servico_demo"] }
      },
      "required": ["servico"],
      "additionalProperties": false
    }
  }
}
```

| Campo | Definição |
|---|---|
| Objetivo | Medir tool-use estruturado sem acionar Command Router, dispatcher, rede ou ação local. |
| Modelos | `meta-llama/llama-3.3-70b-instruct:free` e `nex-agi/nex-n2-pro:free`. |
| Limite de input | Até 768 tokens, incluindo mensagem de sistema, prompt e schema. Se ultrapassar, não chamar. |
| Limite de output | `max_tokens=128`. |
| Máximo de chamadas | Uma por modelo; duas no total; zero retentativas e sem segunda rodada com resultado da ferramenta. |
| Custo estimado | US$ 0,00 com os dois IDs `:free`; custo previsto/registrado maior que zero interrompe o lote. |
| Privacidade/provedor | Somente nomes e valores fictícios. Aplicam-se o provedor fixado e a política sem treino/retenção exigidos no P1. |
| Logs esperados | Telemetria sanitizada padrão mais veredito local `tool_call_valid`; pode registrar o nome sintético da função, mas não argumentos livres, prompt, resposta, headers ou credencial. |
| Aprovação | Produz exatamente uma tool-call com nome `consultar_status_ficticio` e JSON exato `{"servico":"servico_demo"}`, sem texto final e sem despacho. |
| Reprovação | Zero ou múltiplas tool-calls, ferramenta diferente, JSON inválido/campo extra, resposta inventada, tentativa de executar, modelo/provedor divergente, erro ou custo não zero. |

O harness futuro deve parar após receber a primeira resposta e apenas inspecionar a estrutura; a função não será implementada nem executada.

### 14.5 Prompt P3 — Código simples sem escrita

**Texto congelado:**

> Escreva uma função Python pura chamada `normalizar_etiquetas(etiquetas: list[str]) -> list[str]` que remova espaços laterais, descarte strings vazias, converta para minúsculas e elimine duplicatas preservando a ordem. Responda apenas com um bloco de código de no máximo oito linhas. Não leia ou escreva arquivos e não use rede, shell nem pacotes externos.

| Campo | Definição |
|---|---|
| Objetivo | Medir geração de código simples, correto, conciso e sem efeitos colaterais. |
| Modelos | `meta-llama/llama-3.3-70b-instruct:free` e `nex-agi/nex-n2-pro:free`. |
| Limite de input | Até 512 tokens, incluindo mensagem de sistema e serialização. Se ultrapassar, não chamar. |
| Limite de output | `max_tokens=220`. |
| Máximo de chamadas | Uma por modelo; duas no total; zero retentativas. |
| Custo estimado | US$ 0,00 com os dois IDs `:free`; custo previsto/registrado maior que zero interrompe o lote. |
| Privacidade/provedor | Código e nomes inteiramente sintéticos. Aplicam-se o provedor fixado e a política sem treino/retenção exigidos no P1. |
| Logs esperados | Um evento sanitizado padrão por chamada e veredito local de conformidade; não registrar o código integral, prompt, headers ou credencial. |
| Aprovação | Um único bloco Python, até oito linhas, assinatura correta, normalização completa, ordem preservada, sem I/O, rede, shell ou dependência externa. |
| Reprovação | Código inválido/incompleto, texto fora do bloco, mais de oito linhas, efeito colateral, modelo/provedor divergente, erro ou custo não zero. |

A validação inicial será estática; o código retornado não será salvo nem executado nesta fase.

### 14.6 Orçamento máximo congelado

| Item | Input máximo | Output máximo | Chamadas | Custo estimado |
|---|---:|---:|---:|---:|
| P1 nos dois modelos | 1.024 tokens | 360 tokens | 2 | US$ 0,00 |
| P2 nos dois modelos | 1.536 tokens | 256 tokens | 2 | US$ 0,00 |
| P3 nos dois modelos | 1.024 tokens | 440 tokens | 2 | US$ 0,00 |
| **Total do lote gratuito** | **3.584 tokens** | **1.056 tokens** | **6** | **US$ 0,00** |

O teto global de US$ 0,10 continua como trava externa, mas este lote é reprovado se qualquer chamada deixar de ser gratuita.

Se o DeepSeek V4 Flash for proposto depois para os mesmos três prompts, ele será um pacote separado de até três chamadas. Pelas tarifas anotadas nesta análise (US$ 0,09/M input e US$ 0,18/M output), o envelope máximo seria aproximadamente **US$ 0,000257**, mas preço, provedor, privacidade e comando terão de ser reconfirmados; ele não faz parte desta aprovação.

### 14.7 Privacidade e provedor: condição suspensiva

Este pacote congela modelos e prompts, mas não inventa um provedor que não foi verificado nesta etapa. Antes de pedir autorização live:

1. identificar e fixar o provedor exato para cada modelo;
2. confirmar que o provedor não usa prompts/respostas para treino e não retém conteúdo;
3. desativar fallback para outro provedor ou modelo durante o benchmark;
4. rejeitar o lote se essas condições não puderem ser garantidas;
5. apresentar ao usuário a fonte, a política vigente e o comando exato, sem valores de chave.

A aprovação desta seção autoriza somente o **desenho** do lote. Não autoriza consulta de saldo, chamada de API, alteração do script, leitura de `.env`, login, execução ou gasto.

### 14.8 Decisão solicitada

- **Aprovar desenho:** mantém os dois modelos, três prompts e limites congelados; ainda será necessário um segundo aceite para qualquer live.
- **Rejeitar/ajustar:** nenhuma chamada ocorre; o pacote volta para edição documental.
