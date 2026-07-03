# Modularização do frontend — Fatia 1: Vem Passear

**Data:** 2026-07-02

## O que foi decidido
Quebrar o `app.js` monolítico (2.901 linhas, 13 telas) do command-center em módulos ES nativos
(`import`/`export`), um arquivo por tela, **sem mudar comportamento** e **sem build/npm**.
Execução incremental: uma tela por vez, testada no navegador antes da próxima.

## Por quê
- Interface "difícil de mexer": qualquer edição exigia navegar 2.9k linhas.
- Auditoria prévia confirmou que NÃO há `onclick=""` inline (0 ocorrências) — tudo é ligado
  por closures (`el.onclick = () => ...`), então ES Modules é seguro (nenhuma função
  precisa ser global).
- `server.py:56` monta o command-center com `StaticFiles(html=True)` → subpasta `js/` é
  servida com MIME correto, sem 404.

## Alternativas consideradas
- **Migrar pra React/Vite:** rejeitado — troca 1 problema por 3 (build, deps, curva).
- **Big-bang (15 telas de uma vez):** rejeitado — se quebrar, difícil isolar onde.
- **Manter monólito e só conectar endpoints:** rejeitado — cada conexão continuaria cara.

## O que foi feito (Fatia 1)
- **Novo:** `frontend/command-center/js/views/vempassear.js` (872 linhas) — bloco antigo
  1245–2112 do app.js (viewVempassear + todos vp*/at*, dados sintéticos AT_LEADS/AT_MKT).
  Importa 10 símbolos do núcleo: `_esc, h, $, state, BACKEND, tryJson, renderCanvas,
  opToast, opSend, confirmStrong`.
- **app.js:** 2.901 → 2.038 linhas; ganhou `import { viewVempassear }` + `export` dos 10
  helpers compartilhados.
- **index.html:** `<script src>` → `<script type="module" src>`.

## Verificação
- `node --check` OK nos dois arquivos (com import/export removidos p/ check standalone).
- Zero definições vp*/at* restantes no app.js; única ref externa era o router (linha 207).
- Testado no navegador por Murillo (hard refresh, console limpo, abas VP OK) — aprovado.

## Próximo passo
Fatia 2: extrair **Operação** (`viewOperacao` + op*) pra `js/views/operacao.js`,
mantendo `opSend/opToast/confirmStrong` no núcleo (compartilhados com a VP).
Depois: chat, voice, e demais telas; ao final, `app.js` vira só núcleo + router.
