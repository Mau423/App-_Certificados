@echo off
REM Inicia la app de Academia Horizonte con doble clic.
REM Usa el Python del entorno virtual (.venv) de este proyecto.
cd /d "%~dp0"
.venv\Scripts\python.exe app.py
pause
