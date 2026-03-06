@echo off
setlocal enabledelayedexpansion

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
set MODEL_FILE=models\model.gguf

if not exist "%MODEL_FILE%" (
    echo.
    echo ============================================================
    echo   [WARNING] Model LLM ne naydena!
    echo ============================================================
    echo.
    echo   Rekomenduyemye modeli (ot luchshey k bystroy):
    echo.
    echo   1) Qwen2.5-32B Q4_K_M (~20 GB) -- MAKSIMALNOE kachestvo
    echo      Nuzhno 24+ GB RAM
    echo.
    echo   2) Qwen2.5-14B Q4_K_M (~9 GB) -- OTLICHNOE kachestvo
    echo      Nuzhno 12+ GB RAM
    echo.
    echo   3) Qwen2.5-7B Q4_K_M (~5 GB) -- KHOROSHEE kachestvo
    echo      Nuzhno 8+ GB RAM
    echo.
    echo   4) Qwen2.5-3B Q4_K_M (~2.5 GB) -- bazovoe
    echo      Nuzhno 4+ GB RAM
    echo.

    set "DOWNLOAD="
    set /p DOWNLOAD="  Skachat model Qwen2.5-14B (rekomenduyetsya)? (y/n): "
    if /i "!DOWNLOAD!" == "y" (
        echo.
        echo   Ustanovka huggingface-hub...
        pip install huggingface-hub -q
        echo   Skachivanie Qwen2.5-14B-Instruct Q4_K_M...
        echo   Eto mozhet zanyat nekotoroe vremya...
        huggingface-cli download Qwen/Qwen2.5-14B-Instruct-GGUF ^
            qwen2.5-14b-instruct-q4_k_m.gguf ^
            --local-dir models/ --local-dir-use-symlinks False
        if exist "models\qwen2.5-14b-instruct-q4_k_m.gguf" (
            move "models\qwen2.5-14b-instruct-q4_k_m.gguf" "models\model.gguf" >nul
            echo   [OK] Model skachana i ustanovlena!
        )
    ) else (
        echo   Skachayte model pozhe pered ispolzovaniem.
        echo   Sokhranite fayl .gguf kak: models\model.gguf
    )
) else (
    echo   Model naydena: %MODEL_FILE% OK
)

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
