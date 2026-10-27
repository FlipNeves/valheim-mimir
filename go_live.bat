@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
echo ============================================
echo   Mimir - subindo API + tunel publico
echo   Deixe as duas janelas abertas enquanto jogam.
echo ============================================
start "Mimir API" ".venv\Scripts\python.exe" -m uvicorn api.main:app --host 0.0.0.0 --port 8000
timeout /t 8 /nobreak >nul
".venv\Scripts\python.exe" -m scripts.serve_public
echo.
echo Encerrado. Pressione uma tecla para fechar.
pause >nul
