@echo off
REM ============================================================
REM  JAVIS - sobe Backend (8000) + Chat (8001) e abre a tela
REM  Tudo no venv 3.11 (.venv_chainlit) - Python 3.14 quebra anyio
REM ============================================================
cd /d "%~dp0"

echo.
echo  Iniciando JAVIS...
echo.

REM Backend + Command Center (porta 8000)
start "JAVIS Backend 8000" cmd /k "cd /d %~dp0backend && ..\.venv_chainlit\Scripts\python.exe _run_server.py"

REM Chat operacional (porta 8001)
start "JAVIS Chat 8001" cmd /k "cd /d %~dp0 && .venv_chainlit\Scripts\python.exe -m chainlit run app_ui.py --port 8001"

REM Espera subir e abre o Command Center no navegador
timeout /t 6 /nobreak >nul
start "" "http://localhost:8000/command-center/"

echo.
echo  JAVIS no ar:
echo   - Command Center: http://localhost:8000/command-center/
echo   - Chat:           http://localhost:8001
echo.
echo  (feche as duas janelas "JAVIS Backend" e "JAVIS Chat" para desligar)
echo.
