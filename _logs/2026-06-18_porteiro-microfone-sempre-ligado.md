# Portão de ativação no microfone sempre-ligado + cérebro do app de voz — 18/06

## O que foi decidido

Achada a causa raiz de dois problemas relatados ao vivo pelo Murillo testando o
app de voz sempre-ligado (Open-LLM-VTuber, `_ferramentas/voz-sandbox`):

1. **"Responde sem querer, com coisa sem nada a ver"** — o app de voz NUNCA
   passava pelo `_brain()`/`/voice` que recebeu a troca de cérebro de 17/06-18/06.
   Ele fala com o backend por um endpoint totalmente separado,
   `/v1/chat/completions` (compatível OpenAI, `server.py`), e esse endpoint
   processava e respondia QUALQUER fala captada pelo VAD — a "palavra de
   ativação" (Jamba/Javis) só era removida do texto se estivesse presente, nunca
   era exigida. Não existia portão nenhum.
2. **Resposta boa "não escreveu aqui"** — investigado e descartado como bug:
   `history_store.append()` é chamado nesse endpoint e grava no mesmo
   `_data/chat_history.json` que o resto do projeto usa. Conferido ao vivo: a
   conversa do Murillo apareceu lá segundos depois de ele falar. O mais provável
   é a UI web (painel de chat) não atualizar sozinha quando a conversa entra por
   fora dela (pelo app de voz) — não é perda de dados.

## Mudanças

**`voice_bridge.py`** — nova função `has_wake_word(text)`: verifica só os nomes
reais de ativação (jamba/javis/jarvis/...), SEM contar saudações genéricas
(oi/ei/hey) que `_strip_wake_word` também reconhece pra outro propósito (cortar
prefixo educado antes de rotear comando). Importante separar os dois: se "oi"
abrisse o portão, qualquer cumprimento de fundo religaria a escuta.

**`server.py` `/v1/chat/completions`** —
1. **Portão de ativação**: só processa e responde se a palavra de ativação
   apareceu na fala OU se ainda está dentro da "janela de conversa"
   (`_WAKE_SESSION_SECONDS = 25`, contados da última vez que ativou). Assim não
   precisa repetir "Javis" a cada frase de um papo contínuo, mas depois de 25s
   de silêncio/sem ativação, volta a exigir o nome. Fora da janela e sem a
   palavra: devolve resposta vazia (TTS fica em silêncio) e NÃO loga no
   histórico — fala de fundo não some.
2. **Cérebro = Claude assinatura**: trocado `_llm_direct` pra tentar
   `claude_brain.answer()` primeiro (mesma decisão de 17-18/06 de tirar a API
   paga do caminho de conversa); cai pro gpt-4o-mini só se o Claude faltar/vazio.
   Esse endpoint tinha ficado de fora da troca anterior porque eu não sabia que
   ele existia até essa investigação.

## Por quê

Murillo pediu pra deixar a escuta sempre ligada sem responder a qualquer
ruído/fala de fundo, e mencionou que o próprio app sugeriu (numa resposta ao
vivo) usar uma palavra de ativação tipo "Javis" pra resolver isso — confirma
que o portão é o caminho certo, não uma suposição minha.

## Alternativas consideradas

- Exigir a palavra de ativação em TODA fala (sem janela de conversa): rejeitado
  — tornaria papo contínuo cansativo, repetindo "Javis" a cada frase.
- Motor de keyword-spotting dedicado (openWakeWord) rodando antes do
  ASR/Whisper: mais robusto (não precisa transcrever fala não endereçada a ele),
  mas é trabalho maior — fica como evolução futura se o filtro por texto não for
  suficiente.

## Trade-offs honestos

- O filtro hoje é **pós-ASR**: a fala de fundo ainda é transcrita pelo Whisper
  antes de ser descartada (gasta CPU, mas não gasta LLM nem fala via TTS). Um
  motor de keyword-spotting cortaria isso antes do ASR — não implementado agora.
- 25s de janela é um palpite inicial. Se ficar respondendo coisa de fora da
  janela, ou se 25s for curto/longo demais, é só ajustar
  `_WAKE_SESSION_SECONDS` em `server.py`.

## Verificação

