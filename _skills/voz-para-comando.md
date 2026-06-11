# voz-para-comando

## Objetivo

Classificar um texto transcrito por voz e mostrar o que o Command Router faria — sem executar nada. Útil para validar o roteamento de comandos de voz antes de liberar execução.

## Quando usar

- Murillo diz um comando e quer saber como seria roteado
- Durante a fase de validação do dry-run (antes de liberar execução por voz)
- Para depurar classificações inesperadas do Command Router
- Quando o sandbox de voz está ativo e Murillo quer ver o que seria feito com a transcrição

## Formato de entrada

Qualquer texto transcrito por voz — pode ser informal, com erro de pronúncia ou incompleto. O Command Router usa palavras-chave, não semântica.

Exemplos:
- "abre o youtube"
- "toca uma música relaxante"
- "como estão os serviços"
- "anota essa ideia pra mim"

## Formato de saída

```json
{
  "source": "voice",
  "transcript": "texto transcrito",
  "intent": "abrir_youtube",
  "confidence": "high",
  "risk_level": "low",
  "requires_approval": false,
  "action": "open_url",
  "dry_run": true,
  "would_execute": true,
  "reason": "palavra-chave 'youtube' detectada",
  "note": "seguro — executaria via actions.execute() quando liberado"
}
```

## Comandos seguros (would_execute: true na Fase 2)

| Intent | Exemplo de fala |
|--------|----------------|
| `abrir_youtube` | "abre o youtube" |
| `tocar_musica` | "toca uma música" |
| `abrir_openwebui` | "abre o open webui" |
| `abrir_navegador` | "abre o navegador" |
| `status_sistema` | "como estão os serviços" |
| `registrar_ideia` | "anota isso pra mim" |
| `conversa` | "o que você acha de..." |

## Comandos perigosos (would_execute: false — sempre)

| Intent | Exemplo | Comportamento |
|--------|---------|---------------|
| `acao_perigosa` | "apaga", "deleta", "rm -rf", "git push" | BLOQUEADO, nunca executa |
| `abrir_terminal` | "abre o terminal" | requer aprovação humana, nunca por voz |

## Regra de aprovação

- `risk_level: critical` → **sempre bloqueado por voz**, sem exceção, mesmo com aprovação
- `risk_level: medium` → requer aprovação humana explícita (teclar s/N no CLI) — não automatizar por voz
- `risk_level: low` → pode executar automaticamente na Fase 2 (quando Murillo aprovar)

## Regra de log obrigatório

Todo comando de voz, mesmo em dry-run, deve ser logado em `logs/actions.jsonl` com:
- `source: "voice"`
- `dry_run: true`
- `approved: false` (na Fase 1)
- `action_result: "dry_run_only"`

Nenhum evento de voz pode passar sem log.

## Como testar

```powershell
cd _apps/javis-local-interface
python backend/voice_bridge.py "abre o youtube"
```

## Próximo passo para liberar execução

1. Murillo revisa `logs/actions.jsonl` após uso real do sandbox de voz
2. Confirma que os intents estão sendo classificados corretamente
3. Aprova explicitamente a liberação de `dry_run = False`
4. Somente então `voice_bridge.py` chama `actions.execute()`
