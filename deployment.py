# deployment.py - 部署腳本
import os
import sys
import subprocess
import shutil
from pathlib import Path


class SystemDeployer:
    """系統部署器"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.required_files = ['app.py', 'plc_points.json', 'requirements.txt']
        self.optional_files = ['.env', 'config.py']

    def check_requirements(self):
        """檢查部署需求"""
        print("🔍 檢查部署需求...")

        missing_files = []
        for file in self.required_files:
            if not Path(file).exists():
                missing_files.append(file)

        if missing_files:
            print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
            return False

        print("✅ 必要文件檢查通過")
        return True

    def create_directory_structure(self):
        """創建目錄結構"""
        print("📁 創建目錄結構...")

        directories = [
            'logs', 'models', 'data', 'backups', 'templates', 'static/css',
            'static/js', 'static/images'
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {directory}/")

        return True

    def setup_systemd_service(self):
        """設置 systemd 服務（Linux）"""
        if os.name != 'posix':
            print("⚠️  非 Linux 系統，跳過 systemd 設置")
            return True

        print("🔧 設置 systemd 服務...")

        service_content = f"""[Unit]
Description=Smart Oven AI Monitor
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'oven')}
WorkingDirectory={self.project_root}
Environment=PATH={self.project_root}/venv/bin
ExecStart={sys.executable} {self.project_root}/start.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

        service_file = Path('smart-oven-monitor.service')
        with open(service_file, 'w') as f:
            f.write(service_content)

        print(f"   ✅ 服務文件已創建: {service_file}")
        print("   📝 手動安裝步驟:")
        print(f"      sudo cp {service_file} /etc/systemd/system/")
        print("      sudo systemctl daemon-reload")
        print("      sudo systemctl enable smart-oven-monitor")
        print("      sudo systemctl start smart-oven-monitor")

        return True

    def create_backup_script(self):
        """創建備份腳本"""
        print("💾 創建備份腳本...")

        backup_script = '''#!/bin/bash
# 智慧烘箱監控系統備份腳本

BACKUP_DIR="backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="oven_monitor_backup_${DATE}.tar.gz"

echo "🗂️  開始系統備份..."

# 創建備份目錄
mkdir -p ${BACKUP_DIR}

# 打包文件
tar -czf ${BACKUP_DIR}/${BACKUP_FILE} \
    --exclude="backups" \
    --exclude="logs/*.log" \
    --exclude="__pycache__" \
    --exclude=".git" \
    .

echo "✅ 備份完成: ${BACKUP_DIR}/${BACKUP_FILE}"

# 保留最近5個備份
cd ${BACKUP_DIR}
ls -t oven_monitor_backup_*.tar.gz | tail -n +6 | xargs -r rm

echo "🧹 舊備份清理完成"
'''

        with open('backup.sh', 'w') as f:
            f.write(backup_script)

        # 設置執行權限
        if os.name == 'posix':
            os.chmod('backup.sh', 0o755)

        print("   ✅ backup.sh 已創建")
        return True

    def create_monitoring_script(self):
        """創建監控腳本"""
        print("📊 創建系統監控腳本...")

        monitor_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系統健康監控腳本
"""

import psutil
import time
import requests
from datetime import datetime

def check_system_health():
    """檢查系統健康狀況"""
    health_report = {
        'timestamp': datetime.now().isoformat(),
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'system_status': 'unknown'
    }
    
    # 檢查 Web 服務
    try:
        response = requests.get('http://localhost:5000/api/status', timeout=5)
        if response.status_code == 200:
            health_report['web_service'] = 'running'
            data = response.json()
            health_report['system_status'] = data.get('system_status', 'unknown')
        else:
            health_report['web_service'] = 'error'
    except Exception as e:
        health_report['web_service'] = f'failed: {str(e)}'
    
    return health_report

def main():
    """主程序"""
    print("🔍 系統健康檢查")
    print("=" * 30)
    
    health = check_system_health()
    
    print(f"時間: {health['timestamp']}")
    print(f"CPU 使用率: {health['cpu_percent']:.1f}%")
    print(f"記憶體使用率: {health['memory_percent']:.1f}%")
    print(f"磁碟使用率: {health['disk_percent']:.1f}%")
    print(f"Web 服務: {health['web_service']}")
    print(f"系統狀態: {health['system_status']}")
    
    # 健康評分
    issues = []
    if health['cpu_percent'] > 80:
        issues.append("CPU 使用率過高")
    if health['memory_percent'] > 85:
        issues.append("記憶體使用率過高")
    if health['disk_percent'] > 90:
        issues.append("磁碟空間不足")
    if health['web_service'] != 'running':
        issues.append("Web 服務異常")
    
    if issues:
        print("\\n⚠️  發現問題:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("\\n✅ 系統運行正常")

if __name__ == "__main__":
    main()
'''

        with open('health_check.py', 'w', encoding='utf-8') as f:
            f.write(monitor_script)

        print("   ✅ health_check.py 已創建")
        return True

    def deploy(self):
        """執行部署"""
        print("🚀 開始部署智慧烘箱監控系統")
        print("=" * 50)

        steps = [("檢查需求", self.check_requirements),
                 ("創建目錄", self.create_directory_structure),
                 ("設置服務", self.setup_systemd_service),
                 ("創建備份", self.create_backup_script),
                 ("系統監控", self.create_monitoring_script)]

        for step_name, step_func in steps:
            try:
                if not step_func():
                    print(f"❌ {step_name} 失敗")
                    return False
            except Exception as e:
                print(f"❌ {step_name} 錯誤: {e}")
                return False

        print("\n" + "=" * 50)
        print("✅ 部署完成！")
        print("\n📋 部署後檢查清單:")
        print("1. 檢查 .env 文件中的配置")
        print(
            "2. 測試 PLC 連接: python -c \"from app import *; monitor = SmartOvenMonitor(); print('OK')\""
        )
        print("3. 啟動系統: python start.py")
        print("4. 檢查 Web 界面: http://localhost:5000")
        print("5. 執行健康檢查: python health_check.py")
        print("=" * 50)

        return True


if __name__ == "__main__":
    deployer = SystemDeployer()
    success = deployer.deploy()
    sys.exit(0 if success else 1)
