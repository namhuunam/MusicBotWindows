@echo off
REM Di chuyển vào thư mục chứa file Python
cd /d "%~dp0"
chcp 65001
set PYTHONUTF8=1
REM Chạy file Python
python bot.py

REM Tạm dừng để xem thông báo lỗi (nếu có)
pause
