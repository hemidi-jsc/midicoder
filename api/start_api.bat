@echo off
REM Script để khởi động Midicoder WebGUI API Server
REM Chạy file này để start API trên port 6868
REM
REM LƯU Ý: Trước khi chạy API, phải init dự án bằng CLI:
REM   midicoder init
REM Command này sẽ tạo ~/.midicoder/midicoder.json với CWD
REM API sẽ tự động load CWD từ file config này

echo ========================================
echo Midicoder WebGUI API Server
echo ========================================
echo Port: 6868
echo Swagger UI: http://localhost:6868/docs
echo Status API: http://localhost:6868/api/health/status
echo ========================================
echo.
echo LƯU Ý:
echo - Đảm bảo đã chạy: midicoder init
echo - CWD được load từ ~/.midicoder/midicoder.json
echo - Đổi CWD bằng: midicoder config set cwd "new-dir"
echo ========================================
echo.

cd /d "%~dp0"

REM Set PYTHONPATH để Python tìm thấy module 'app'
set PYTHONPATH=%~dp0;%PYTHONPATH%

echo Starting API server...
echo.

REM Chạy uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port 6868

REM Nếu script thoát, chờ user nhấn phím
pause
