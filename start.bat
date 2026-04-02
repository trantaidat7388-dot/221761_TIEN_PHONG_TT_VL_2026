@echo off
chcp 65001 >nul
title Word2LaTeX - Launcher

echo.
echo ============================================================
echo   Word2LaTeX Converter  ^|  1-Click Launcher (Auto Reset)
echo ============================================================
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%"

REM ============================================================
REM STEP 1: DON DEP SERVER CU (AUTO RESET)
REM ============================================================
echo [1/5] Freeing ports 3000, 5173, 8000 and killing Node...

REM Tat cac cua so CMD cu
taskkill /fi "WINDOWTITLE eq Word2LaTeX*" /f >nul 2>&1

REM San lung tien trinh ngam dang chiem port
for %%T in (8000 5173 3000) do (
    for /f "tokens=5 delims= " %%P in ('netstat -ano 2^>nul ^| findstr /R ":%%T " ^| findstr "LISTENING"') do (
        if NOT "%%P"=="0" if NOT "%%P"=="" (
            echo       - Da diet tien trinh PID %%P tai Port %%T
            taskkill /PID %%P /F >nul 2>&1
        )
    )
)
timeout /t 1 /nobreak >nul
echo       OK - Ports cleared.
echo.

REM ============================================================
REM STEP 2: CLEAN PYCACHE (EP PYTHON NHAN CODE MOI)
REM ============================================================
echo [2/5] Cleaning __pycache__...

for /d /r "%ROOT%" %%D in (__pycache__) do (
    if exist "%%D" rd /s /q "%%D" >nul 2>&1
)
echo       OK - Cache cleared.
echo.

REM ============================================================
REM STEP 3: ACTIVATE VENV & INSTALL DEPENDENCIES
REM ============================================================
echo [3/5] Installing Python dependencies...

if exist "%ROOT%.venv\Scripts\activate.bat" (
    echo       OK - Environment activated.
    call "%ROOT%.venv\Scripts\activate.bat"
) else (
    echo       WARNING: .venv not found. Creating virtual environment...
    python -m venv "%ROOT%.venv"
    if exist "%ROOT%.venv\Scripts\activate.bat" (
        echo       OK - .venv created successfuly.
        call "%ROOT%.venv\Scripts\activate.bat"
    ) else (
        echo       ERROR: Failed to create .venv. Using system Python.
    )
)

echo       Installing dependencies...
pip install -r "%ROOT%backend\requirements.txt" --quiet --disable-pip-version-check
if %ERRORLEVEL% NEQ 0 (
    echo       ERROR: pip install failed. Check your Python environment.
    pause
    exit /b 1
)
echo       OK - Dependencies ready.
echo.

REM ============================================================
REM STEP 4: START BACKEND
REM ============================================================
echo [4/5] Starting Backend (FastAPI on :8000)...

start "Word2LaTeX Backend" cmd /k "chcp 65001 >nul & cd /d ""%ROOT%"" & (if exist "".venv\Scripts\activate.bat"" call "".venv\Scripts\activate.bat"") & python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul
echo       OK - Backend window opened.
echo.

REM ============================================================
REM STEP 5: START FRONTEND
REM ============================================================
echo [5/5] Starting Frontend (Vite on :5173)...

start "Word2LaTeX Frontend" cmd /k "chcp 65001 >nul & cd /d ""%ROOT%frontend"" & (if not exist node_modules npm install --prefer-offline) & npm run dev"

echo       OK - Frontend window opened.
echo.

REM ============================================================
REM AUTO-OPEN BROWSER 
REM ============================================================
echo Waiting 8 seconds for servers to boot...
timeout /t 8 /nobreak >nul
echo Opening http://localhost:5173 in your browser...
start "" http://localhost:5173

echo.
echo HOAN TAT! Ban co the thu nho cua so nay lai.
exit