#!/bin/bash
echo "啟動 ECU 監控系統..."
echo

# 檢查虛擬環境
if [ -f ".venv_new/bin/activate" ]; then
    echo "啟用虛擬環境..."
    source .venv_new/bin/activate
elif [ -f "venv/bin/activate" ]; then
    echo "啟用虛擬環境..."
    source venv/bin/activate
else
    echo "警告: 未發現虛擬環境，使用系統 Python"
fi

echo
echo "首先測試模組安裝..."
python test_modules.py

echo
echo "啟動主程式..."
python main.py