`python -c "import server"` OK · `pytest tests/` 71/71 · teste isolado de
`has_wake_word`: "Javis, que horas são?" → True; "aí cara, vamos almoçar" →
False; "oi, tudo bem?" → False (saudação não abre o portão).

Teste ao vivo pendente (Murillo): reiniciar o app de voz e testar (a) falar sem
dizer "Javis" perto do microfone — não deve responder; (b) dizer "Javis" e
manter um papo de seguida sem repetir o nome — deve continuar respondendo
durante a janela.

## Próximo passo

1. Murillo testa ao vivo e diz se 25s tá bom, curto ou longo, e se o portão
   está pegando bem o nome mesmo com ruído do ASR.
2. Bugs ainda abertos de sessões anteriores, não tocados aqui: confusão de
   identidade (Javis falando como se fosse a empresa Vem Passear Jampa) e
   afirmação fabricada de execução ("Iniciei a execução das remediais" sem
   mudança real de arquivo).

---

## Adendo — bug de encoding (mojibake "Ã©") RESOLVIDO

Murillo colou a resposta do Javis cheia de `Ã©`/`Ã¡`/`â€"`. Diagnóstico pelos
bytes crus do `chat_history.json`: dupla codificação (`\xc3\x83\xc2\xa9` onde
deveria ser `\xc3\xa9` = é). Sem perda de dado (recuperável), mas ilegível.

**Causa raiz**: `claude_brain.py` tinha DOIS métodos com tratamento de encoding
diferente. `answer()` (síncrono) já passava `encoding="utf-8"` no subprocess.
`answer_stream()` (streaming, usado pela voz) tinha `text=True` SEM `encoding` →
no Windows a saída UTF-8 do `claude` CLI era decodificada como cp1252 → mojibake.
Só aparecia quando o cérebro era o Claude (a partir de 00:26:14, quando a troca
de 17-18/06 entrou) — entradas anteriores (gpt-4o-mini) estavam limpas.

**Correção**: adicionado `encoding="utf-8", errors="replace"` no `Popen` do
`answer_stream` (claude_brain.py:130), igual ao `answer()`. Para o mojibake na
origem.

**Reparo retroativo**: as 2 entradas já gravadas com mojibake no
`chat_history.json` foram consertadas in-place (round-trip cp1252→utf-8). Zero
mojibake restante, bytes conferidos (`\xc3\xa9`).

Verificação: `pytest tests/` 71/71 · `import claude_brain` OK · bytes do JSON
conferidos limpos.

---

## Adendo 2 — wake word medida na voz real do Murillo + nome fixado em "Javis"

Murillo gravou 5 falas chamando o assistente (`Documents\Gravações de som\
Gravando.mp3`). Rodei pelo MESMO Whisper do Javis (faster_whisper small/cpu/int8/
pt, via o venv do voz-sandbox) pra MEDIR o que o ASR ouve de verdade.

**Resultado:**
- COM o `initial_prompt` atual ("Javis. YouTube. Open WebUI.") → Whisper
  transcreve **"Javis"** toda vez (certo).
- SEM prompt → ouve **"Javes"**. Mas o portão já aceitava as duas, então
  funcionava de qualquer jeito.

**Verdade técnica dita ao Murillo**: a promessa que a voz (Claude) fez de
"treinar/calibrar o ouvido com 5 gravações" NÃO existe nesse setup — faster_whisper
é pré-treinado, sem fine-tuning. A gravação serviu pra MEDIR/PROVAR, não treinar.
E provou que o reconhecimento do nome já estava resolvido.

**Decisão (Murillo)**: nome oficial = **"Javis"**. Enxuguei `WAKE_WORDS` (o portão
`has_wake_word`) de 9 termos pra 5 focados em Javis: `javis, javes, jávis, jáves,
jarvis`. Tirei os palpites antigos (jamba/jambo/jambá/diabes/diaves/chaves) que só
abriam o portão à toa. Eles continuam no `_PREFIX_WORDS` (corte de prefixo em
modo-comando) — por isso os testes de strip (test_voice_bridge 121-123) seguem
passando. O `initial_prompt` do conf.yaml já está "Javis", não mexi.

Verificação: `pytest tests/` 71/71 · portão abre em Javis/Javes/Jarvis, fica quieto
em fala sem o nome.

**Sem commit/push — Murillo revisa e decide o que comita.**
