@echo off
:: Javis — Launcher

:: Se o servidor já está rodando, só abre o browser
netstat -an 2>nul | findstr ":8000 " >nul 2>&1
if %errorlevel%==0 goto :abrir

:: Inicia o servidor (janela minimizada, fica aberta para ver erros)
start "Javis Server" /MIN cmd /k "cd /d C:\Users\noteacer\Desktop\javis\_apps\javis-local-interface && C:\Python314\python.exe backend\server.py"

:: Aguarda o servidor subir (5s)
timeout /t 5 /nobreak >nul

:abrir
start "" "http://localhost:8000"
