@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo    Study AI Assistant -- Ustanovka (Windows)
echo    Lokalnaya II-sistema dlya ucheby
echo ============================================================
echo.

:: 1. Check Python
echo -^> Proverka Python...
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python ne nayden! Ustanovite Python 3.9+ s python.org
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python -c "import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")"') do set PYVER=%%i
echo   Python %PYVER% OK

:: 2. Virtual environment
echo.
echo -^> Virtualnoe okruzhenie...
if not exist "venv\" (
    python -m venv venv
    echo   Sozdano OK
) else (
    echo   Uzhe sushchestvuet OK
)

:: 3. Activate venv
call venv\Scripts\activate.bat

:: 4. Upgrade pip
echo.
echo -^> Obnovlenie pip...
python -m pip install --upgrade pip -q

:: 5. Install dependencies
echo.
echo -^> Ustanovka zavisimostey (mozhet zanyat 5-10 minut)...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [ERROR] Oshibka ustanovki zavisimostey!
    pause
    exit /b 1
)
echo   Zavisimosti ustanovleny OK

:: 6. Create directories
if not exist "books\" mkdir books
if not exist "output\" mkdir output
if not exist "data\" mkdir data
if not exist "models\" mkdir models

:: 7. Check model
echo.
echo -^> Proverka LLM modeli...
if exist "models\model.gguf" goto model_ok
if exist "models\qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf" goto model_ok
echo.
echo ============================================================
echo   [WARNING] Model LLM ne naydena! Skachivanie...
echo ============================================================
echo.
pip install huggingface-hub -q
hf download Qwen/Qwen2.5-14B-Instruct-GGUF --include "qwen2.5-14b-instruct-q4_k_m-*.gguf" --local-dir models/
if exist "models\qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf" echo   [OK] Model skachana!
goto done_model
:model_ok
echo   Model naydena: models\model.gguf OK
:done_model

:: 8. Done
echo.
echo ============================================================
echo   [OK] Ustanovka zavershena!
echo ============================================================
echo.
echo   Zapusk:
echo.
echo     venv\Scripts\activate
echo     python main.py
echo.
echo   Otkroetsya GUI v brauzere: http://localhost:7860
echo   REST API budet dostupno na: http://localhost:8000
echo.
echo   1. Zagruzite knigi cherez interfeys (vkladka "Knigi")
echo   2. Nazhmite "Indeksirovat"
echo   3. Sozdavayte dokumenty ili zadavayte voprosy!
echo.
pause
