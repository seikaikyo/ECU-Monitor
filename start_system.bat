@echo off
echo 啟動 ECU 監控系統...
echo.

REM 檢查虛擬環境
if exist .venv_new\Scripts\activate.bat (
    echo 啟用虛擬環境...
    call .venv_new\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    echo 啟用虛擬環境...
    call venv\Scripts\activate.bat
) else (
    echo 警告: 未發現虛擬環境，使用系統 Python
)

echo.
echo 首先測試模組安裝...
python test_modules.py

echo.
echo 啟動主程式...
python main.py

pause
