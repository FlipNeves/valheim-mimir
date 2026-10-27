@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
echo ============================================
echo   Mimir API - deixe esta janela aberta
echo   Endereco: http://localhost:8000
echo ============================================
".venv\Scripts\python.exe" -m uvicorn api.main:app --host 0.0.0.0 --port 8000
echo.
echo A API encerrou. Pressione uma tecla para fechar.
pause >nul
