@echo off
:: Javis — Launcher (robusto)
:: Sobe o servidor se ele nao estiver REALMENTE respondendo e abre o browser.

cd /d C:\Users\noteacer\Desktop\javis\_apps\javis-local-interface

:: Health check de verdade: o servidor responde em http://localhost:8000 ?
curl -s -o nul -m 2 http://localhost:8000/ && goto :abrir

echo.
echo  [Javis] Servidor nao esta respondendo. Subindo...
echo.

:: Janela visivel (nao minimizada) para enxergar erros se cair
:: JAVIS_AUTO_CODEX=1 -> delegacao automatica Claude->Codex ligada (Claude pensa,
:: Codex executa tarefas de codigo, Claude audita depois). Guardrails: sem git
:: commit/push. Pra desligar, troque para 0.
start "Javis Server" cmd /k "cd /d C:\Users\noteacer\Desktop\javis\_apps\javis-local-interface && set JAVIS_AUTO_CODEX=1 && C:\Python314\python.exe backend\server.py"

:: Espera o servidor responder (ate ~25s), checando a cada 1s
set /a tries=0
:wait
timeout /t 1 /nobreak >nul
curl -s -o nul -m 2 http://localhost:8000/ && goto :abrir
set /a tries+=1
if %tries% lss 25 goto :wait

echo.
echo  [Javis] O servidor nao subiu a tempo. Veja a janela "Javis Server" para o erro.
echo.

:abrir
start "" "http://localhost:8000"
