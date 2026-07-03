# Resumo: 2026-06-16_video_google-notebooklm-api-enterprise-only-access-amp-how-it-work_e9760a0f

Área: tecnico
Resumido em: 2026-07-02 (Javis / Claude assinatura)
Origem: _entrada/2026-06-16_video_google-notebooklm-api-enterprise-only-access-amp-how-it-work_e9760a0f.md

## Resumo

O vídeo mostra que a API do Google NotebookLM **não é aberta ao público** — o acesso programático é restrito a clientes **Enterprise** (via Google Cloud / Agentspace). Não existe chave de API self-service como em outras ferramentas Google. A demo cobre como funciona esse acesso corporativo (autenticação por conta gerenciada, ingestão de fontes e geração de resumos/áudio via API), deixando claro que integrações "caseiras" hoje dependem da interface web, não de endpoint público.

## Aprendizados aplicáveis ao negócio

1. **Não dá para automatizar o NotebookLM direto no Javis** por enquanto — sem tier Enterprise, o fluxo continua manual (subir material → gerar resumo → colar em `_resumos/`). Alinha com o "Próximo passo" deste próprio material.
2. **O valor do NotebookLM é o processamento de fontes**, não a API. Para a Vem Passear, ele serve como ferramenta de estudo/curadoria de conteúdo (roteiros, FAQs de turistas, material de treino), operado à mão.
3. **Se precisar de resumo programático de verdade, a rota é a API Claude/Anthropic** (que você já usa por assinatura) — não vale esperar liberação Enterprise do NotebookLM.
4. **Cuidado com dependência de ferramenta fechada**: qualquer pipeline que dependa do NotebookLM fica travado no manual e não escala para automação do Javis.

## Ações concretas

1. **Manter NotebookLM como etapa manual** no fluxo de treinamento — não investir tempo tentando integrar via API agora; registrar em `_logs/` que o acesso é Enterprise-only.
2. **Replicar a capacidade de resumo de fontes dentro do Javis** usando o cérebro Claude que já roda por assinatura, tornando o pipeline `_entrada/ → _resumos/` automatizável sem depender do Google.
