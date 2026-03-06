@echo off
chcp 65001 >nul
title Word2LaTeX - Starting...

echo ╔══════════════════════════════════════════╗
echo ║     Word2LaTeX - Kill ^& Restart          ║
echo ╚══════════════════════════════════════════╝
echo.

REM Thiết lập thư mục gốc
set ROOT=%~dp0
cd /d "%ROOT%"

REM ============================================
REM 0. TẮT HẾT PROCESSES CŨ
REM ============================================
echo [0/3] Dọn dẹp processes cũ...

REM Tắt cửa sổ cmd cũ theo tên window title
taskkill /fi "WINDOWTITLE eq Word2LaTeX Backend" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Word2LaTeX Frontend" /f >nul 2>&1

REM Kill mọi process đang chiếm port 8000 (backend)
echo       Đang giải phóng port 8000...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING') do (
    if NOT "%%p"=="0" (
        taskkill /PID %%p /F >nul 2>&1
    )
)

REM Kill mọi process đang chiếm port 5173 (frontend)
echo       Đang giải phóng port 5173...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5173 " ^| findstr LISTENING') do (
    if NOT "%%p"=="0" (
        taskkill /PID %%p /F >nul 2>&1
    )
)

REM Xóa __pycache__ để đảm bảo code mới nhất được load
echo       Xóa __pycache__...
if exist "src\__pycache__" rd /s /q "src\__pycache__"
if exist "backend\__pycache__" rd /s /q "backend\__pycache__"

REM Đợi OS giải phóng port
timeout /t 2 /nobreak >nul
echo       OK - Đã dọn sạch.
echo.

REM ============================================
REM 1. Khởi động Backend (FastAPI + Uvicorn)
REM ============================================
echo [1/3] Đang khởi động Backend (port 8000)...

REM Kiểm tra .venv
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else if exist "backend\.venv\Scripts\python.exe" (
    set PYTHON=backend\.venv\Scripts\python.exe
) else (
    set PYTHON=python
)

start "Word2LaTeX Backend" cmd /c "cd /d %ROOT%backend && %ROOT%%PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-dir . --reload-dir %ROOT%src"

REM Đợi backend khởi động
timeout /t 3 /nobreak >nul

REM ============================================
REM 2. Khởi động Frontend (Vite Dev Server)
REM ============================================
echo [2/3] Đang khởi động Frontend (port 5173)...

REM Kiểm tra node_modules
if not exist "frontend\node_modules" (
    echo     Đang cài đặt dependencies frontend...
    cd /d "%ROOT%frontend"
    call npm install
    cd /d "%ROOT%"
)

start "Word2LaTeX Frontend" cmd /c "cd /d %ROOT%frontend && npm run dev"

REM Đợi frontend khởi động
timeout /t 3 /nobreak >nul

REM ============================================
REM 3. Mở trình duyệt
REM ============================================
echo [3/3] Mở trình duyệt...
echo.
echo ╔══════════════════════════════════════════╗
echo ║  Backend:  http://localhost:8000         ║
echo ║  Frontend: http://localhost:5173         ║
echo ║  API Docs: http://localhost:8000/docs    ║
echo ╚══════════════════════════════════════════╝
echo.
start "" "http://localhost:5173"

echo Nhấn phím bất kỳ để DỪNG cả hai server...
pause >nul

REM Dừng cả hai
echo.
echo Đang dừng servers...
taskkill /fi "WINDOWTITLE eq Word2LaTeX Backend" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Word2LaTeX Frontend" /f >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING') do (
    if NOT "%%p"=="0" taskkill /PID %%p /F >nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5173 " ^| findstr LISTENING') do (
    if NOT "%%p"=="0" taskkill /PID %%p /F >nul 2>&1
)
echo Đã dừng. Tạm biệt!
