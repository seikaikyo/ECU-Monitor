#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import sys
import os


def run_command(command, description):
    """執行命令並顯示結果"""
    print(f"\n--- {description} ---")
    print(f"執行指令: {' '.join(command)}")

    try:
        result = subprocess.run(command,
                                capture_output=True,
                                text=True,
                                check=True)
        print("✅ 執行成功")
        if result.stdout:
            print("輸出:", result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 執行失敗: {e}")
        if e.stdout:
            print("標準輸出:", e.stdout.strip())
        if e.stderr:
            print("錯誤輸出:", e.stderr.strip())
        return False
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        return False


def check_python_version():
    """檢查 Python 版本"""
    print("=== 檢查 Python 環境 ===")
    print(f"Python 版本: {sys.version}")
    print(f"Python 執行檔: {sys.executable}")

    version_info = sys.version_info
    if version_info.major >= 3 and version_info.minor >= 8:
        print("✅ Python 版本符合要求 (>= 3.8)")
        return True
    else:
        print("❌ Python 版本過舊，建議使用 Python 3.8 或更新版本")
        return False


def upgrade_pip():
    """升級 pip"""
    return run_command(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"], "升級 pip")


def install_requirements():
    """安裝套件依賴"""
    requirements = [
        "pandas>=1.5.0", "numpy>=1.21.0", "requests>=2.25.0",
        "scikit-learn>=1.0.0", "dash>=2.0.0", "dash-core-components>=2.0.0",
        "dash-html-components>=2.0.0", "plotly>=5.0.0"
    ]

    print("\n=== 安裝 Python 套件 ===")
    success_count = 0

    for req in requirements:
        if run_command([sys.executable, "-m", "pip", "install", req],
                       f"安裝 {req}"):
            success_count += 1
        else:
            print(f"⚠️ 安裝 {req} 失敗，繼續安裝其他套件...")

    print(f"\n套件安裝結果: {success_count}/{len(requirements)} 個套件安裝成功")
    return success_count == len(requirements)


def install_from_requirements_file():
    """從 requirements.txt 安裝套件"""
    if os.path.exists("requirements.txt"):
        return run_command(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            "從 requirements.txt 安裝套件")
    else:
        print("requirements.txt 檔案不存在，跳過此步驟")
        return True


def verify_installation():
    """驗證安裝結果"""
    print("\n=== 驗證安裝結果 ===")

    modules_to_test = [
        "pandas", "numpy", "requests", "sklearn", "dash", "plotly"
    ]

    success_count = 0
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module} - 可正常匯入")
            success_count += 1
        except ImportError:
            print(f"❌ {module} - 匯入失敗")

    print(f"\n驗證結果: {success_count}/{len(modules_to_test)} 個模組可正常使用")
    return success_count == len(modules_to_test)


def create_launch_script():
    """建立啟動腳本"""

    # Windows 批次檔
    batch_content = """@echo off
echo 啟動 ECU 監控系統...
echo.

REM 檢查虛擬環境
if exist .venv_new\\Scripts\\activate.bat (
    echo 啟用虛擬環境...
    call .venv_new\\Scripts\\activate.bat
) else if exist venv\\Scripts\\activate.bat (
    echo 啟用虛擬環境...
    call venv\\Scripts\\activate.bat
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
"""

    # Linux/Mac Shell 腳本
    shell_content = """#!/bin/bash
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
"""

    try:
        # 建立 Windows 批次檔
        with open("start_system.bat", "w", encoding="utf-8") as f:
            f.write(batch_content)
        print("✅ 已建立 start_system.bat (Windows 啟動腳本)")

        # 建立 Linux/Mac Shell 腳本
        with open("start_system.sh", "w", encoding="utf-8") as f:
            f.write(shell_content)
        os.chmod("start_system.sh", 0o755)  # 賦予執行權限
        print("✅ 已建立 start_system.sh (Linux/Mac 啟動腳本)")

        return True
    except Exception as e:
        print(f"❌ 建立啟動腳本時發生錯誤: {e}")
        return False


def main():
    """主函數"""
    print("=== ECU 監控系統環境設定工具 ===\n")

    # 檢查 Python 版本
    if not check_python_version():
        print("請升級 Python 版本後重新執行此腳本")
        return False

    # 升級 pip
    upgrade_pip()

    # 安裝套件
    if os.path.exists("requirements.txt"):
        install_success = install_from_requirements_file()
    else:
        install_success = install_requirements()

    # 驗證安裝
    verify_success = verify_installation()

    # 建立啟動腳本
    script_success = create_launch_script()

    print("\n=== 設定完成 ===")

    if install_success and verify_success:
        print("🎉 環境設定成功！")
        print("\n接下來您可以:")
        print("1. 執行 'python test_modules.py' 測試所有模組")
        print("2. 執行 'python dashboard_app.py' 直接啟動儀表板")
        print("3. 執行 'python main.py' 啟動完整系統")

        if script_success:
            print(
                "4. 使用 start_system.bat (Windows) 或 ./start_system.sh (Linux/Mac) 啟動系統"
            )

        return True
    else:
        print("❌ 環境設定過程中遇到問題，請檢查上述錯誤訊息")
        return False


if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n設定過程被中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n設定過程中發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
