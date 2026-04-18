@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Word2LaTeX - Ngrok Manager

echo.
echo ============================================================
echo   Trình quản lý Ngrok (Tài khoản mới)
echo ============================================================
echo.

REM Kiểm tra Ngrok đã cài chưa
ngrok --version >nul 2>&1
if errorlevel 1 (
    echo [LOI] Ngrok chưa được cài đặt hoặc chưa được thêm vào PATH.
    echo Vui lòng tải Ngrok tại: https://ngrok.com/download
    pause
    exit /b 1
)

:MENU
cls
echo ============================================================
echo   Trình quản lý Ngrok (Tài khoản mới)
echo ============================================================
echo.
echo 1. Thêm/Cập nhật Ngrok Authtoken (Chỉ làm 1 lần cho tài khoản mới)
echo 2. Chạy Ngrok với Static Domain (Chuẩn nhất)
echo 3. Chạy Ngrok với Link ngẫu nhiên (Dành cho bản miễn phí cơ bản)
echo 4. Thoát
echo.
set "choice="
set /p choice="Chọn hành động (1-4): "

if "!choice!"=="1" (
    set "token="
    set /p token="Nhập Authtoken của bạn: "
    if not "!token!"=="" (
        ngrok config add-authtoken !token!
        echo.
        echo Authtoken đã được lưu thành công!
    ) else (
        echo [!] Bạn chưa nhập token.
    )
    pause
    goto MENU
)

if "!choice!"=="2" (
    set "domain="
    set /p domain="Nhập Static Domain (ví dụ: abc-xyz.ngrok-free.app): "
    if not "!domain!"=="" (
        echo.
        echo Đang khởi chạy Ngrok với domain !domain!...
        echo [!] HÃY NHỚ CẬP NHẬT LINK NÀY VÀO BACKEND/.ENV
        echo.
        ngrok http --domain=!domain! 5173
    ) else (
        echo [!] Bạn chưa nhập domain.
    )
    pause
    goto MENU
)

if "!choice!"=="3" (
    echo.
    echo Đang khởi chạy Ngrok với link ngẫu nhiên...
    echo [!] KHI NGROK HIỆN RA, HÃY COPY LINK "Forwarding" dán vào BACKEND/.ENV
    echo.
    ngrok http 5173
    pause
    goto MENU
)

if "!choice!"=="4" exit /b 0
goto MENU
