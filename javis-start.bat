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
:: R1 safe startup: adaptadores externos, execucao headless e acoes locais ficam
:: desligados por padrao. Ligue flags explicitamente em outra janela se precisar.
start "Javis Server" cmd /k "cd /d C:\Users\noteacer\Desktop\javis\_apps\javis-local-interface && set JAVIS_ENABLE_EXTERNAL_ADAPTERS=false && set JAVIS_ENABLE_CODEX_EXEC=false && set JAVIS_ENABLE_CLAUDE_EXEC=false && set JAVIS_ENABLE_BROWSER=false && set JAVIS_ENABLE_TELEGRAM=false && set JAVIS_ENABLE_MCP=false && set JAVIS_ENABLE_LOCAL_ACTIONS=false && set JAVIS_ENABLE_VP_EFFECTS=false && set JAVIS_DEV_ALLOW_CORS=false && set JAVIS_AUTO_CODEX=0 && C:\Python314\python.exe backend\server.py"

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
