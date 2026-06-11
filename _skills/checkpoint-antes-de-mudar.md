# checkpoint-antes-de-mudar

## Objetivo

Criar um registro do estado atual do projeto antes de qualquer mudança arquitetural, integração nova ou refatoração significativa — para poder voltar ao ponto certo se algo der errado.

## Quando usar

- Antes de integrar um novo módulo (ex: conectar voice_bridge ao Open-LLM-VTuber)
- Antes de refatorar um arquivo de backend existente
- Antes de adicionar uma dependência nova
- Antes de mudar a estrutura de pastas do projeto
- Quando a tarefa vai afetar mais de 2 arquivos ao mesmo tempo
- Quando Murillo diz "vamos mudar a arquitetura"

## Quando não usar

- Edições menores de documentação
- Criação de arquivo novo sem alterar existentes
- Adição de skill que não toca código funcional
- Correção de typo

## Entrada esperada

- Descrição da mudança planejada
- Arquivos que serão afetados
- Motivo da mudança

## Saída esperada

Arquivo `_logs/checkpoint-YYYY-MM-DD_nome-da-mudanca.md` com:

```markdown
# Checkpoint — [nome da mudança]
Data: YYYY-MM-DD

## Estado antes da mudança
- git status --short
- Arquivos afetados
- Estado atual dos módulos

## O que será mudado
- [lista dos arquivos que serão tocados]
- [descrição da mudança]

## Como reverter
- [passos para desfazer, se necessário]

## Pendências antes de começar
- [qualquer pré-requisito não atendido]
```

## Riscos

- Pular o checkpoint e fazer mudança grande → sem ponto de retorno
- Checkpoint depois da mudança → não serve para reverter

## Regra de aprovação

- Não requer aprovação para criar o checkpoint
- Requer aprovação para **iniciar** a mudança após o checkpoint

## Regra de log

- O checkpoint em si é o log — salvar em `_logs/`
- Nome do arquivo deve identificar a mudança claramente

## Exemplo bom

```
Murillo: "vamos conectar o voice_bridge ao Open-LLM-VTuber"
Javis: [cria _logs/checkpoint-2026-06-11_voice-bridge-integration.md]
[documenta estado atual, arquivos afetados, como reverter]
Javis: "Checkpoint criado. Podemos prosseguir?"
```

## Exemplo ruim

```
Murillo: "vamos conectar o voice_bridge"
Javis: [começa a editar single_conversation.py diretamente]
→ ERRADO — sem checkpoint, sem registro de como reverter
```
