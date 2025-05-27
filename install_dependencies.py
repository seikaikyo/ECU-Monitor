# install_dependencies.py - 依賴安裝腳本
import subprocess
import sys
import pkg_resources
from pathlib import Path


def check_python_version():
    """檢查 Python 版本"""
    if sys.version_info < (3, 8):
        print("❌ 錯誤: 需要 Python 3.8 或更高版本")
        print(f"   當前版本: {sys.version}")
        return False
    print(f"✅ Python 版本檢查通過: {sys.version}")
    return True


def install_requirements():
    """安裝依賴套件"""
    requirements = [
        'flask==2.3.3', 'flask-socketio==5.3.6', 'pandas==2.0.3',
        'numpy==1.24.3', 'scikit-learn==1.3.0', 'requests==2.31.0',
        'joblib==1.3.2', 'python-socketio==5.8.0', 'eventlet==0.33.3'
    ]

    print("📦 開始安裝依賴套件...")

    for requirement in requirements:
        try:
            print(f"   安裝 {requirement}...")
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', requirement])
        except subprocess.CalledProcessError as e:
            print(f"❌ 安裝 {requirement} 失敗: {e}")
            return False

    print("✅ 所有依賴套件安裝完成")
    return True


def check_optional_dependencies():
    """檢查可選依賴"""
    optional_deps = {'pymodbus': 'PLC Modbus 通訊', 'pyserial': '串列埠通訊'}

    print("\n🔍 檢查可選依賴套件:")
    for package, description in optional_deps.items():
        try:
            pkg_resources.get_distribution(package)
            print(f"   ✅ {package} - {description}")
        except pkg_resources.DistributionNotFound:
            print(f"   ⚠️  {package} - {description} (未安裝，將使用模擬數據)")


def create_config_files():
    """創建配置文件"""
    print("\n📄 創建配置文件...")

    # 創建環境變數文件
    env_content = """# 智慧烘箱監控系統環境變數配置
# PLC 連接設定
PLC_HOST=192.168.1.100
PLC_PORT=502
PLC_TIMEOUT=10

# 監控設定
MONITORING_INTERVAL=30
DATA_RETENTION_DAYS=30

# Web 服務設定  
WEB_HOST=0.0.0.0
WEB_PORT=5000
DEBUG_MODE=false

# AI 模型設定
ANOMALY_CONTAMINATION=0.1
MIN_TRAINING_SAMPLES=50

# 日誌設定
LOG_LEVEL=INFO
LOG_FILE=logs/oven_monitor.log
"""

    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("   ✅ .env 文件已創建")

    # 創建啟動腳本
    start_script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
智慧烘箱 AI 監控系統啟動腳本
\"\"\"

import os
import sys
from pathlib import Path

# 添加當前目錄到 Python 路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 加載環境變數
def load_env():
    env_file = current_dir / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 智慧烘箱 AI 監控系統")
    print("=" * 50)
    
    # 加載環境變數
    load_env()
    
    try:
        # 導入主程式
        from app import main
        main()
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        print("請確認所有依賴套件已正確安裝")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\\n👋 感謝使用智慧烘箱監控系統！")
    except Exception as e:
        print(f"❌ 系統錯誤: {e}")
        sys.exit(1)
"""

    with open('start.py', 'w', encoding='utf-8') as f:
        f.write(start_script)
    print("   ✅ start.py 啟動腳本已創建")

    # 創建目錄結構
    directories = ['logs', 'models', 'data', 'templates']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   ✅ {directory}/ 目錄已創建")


def main():
    """主安裝程序"""
    print("🚀 智慧烘箱 AI 監控系統 - 自動安裝程序")
    print("=" * 50)

    # 檢查 Python 版本
    if not check_python_version():
        return False

    # 安裝依賴
    if not install_requirements():
        return False

    # 檢查可選依賴
    check_optional_dependencies()

    # 創建配置文件
    create_config_files()

    print("\n" + "=" * 50)
    print("✅ 安裝完成！")
    print("\n使用方法:")
    print("1. 修改 .env 文件中的 PLC 連接設定")
    print("2. 執行: python start.py")
    print("3. 打開瀏覽器: http://localhost:5000")
    print("=" * 50)

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)

# ---
