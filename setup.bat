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

:: 5. Install PyTorch (for embeddings/reranker)
echo.
echo -^> Ustanovka PyTorch...
where nvidia-smi >nul 2>&1
if errorlevel 1 goto torch_cpu

:: NVIDIA GPU found — detect CUDA version and install matching torch
python -c "import subprocess,re; o=subprocess.getoutput('nvcc --version'); m=re.search(r'release (\d+)\.(\d+)', o); f=open('_cuda_ver.tmp','w'); f.write(m.group(1)+'.'+m.group(2) if m else ''); f.close()"
set /p CUDA_VER=<_cuda_ver.tmp
del _cuda_ver.tmp
for /f "tokens=1,2 delims=." %%a in ("!CUDA_VER!") do set CUDA_TAG=cu%%a%%b
echo   NVIDIA GPU nayden, CUDA !CUDA_VER! (tag: !CUDA_TAG!)
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/!CUDA_TAG!
if not errorlevel 1 goto torch_done
echo   [WARN] !CUDA_TAG! ne nayden, probuju cu130...
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
if not errorlevel 1 goto torch_done
echo   [WARN] cu130 ne nayden, probuju cu128...
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
if not errorlevel 1 goto torch_done
echo   [WARN] cu128 ne nayden, probuju cu126...
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
if not errorlevel 1 goto torch_done

:torch_cpu
echo   Ustanovka PyTorch (CPU)...
uv pip install torch torchvision
:torch_done

:: 6. Install dependencies
echo.
echo -^> Ustanovka zavisimostey...
uv pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Oshibka ustanovki zavisimostey!
    pause
    exit /b 1
)
echo   Zavisimosti ustanovleny OK

:: 7. Create directories
if not exist "books\" mkdir books
if not exist "output\" mkdir output
if not exist "data\" mkdir data
if not exist "models\" mkdir models

:: 8. Check LM Studio
echo.
echo -^> Proverka LM Studio...
python -c "import urllib.request; urllib.request.urlopen('http://localhost:1234/v1/models', timeout=3); print('ok')" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ============================================================
    echo   [INFO] LM Studio ne zapushchen!
    echo ============================================================
    echo.
    echo   Dlya raboty prilozhenia neobhodimo:
    echo   1. Skachat LM Studio: https://lmstudio.ai
    echo   2. Ustanovit i zapustit LM Studio
    echo   3. Zagruzit model (naprimer: Qwen2.5-14B-Instruct)
    echo   4. Zapustit server: Developer tab -^> Start Server
    echo.
) else (
    echo   LM Studio server rabotaet OK
)

:: 9. Done
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
echo   1. Ubedites chto LM Studio zapushchen i server aktiven
echo   2. Zagruzite knigi cherez interfeys (vkladka "Knigi")
echo   3. Nazhmite "Indeksirovat"
echo   4. Sozdavayte dokumenty ili zadavayte voprosy!
echo.
pause
