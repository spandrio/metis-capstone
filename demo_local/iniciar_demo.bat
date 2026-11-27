@echo off
cd /d "%~dp0.."
echo Metis - demo local
where py >nul 2>nul && (set PY=py) || (set PY=python)
if not exist ".venv\Scripts\streamlit.exe" (
  echo Creando entorno virtual la primera vez, tarda unos minutos...
  %PY% -m venv .venv
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r demo_local\requirements.txt
)
echo Abriendo http://localhost:8501 ...
start "" cmd /c "timeout /t 6 >nul & start http://localhost:8501"
".venv\Scripts\python.exe" -m streamlit run demo_local\app.py --server.headless true --browser.gatherUsageStats false --theme.base light
pause
