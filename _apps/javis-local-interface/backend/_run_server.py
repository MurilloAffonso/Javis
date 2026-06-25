"""Launcher simples do server.py no venv 3.11 (usado pelo iniciar-javis.bat).
Roda a partir da pasta backend/ para resolver 'server:app'."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
