@echo off
echo 啟動 DOCX/PPTX 轉 ODF 工具...
echo.

REM 使用 venv 內的 Python 啟動
set PYTHON="%~dp0venv\bin\python.exe"
if not exist %PYTHON% (
    echo 找不到 venv，請先執行: python -m venv venv
    echo 然後執行: venv\bin\pip install flask werkzeug
    pause
    exit /b 1
)

echo 伺服器啟動中，請在瀏覽器開啟 http://localhost:5000
echo 按 Ctrl+C 停止伺服器
echo.
%PYTHON% "%~dp0app.py"
pause
