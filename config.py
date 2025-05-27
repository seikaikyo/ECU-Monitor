# config.py - 系統配置文件
import os
from pathlib import Path


class Config:
    """系統配置類"""

    # 基本設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'smart-oven-ai-monitor-2024'

    # 數據庫設定
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'oven_monitoring.db'

    # PLC 連接設定
    PLC_HOST = os.environ.get('PLC_HOST') or '192.168.1.100'
    PLC_PORT = int(os.environ.get('PLC_PORT') or 502)
    PLC_TIMEOUT = int(os.environ.get('PLC_TIMEOUT') or 10)

    # 監控設定
    MONITORING_INTERVAL = int(os.environ.get('MONITORING_INTERVAL') or 30)  # 秒
    DATA_RETENTION_DAYS = int(os.environ.get('DATA_RETENTION_DAYS') or 30)  # 天

    # AI 模型設定
    MODEL_DIR = Path(os.environ.get('MODEL_DIR') or 'models')
    ANOMALY_CONTAMINATION = float(
        os.environ.get('ANOMALY_CONTAMINATION') or 0.1)
    MIN_TRAINING_SAMPLES = int(os.environ.get('MIN_TRAINING_SAMPLES') or 50)

    # Web 服務設定
    WEB_HOST = os.environ.get('WEB_HOST') or '0.0.0.0'
    WEB_PORT = int(os.environ.get('WEB_PORT') or 5000)
    DEBUG_MODE = os.environ.get('DEBUG_MODE', 'False').lower() == 'true'

    # 日誌設定
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'oven_monitor.log'

    # 安全設定
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

    @classmethod
    def init_directories(cls):
        """初始化必要目錄"""
        cls.MODEL_DIR.mkdir(exist_ok=True)

        # 創建日誌目錄
        log_dir = Path(cls.LOG_FILE).parent
        log_dir.mkdir(exist_ok=True)


# ---
