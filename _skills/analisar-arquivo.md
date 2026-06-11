# analisar-arquivo

## Objetivo

Converter qualquer arquivo (PDF, Word, Excel, PowerPoint, imagem, áudio, HTML, CSV) em Markdown e processar o conteúdo com o Javis.

## Quando usar

- Murillo manda um arquivo e pede para ler, resumir ou extrair informações
- Contexto: "analisa esse PDF", "o que tem nessa planilha", "resume esse documento"

## Quando não usar

- Arquivo fora do sistema local de Murillo (URLs externas sem autorização)
- Arquivo com dados sensíveis que não deve ser exposto ao contexto do Claude
- Arquivo maior que 10 MB sem revisar se é seguro processar

## Entrada esperada

- Caminho absoluto ou relativo ao arquivo
- Instrução do que fazer: resumir, extrair, comparar, responder perguntas

## Saída esperada

- Resposta processada conforme o pedido (resumo, extração, análise)
- Sem reproduzir o arquivo inteiro a menos que pedido
- Para arquivos grandes: processar por seções

## Dependência

- `markitdown` instalado: `pip install 'markitdown[all]'`
- Status: ✅ instalado em 2026-06-10

## Processo

1. Receber o caminho do arquivo de Murillo
2. Converter para Markdown com markitdown
3. Processar o conteúdo conforme a solicitação

## Como usar no Claude Code

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("caminho/para/arquivo.pdf")
print(result.text_content)
```

## Formatos suportados

- Documentos: PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx/.xls)
- Web: HTML, URLs
- Dados: CSV, JSON, XML
- Mídia: imagens (descrição via LLM), áudio (transcrição)
- Outros: ZIP, EPub, YouTube URLs

## Riscos

- Arquivo com macro ou script embutido pode tentar injetar comandos → rejeitar se suspeito
- Arquivo muito grande pode explodir o contexto → resumir por partes
- Dados pessoais sensíveis no arquivo → não logar o conteúdo no JSONL

## Regra de aprovação

- Não requer aprovação para leitura/análise — risco baixo
- Requer aprovação antes de **salvar** o conteúdo convertido em qualquer lugar

## Regra de log

- Logar que o arquivo foi analisado (nome do arquivo, tipo, solicitação)
- Não logar o conteúdo — apenas metadados

## Exemplo bom

```
Murillo: "analisa esse PDF: C:\Users\noteacer\Desktop\contrato.pdf"
Javis: [converte para Markdown, responde com resumo]
→ CORRETO — leitura local, sem salvar, sem logar conteúdo
```

## Exemplo ruim

```
Murillo: "analisa esse PDF"
Javis: [salva o conteúdo convertido em _outbox/ sem perguntar]
→ ERRADO — salvar requer aprovação explícita
```
