# Skill "Verificar Antes de Concluir" + regra anti-fabricação nos prompts — 18/06

## O que foi decidido

Pincei do repo obra/superpowers (analisado a pedido do Murillo) a ideia da skill
`verification-before-completion`, porque ela ataca um bug REAL que pegamos hoje:
o Javis afirmou "Iniciei a execução das remediais" sem nenhum arquivo ter sido
tocado (execução fabricada). Não adotei o framework inteiro — só a 1 ideia que
resolve dor concreta.

## Por que NÃO só um markdown

Skill em `_skills/` que nada carrega = papel de parede, não conserta o bug. O
erro nasce no system prompt do cérebro. Então plugei a regra onde tem dente E
documentei o princípio.

## Mudanças

1. **`backend/agent.py`** (`SYSTEM_AGENT`, caminho do agente tool-use): nova
   regra absoluta 6 — "NÃO FINJA QUE FEZ: nunca diga que executou/iniciou/criou/
   terminou se nenhuma ferramenta foi realmente chamada nesta resposta."
2. **`backend/claude_brain.py`** (`_SYSTEM`, caminho da voz/raciocínio): "NUNCA
   afirme que executou/iniciou/criou/terminou: você só pensa e responde, não age."
   (esse cérebro é raciocínio puro, sem ferramenta — então qualquer "fiz" dele é
   mentira por definição).
3. **`_skills/verificar-antes-de-concluir.md`** (novo): a skill documentada no
   estilo superpowers — propósito, quando usar, o check de 4 passos, tabela de
   "bandeiras vermelhas" (racionalização vs. realidade), formas certas de
   responder, e um aviso de que ela só tem efeito enquanto as regras seguirem
   nos dois prompts.

## Verificação

`pytest tests/` 71/71 · import de `agent` e `claude_brain` OK · asserts
confirmam que as duas regras estão presentes nos prompts.

## Próximo passo / observação honesta

- Isso REDUZ a chance do bug, não dá garantia matemática — modelo de linguagem
  ainda pode escorregar. O reforço real seria nunca persistir no histórico uma
  resposta de "conclusão" sem ação registrada, mas isso é mais invasivo; ficou
  como ideia futura se o problema voltar.
- 2ª ideia do superpowers (reforçar template dos 17 agentes com seção de "red
  flags"): NÃO feita agora — seriam 17 arquivos editados por pouco ganho. Fica
  anotada caso o Murillo queira.

**Sem commit/push — Murillo revisa e decide o que comita.**
