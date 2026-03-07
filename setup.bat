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

:: 2. Install uv if missing
echo.
echo -^> Proverka uv...
where uv >nul 2>&1
if errorlevel 1 (
    echo   uv ne nayden, ustanavlivayu...
    pip install uv
)
echo   uv OK

:: 3. Virtual environment
echo.
echo -^> Virtualnoe okruzhenie...
if not exist "venv\" (
    uv venv venv
    echo   Sozdano OK
) else (
    echo   Uzhe sushchestvuet OK
)

:: 4. Activate venv
call venv\Scripts\activate.bat

:: 5. Install PyTorch with CUDA
echo.
echo -^> Ustanovka PyTorch (CUDA 12.6)...
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
if errorlevel 1 (
    echo   [WARN] PyTorch CUDA ne ustanovlen, ustanavlivayu CPU versiju...
    uv pip install torch
)

:: 6. Install llama-cpp-python with CUDA (requires pip for cmake args)
echo.
echo -^> Ustanovka llama-cpp-python s CUDA...
pip install llama-cpp-python --force-reinstall --no-cache-dir -C cmake.args="-DGGML_CUDA=ON"
if errorlevel 1 (
    echo   [WARN] llama-cpp-python CUDA ne ustanovlen, ustanavlivayu CPU versiju...
    uv pip install llama-cpp-python
)

:: 7. Install remaining dependencies
echo.
echo -^> Ustanovka zavisimostey (mozhet zanyat 5-10 minut)...
uv pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Oshibka ustanovki zavisimostey!
    pause
    exit /b 1
)
echo   Zavisimosti ustanovleny OK

:: 8. Create directories
if not exist "books\" mkdir books
if not exist "output\" mkdir output
if not exist "data\" mkdir data
if not exist "models\" mkdir models

:: 9. Check model
echo.
echo -^> Proverka LLM modeli...
if exist "models\model.gguf" goto model_ok
if exist "models\qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf" goto model_ok
echo.
echo ============================================================
echo   [WARNING] Model LLM ne naydena! Skachivanie...
echo ============================================================
echo.
uv pip install huggingface-hub
hf download Qwen/Qwen2.5-14B-Instruct-GGUF --include "qwen2.5-14b-instruct-q4_k_m-*.gguf" --local-dir models/
if exist "models\qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf" echo   [OK] Model skachana!
goto done_model
:model_ok
echo   Model naydena OK
:done_model

:: 10. Done
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
