import pandas as pd
import numpy as np
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sqlite3
from pathlib import Path

# AI 相關模組
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import joblib

# Web 相關模組
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading

# Modbus 通訊模組
try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.exceptions import ModbusException
    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False
    print("警告: pymodbus 未安裝，將使用模擬數據")

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('oven_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ])
logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """警報等級"""
    NORMAL = "正常"
    WARNING = "警告"
    CRITICAL = "嚴重"


@dataclass
class PLCMetric:
    """PLC 指標數據結構"""
    id: str
    name: str
    value: float
    unit: str
    timestamp: datetime
    status: AlertLevel = AlertLevel.NORMAL


@dataclass
class AnomalyResult:
    """異常檢測結果"""
    timestamp: datetime
    is_anomaly: bool
    anomaly_score: float
    affected_metrics: List[str]
    description: str
    alert_level: AlertLevel


class DatabaseManager:
    """數據庫管理器"""

    def __init__(self, db_path: str = "oven_monitoring.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化數據庫"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 創建指標數據表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    device_id INTEGER,
                    INDEX(metric_id),
                    INDEX(timestamp)
                )
            ''')

            # 創建異常記錄表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_anomaly BOOLEAN NOT NULL,
                    anomaly_score REAL,
                    affected_metrics TEXT,
                    description TEXT,
                    alert_level TEXT,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')

            # 創建AI模型記錄表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    model_path TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    accuracy REAL,
                    is_active BOOLEAN DEFAULT FALSE
                )
            ''')

            conn.commit()

    def save_metrics(self, metrics: List[PLCMetric]):
        """保存指標數據"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for metric in metrics:
                cursor.execute(
                    '''
                    INSERT INTO metrics (metric_id, metric_name, value, unit, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (metric.id, metric.name, metric.value, metric.unit,
                      metric.timestamp))

            conn.commit()

    def save_anomaly(self, anomaly: AnomalyResult):
        """保存異常記錄"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                '''
                INSERT INTO anomalies (timestamp, is_anomaly, anomaly_score, 
                                     affected_metrics, description, alert_level)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (anomaly.timestamp, anomaly.is_anomaly, anomaly.anomaly_score,
                  ','.join(anomaly.affected_metrics), anomaly.description,
                  anomaly.alert_level.value))

            conn.commit()

    def get_recent_metrics(self, hours: int = 24) -> pd.DataFrame:
        """獲取最近的指標數據"""
        with sqlite3.connect(self.db_path) as conn:
            since_time = datetime.now() - timedelta(hours=hours)

            query = '''
                SELECT metric_id, metric_name, value, unit, timestamp
                FROM metrics 
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            '''

            return pd.read_sql_query(query, conn, params=[since_time])


class PLCDataReader:
    """PLC 數據讀取器"""

    def __init__(self, config_path: str = "plc_points.json"):
        self.config = self.load_config(config_path)
        self.clients = {}
        self.last_read_time = {}

    def load_config(self, config_path: str) -> dict:
        """加載 PLC 配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"配置文件 {config_path} 不存在")
            return {"metric_groups": []}

    def connect_plc(self,
                    host: str,
                    port: int = 502) -> Optional[ModbusTcpClient]:
        """連接 PLC"""
        if not MODBUS_AVAILABLE:
            return None

        try:
            client = ModbusTcpClient(host=host, port=port, timeout=10)
            if client.connect():
                logger.info(f"成功連接到 PLC: {host}:{port}")
                return client
            else:
                logger.error(f"無法連接到 PLC: {host}:{port}")
                return None
        except Exception as e:
            logger.error(f"PLC 連接錯誤: {e}")
            return None

    def read_modbus_registers(self,
                              client: ModbusTcpClient,
                              start_address: int,
                              count: int,
                              device_id: int = 1) -> Optional[List[int]]:
        """讀取 Modbus 寄存器"""
        try:
            result = client.read_holding_registers(
                address=start_address - 1,  # Modbus 地址從0開始
                count=count,
                slave=device_id)

            if result.isError():
                logger.error(f"Modbus 讀取錯誤: {result}")
                return None

            return result.registers
        except Exception as e:
            logger.error(f"讀取寄存器錯誤: {e}")
            return None

    def parse_register_value(self, registers: List[int], offset: int,
                             data_type: str, scale_factor: float) -> float:
        """解析寄存器值"""
        try:
            if data_type == "INT16":
                # 處理有符號16位整數
                raw_value = registers[offset]
                if raw_value > 32767:
                    raw_value -= 65536
                return raw_value / scale_factor

            elif data_type == "FLOAT32":
                # 處理32位浮點數（需要兩個寄存器）
                if offset + 1 < len(registers):
                    # 高位在前，低位在後
                    high_word = registers[offset]
                    low_word = registers[offset + 1]

                    # 組合成32位整數，然後轉換為浮點數
                    combined = (high_word << 16) | low_word
                    float_bytes = combined.to_bytes(4,
                                                    byteorder='big',
                                                    signed=False)
                    import struct
                    float_value = struct.unpack('>f', float_bytes)[0]
                    return float_value / scale_factor
                else:
                    logger.warning(f"FLOAT32 數據不足，offset: {offset}")
                    return 0.0

            else:
                logger.warning(f"不支援的數據類型: {data_type}")
                return 0.0

        except Exception as e:
            logger.error(f"解析寄存器值錯誤: {e}")
            return 0.0

    def read_all_metrics(self,
                         plc_host: str = "192.168.1.100") -> List[PLCMetric]:
        """讀取所有指標"""
        metrics = []
        current_time = datetime.now()

        for group in self.config.get("metric_groups", []):
            group_name = group["group_name"]
            device_id = group["device_id"]
            start_address = group["start_address"]
            count = group["count"]

            # 獲取或創建 PLC 客戶端
            client_key = f"{plc_host}_{device_id}"
            if client_key not in self.clients:
                self.clients[client_key] = self.connect_plc(plc_host)

            client = self.clients[client_key]

            if client is None:
                # 使用模擬數據
                logger.warning(f"使用模擬數據替代 {group_name}")
                metrics.extend(self.generate_mock_data(group, current_time))
                continue

            # 讀取寄存器數據
            registers = self.read_modbus_registers(client, start_address,
                                                   count, device_id)

            if registers is None:
                logger.warning(f"無法讀取 {group_name} 數據，使用模擬數據")
                metrics.extend(self.generate_mock_data(group, current_time))
                continue

            # 解析每個指標
            for metric_config in group["metrics"]:
                try:
                    value = self.parse_register_value(
                        registers, metric_config["register_offset"],
                        metric_config["data_type"],
                        metric_config["scale_factor"])

                    metric = PLCMetric(id=metric_config["id"],
                                       name=metric_config["name"],
                                       value=value,
                                       unit=metric_config["unit"],
                                       timestamp=current_time)
                    metrics.append(metric)

                except Exception as e:
                    logger.error(f"解析指標 {metric_config['id']} 錯誤: {e}")

        logger.info(f"讀取了 {len(metrics)} 個指標數據")
        return metrics

    def generate_mock_data(self, group_config: dict,
                           timestamp: datetime) -> List[PLCMetric]:
        """生成模擬數據"""
        mock_metrics = []

        for metric_config in group_config["metrics"]:
            # 根據指標類型生成合理的模擬值
            metric_id = metric_config["id"]

            if "temp" in metric_id:
                # 溫度類指標：150-200°C 範圍
                base_value = 175 + np.sin(time.time() / 300) * 15
                noise = np.random.normal(0, 2)
                value = max(100, min(250, base_value + noise))

            elif "humidity" in metric_id or "濕度" in metric_config["name"]:
                # 濕度類指標：30-60% 範圍
                base_value = 45 + np.sin(time.time() / 200) * 10
                noise = np.random.normal(0, 2)
                value = max(20, min(80, base_value + noise))

            elif "power" in metric_id or "功率" in metric_config["name"]:
                # 功率類指標：1500-3000W 範圍
                base_value = 2250 + np.sin(time.time() / 400) * 400
                noise = np.random.normal(0, 50)
                value = max(1000, min(4000, base_value + noise))

            elif "current" in metric_id or "電流" in metric_config["name"]:
                # 電流類指標：10-50A 範圍
                base_value = 25 + np.sin(time.time() / 180) * 10
                noise = np.random.normal(0, 1)
                value = max(5, min(60, base_value + noise))

            elif "freq" in metric_id or "頻率" in metric_config["name"]:
                # 頻率類指標：40-60Hz 範圍
                base_value = 50 + np.sin(time.time() / 120) * 5
                noise = np.random.normal(0, 0.5)
                value = max(30, min(70, base_value + noise))

            elif "pressure" in metric_id or "壓力" in metric_config["name"]:
                # 壓力類指標：根據單位設定範圍
                if metric_config["unit"] == "kPa":
                    base_value = 500 + np.sin(time.time() / 250) * 100
                    noise = np.random.normal(0, 10)
                    value = max(200, min(800, base_value + noise))
                else:  # Pa
                    base_value = 100 + np.sin(time.time() / 150) * 20
                    noise = np.random.normal(0, 5)
                    value = max(50, min(200, base_value + noise))

            else:
                # 其他指標：通用範圍
                base_value = 100 + np.sin(time.time() / 300) * 20
                noise = np.random.normal(0, 5)
                value = max(50, min(150, base_value + noise))

            # 偶爾添加異常值（5% 機率）
            if np.random.random() < 0.05:
                value *= np.random.choice([0.7, 1.4])  # 異常偏高或偏低

            metric = PLCMetric(id=metric_id,
                               name=metric_config["name"],
                               value=round(value, 2),
                               unit=metric_config["unit"],
                               timestamp=timestamp)
            mock_metrics.append(metric)

        return mock_metrics

    def close_connections(self):
        """關閉所有 PLC 連接"""
        for client in self.clients.values():
            if client:
                client.close()
        self.clients.clear()


class SmartOvenAI:
    """智慧烘箱 AI 分析引擎"""

    def __init__(self, model_path: str = "models/"):
        self.model_path = Path(model_path)
        self.model_path.mkdir(exist_ok=True)

        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(contamination=0.1,
                                                random_state=42,
                                                n_estimators=200)

        self.feature_columns = []
        self.is_trained = False
        self.training_history = []

    def prepare_features(self,
                         metrics_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """準備機器學習特徵"""
        if metrics_df.empty:
            return None

        try:
            # 轉換時間戳格式
            if 'timestamp' in metrics_df.columns:
                metrics_df['timestamp'] = pd.to_datetime(
                    metrics_df['timestamp'])

            # 透視表格式化
            pivot_df = metrics_df.pivot_table(index='timestamp',
                                              columns='metric_id',
                                              values='value',
                                              aggfunc='mean')

            # 處理缺失值
            pivot_df = pivot_df.fillna(method='ffill').fillna(method='bfill')

            # 添加時間特徵
            pivot_df['hour'] = pivot_df.index.hour
            pivot_df['day_of_week'] = pivot_df.index.dayofweek
            pivot_df['minute'] = pivot_df.index.minute

            # 添加統計特徵
            numeric_cols = pivot_df.select_dtypes(include=[np.number]).columns
            base_cols = [
                col for col in numeric_cols
                if col not in ['hour', 'day_of_week', 'minute']
            ]

            for col in base_cols:
                if len(pivot_df[col].dropna()) > 10:
                    # 滾動統計
                    pivot_df[f'{col}_ma5'] = pivot_df[col].rolling(
                        5, min_periods=1).mean()
                    pivot_df[f'{col}_std5'] = pivot_df[col].rolling(
                        5, min_periods=1).std()
                    pivot_df[f'{col}_diff'] = pivot_df[col].diff()

                    # 異常程度特徵
                    mean_val = pivot_df[col].mean()
                    std_val = pivot_df[col].std()
                    if std_val > 0:
                        pivot_df[f'{col}_zscore'] = (pivot_df[col] -
                                                     mean_val) / std_val

            # 清理數據
            cleaned_df = pivot_df.dropna()

            if cleaned_df.empty:
                logger.warning("特徵準備後沒有可用數據")
                return None

            return cleaned_df

        except Exception as e:
            logger.error(f"準備特徵時發生錯誤: {e}")
            return None

    def train_model(self, features_df: pd.DataFrame) -> bool:
        """訓練 AI 模型"""
        if features_df is None or features_df.empty:
            return False

        try:
            # 選擇數值特徵
            numeric_features = features_df.select_dtypes(include=[np.number])

            # 移除常數列
            valid_cols = []
            for col in numeric_features.columns:
                if numeric_features[col].std() > 1e-8:
                    valid_cols.append(col)

            if len(valid_cols) < 2:
                logger.warning("有效特徵數量不足")
                return False

            numeric_features = numeric_features[valid_cols]
            self.feature_columns = valid_cols

            # 標準化
            scaled_data = self.scaler.fit_transform(numeric_features)

            # 訓練異常檢測模型
            self.anomaly_detector.fit(scaled_data)

            # 保存模型
            self.save_model()

            self.is_trained = True

            # 記錄訓練歷史
            training_info = {
                'timestamp': datetime.now(),
                'features_count': len(valid_cols),
                'samples_count': len(numeric_features),
                'feature_names': valid_cols
            }
            self.training_history.append(training_info)

            logger.info(
                f"AI 模型訓練完成，使用 {len(valid_cols)} 個特徵，{len(numeric_features)} 個樣本"
            )
            return True

        except Exception as e:
            logger.error(f"模型訓練錯誤: {e}")
            return False

    def predict_anomalies(self,
                          features_df: pd.DataFrame) -> List[AnomalyResult]:
        """預測異常"""
        if not self.is_trained or features_df is None or features_df.empty:
            return []

        try:
            # 選擇相同的特徵
            if not all(col in features_df.columns
                       for col in self.feature_columns):
                logger.warning("特徵不匹配，無法進行預測")
                return []

            numeric_features = features_df[self.feature_columns]
            scaled_data = self.scaler.transform(numeric_features)

            # 預測異常
            predictions = self.anomaly_detector.predict(scaled_data)
            scores = self.anomaly_detector.decision_function(scaled_data)

            results = []
            for i, (timestamp, is_anomaly, score) in enumerate(
                    zip(features_df.index, predictions == -1, scores)):
                if is_anomaly:
                    # 找出最異常的指標
                    row_data = numeric_features.iloc[i]
                    affected_metrics = self.identify_anomalous_metrics(
                        row_data)

                    # 確定警報等級
                    if score < -0.5:
                        alert_level = AlertLevel.CRITICAL
                    elif score < -0.2:
                        alert_level = AlertLevel.WARNING
                    else:
                        alert_level = AlertLevel.NORMAL

                    description = f"檢測到異常模式，異常分數: {score:.3f}"
                    if affected_metrics:
                        description += f"，主要異常指標: {', '.join(affected_metrics[:3])}"

                    result = AnomalyResult(timestamp=timestamp,
                                           is_anomaly=is_anomaly,
                                           anomaly_score=score,
                                           affected_metrics=affected_metrics,
                                           description=description,
                                           alert_level=alert_level)
                    results.append(result)

            logger.info(f"異常檢測完成，發現 {len(results)} 個異常")
            return results

        except Exception as e:
            logger.error(f"異常預測錯誤: {e}")
            return []

    def identify_anomalous_metrics(self, row_data: pd.Series) -> List[str]:
        """識別異常指標"""
        anomalous_metrics = []

        try:
            # 計算 Z-score
            for col in row_data.index:
                if col.endswith('_zscore'):
                    original_col = col.replace('_zscore', '')
                    z_score = abs(row_data[col])

                    if z_score > 2.5:  # Z-score 閾值
                        anomalous_metrics.append(original_col)

            # 如果沒有 Z-score 特徵，使用其他方法
            if not anomalous_metrics:
                # 尋找最大偏差的指標
                base_cols = [
                    col for col in row_data.index if not any(
                        suffix in col
                        for suffix in ['_ma5', '_std5', '_diff', '_zscore'])
                ]

                # 簡單的偏差檢測
                for col in base_cols[:5]:  # 只檢查前5個主要指標
                    anomalous_metrics.append(col)

        except Exception as e:
            logger.error(f"識別異常指標錯誤: {e}")

        return anomalous_metrics[:5]  # 最多返回5個異常指標

    def save_model(self):
        """保存模型"""
        try:
            model_data = {
                'scaler': self.scaler,
                'anomaly_detector': self.anomaly_detector,
                'feature_columns': self.feature_columns,
                'training_time': datetime.now()
            }

            model_file = self.model_path / f"oven_ai_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            joblib.dump(model_data, model_file)
            logger.info(f"模型已保存到: {model_file}")

        except Exception as e:
            logger.error(f"保存模型錯誤: {e}")

    def load_model(self, model_file: str):
        """加載模型"""
        try:
            model_data = joblib.load(model_file)
            self.scaler = model_data['scaler']
            self.anomaly_detector = model_data['anomaly_detector']
            self.feature_columns = model_data['feature_columns']
            self.is_trained = True

            logger.info(f"模型已從 {model_file} 加載")
            return True

        except Exception as e:
            logger.error(f"加載模型錯誤: {e}")
            return False


class SmartOvenMonitor:
    """智慧烘箱監控系統主控制器"""

    def __init__(self,
                 plc_host: str = "192.168.1.100",
                 config_path: str = "plc_points.json"):
        self.plc_host = plc_host
        self.db_manager = DatabaseManager()
        self.plc_reader = PLCDataReader(config_path)
        self.ai_engine = SmartOvenAI()

        self.is_running = False
        self.monitoring_thread = None
        self.current_metrics = []
        self.recent_anomalies = []

        # 統計資訊
        self.stats = {
            'total_readings': 0,
            'anomaly_count': 0,
            'last_update': None,
            'system_status': 'STARTING'
        }

    def start_monitoring(self, interval: int = 30):
        """開始監控"""
        if self.is_running:
            logger.warning("監控系統已在運行中")
            return

        self.is_running = True
        self.stats['system_status'] = 'RUNNING'

        self.monitoring_thread = threading.Thread(target=self._monitoring_loop,
                                                  args=(interval, ),
                                                  daemon=True)
        self.monitoring_thread.start()
        logger.info(f"監控系統已啟動，採樣間隔: {interval} 秒")

    def stop_monitoring(self):
        """停止監控"""
        self.is_running = False
        self.stats['system_status'] = 'STOPPED'

        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

        self.plc_reader.close_connections()
        logger.info("監控系統已停止")

    def _monitoring_loop(self, interval: int):
        """監控主循環"""
        logger.info("開始監控循環")

        # 首次訓練模型
        self._initial_training()

        while self.is_running:
            try:
                # 讀取 PLC 數據
                metrics = self.plc_reader.read_all_metrics(self.plc_host)

                if metrics:
                    # 保存到數據庫
                    self.db_manager.save_metrics(metrics)
                    self.current_metrics = metrics

                    # 異常檢測
                    self._perform_anomaly_detection()

                    # 更新統計
                    self.stats['total_readings'] += len(metrics)
                    self.stats['last_update'] = datetime.now()

                    logger.info(f"成功處理 {len(metrics)} 個指標數據")

                time.sleep(interval)

            except Exception as e:
                logger.error(f"監控循環錯誤: {e}")
                time.sleep(interval)

    def _initial_training(self):
        """初始模型訓練"""
        try:
            # 獲取歷史數據
            historical_data = self.db_manager.get_recent_metrics(hours=48)

            if len(historical_data) < 100:
                logger.info("歷史數據不足，將在運行過程中累積數據進行訓練")
                return

            # 準備特徵並訓練模型
            features_df = self.ai_engine.prepare_features(historical_data)
            if features_df is not None:
                success = self.ai_engine.train_model(features_df)
                if success:
                    logger.info("AI 模型初始訓練完成")
                else:
                    logger.warning("AI 模型初始訓練失敗")

        except Exception as e:
            logger.error(f"初始訓練錯誤: {e}")

    def _perform_anomaly_detection(self):
        """執行異常檢測"""
        try:
            if not self.ai_engine.is_trained:
                # 嘗試重新訓練
                recent_data = self.db_manager.get_recent_metrics(hours=2)
                if len(recent_data) >= 50:
                    features_df = self.ai_engine.prepare_features(recent_data)
                    if features_df is not None:
                        self.ai_engine.train_model(features_df)
                return

            # 獲取最近數據進行異常檢測
            recent_data = self.db_manager.get_recent_metrics(hours=1)
            if len(recent_data) < 10:
                return

            features_df = self.ai_engine.prepare_features(recent_data)
            if features_df is not None:
                anomalies = self.ai_engine.predict_anomalies(features_df)

                for anomaly in anomalies:
                    self.db_manager.save_anomaly(anomaly)
                    self.recent_anomalies.append(anomaly)
                    self.stats['anomaly_count'] += 1

                    # 記錄異常
                    logger.warning(f"檢測到異常: {anomaly.description}")

                # 保持最近100個異常記錄
                if len(self.recent_anomalies) > 100:
                    self.recent_anomalies = self.recent_anomalies[-100:]

        except Exception as e:
            logger.error(f"異常檢測錯誤: {e}")

    def get_current_status(self) -> Dict:
        """獲取當前系統狀態"""
        try:
            # 計算關鍵指標
            temp_metrics = [
                m for m in self.current_metrics if 'temp' in m.id.lower()
            ]
            power_metrics = [
                m for m in self.current_metrics if 'power' in m.id.lower()
            ]

            avg_temp = np.mean([m.value
                                for m in temp_metrics]) if temp_metrics else 0
            total_power = sum([m.value
                               for m in power_metrics]) if power_metrics else 0

            # 計算效率分數（簡化算法）
            efficiency_score = min(
                100, max(0, 100 - (len(self.recent_anomalies) * 2)))

            # 最近異常數量
            recent_anomalies_24h = len([
                a for a in self.recent_anomalies
                if (datetime.now() - a.timestamp).total_seconds() < 86400
            ])

            return {
                'system_status':
                self.stats['system_status'],
                'last_update':
                self.stats['last_update'].isoformat()
                if self.stats['last_update'] else None,
                'total_readings':
                self.stats['total_readings'],
                'current_temp':
                round(avg_temp, 1),
                'current_power':
                round(total_power, 0),
                'efficiency_score':
                round(efficiency_score, 1),
                'anomaly_count_24h':
                recent_anomalies_24h,
                'ai_model_trained':
                self.ai_engine.is_trained,
                'active_metrics_count':
                len(self.current_metrics),
                'recent_anomalies': [
                    {
                        'timestamp': a.timestamp.isoformat(),
                        'description': a.description,
                        'alert_level': a.alert_level.value,
                        'affected_metrics': a.affected_metrics[:3]  # 只顯示前3個
                    } for a in self.recent_anomalies[-5:]  # 最近5個異常
                ]
            }
        except Exception as e:
            logger.error(f"獲取系統狀態錯誤: {e}")
            return {'error': str(e)}

    def get_metrics_data(self, hours: int = 1) -> Dict:
        """獲取指標數據"""
        try:
            df = self.db_manager.get_recent_metrics(hours)

            if df.empty:
                return {'timestamps': [], 'metrics': {}}

            # 按時間排序
            df = df.sort_values('timestamp')

            # 轉換為前端需要的格式
            timestamps = df['timestamp'].dt.strftime('%H:%M:%S').tolist()

            metrics_data = {}
            for metric_id in df['metric_id'].unique():
                metric_df = df[df['metric_id'] == metric_id]
                metrics_data[metric_id] = {
                    'name': metric_df['metric_name'].iloc[0],
                    'unit': metric_df['unit'].iloc[0],
                    'values': metric_df['value'].tolist()
                }

            return {'timestamps': timestamps, 'metrics': metrics_data}

        except Exception as e:
            logger.error(f"獲取指標數據錯誤: {e}")
            return {'error': str(e)}


# Flask Web 應用
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局監控系統實例
monitor = None


@app.route('/')
def index():
    """主頁"""
    return render_template('smart_oven_dashboard.html')


@app.route('/api/status')
def api_status():
    """獲取系統狀態 API"""
    if monitor:
        return jsonify(monitor.get_current_status())
    else:
        return jsonify({'error': '監控系統未啟動'}), 500


@app.route('/api/metrics')
def api_metrics():
    """獲取指標數據 API"""
    hours = request.args.get('hours', 1, type=int)
    if monitor:
        return jsonify(monitor.get_metrics_data(hours))
    else:
        return jsonify({'error': '監控系統未啟動'}), 500


@app.route('/api/start', methods=['POST'])
def api_start():
    """啟動監控 API"""
    global monitor
    try:
        if monitor is None:
            data = request.get_json() or {}
            plc_host = data.get('plc_host', '192.168.1.100')
            interval = data.get('interval', 30)

            monitor = SmartOvenMonitor(plc_host=plc_host)
            monitor.start_monitoring(interval)

            return jsonify({'message': '監控系統已啟動', 'status': 'success'})
        else:
            return jsonify({'message': '監控系統已在運行中', 'status': 'warning'})
    except Exception as e:
        logger.error(f"啟動監控錯誤: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stop', methods=['POST'])
def api_stop():
    """停止監控 API"""
    global monitor
    try:
        if monitor:
            monitor.stop_monitoring()
            monitor = None
            return jsonify({'message': '監控系統已停止', 'status': 'success'})
        else:
            return jsonify({'message': '監控系統未運行', 'status': 'warning'})
    except Exception as e:
        logger.error(f"停止監控錯誤: {e}")
        return jsonify({'error': str(e)}), 500


@socketio.on('connect')
def handle_connect():
    """WebSocket 連接處理"""
    logger.info('WebSocket 客戶端已連接')
    if monitor:
        emit('status_update', monitor.get_current_status())


@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket 斷開處理"""
    logger.info('WebSocket 客戶端已斷開')


def broadcast_updates():
    """廣播更新數據"""
    while True:
        try:
            if monitor and monitor.is_running:
                status = monitor.get_current_status()
                socketio.emit('status_update', status)

                # 如果有新異常，發送警報
                if status.get('recent_anomalies'):
                    latest_anomaly = status['recent_anomalies'][-1]
                    if latest_anomaly.get('alert_level') in ['警告', '嚴重']:
                        socketio.emit('anomaly_alert', latest_anomaly)

            time.sleep(10)  # 每10秒廣播一次

        except Exception as e:
            logger.error(f"廣播更新錯誤: {e}")
            time.sleep(10)


def main():
    """主程式入口"""
    print("=== 智慧烘箱 AI 監控系統 ===")
    print("作者: AI Assistant")
    print("版本: 1.0.0")
    print("=" * 40)

    # 檢查必要檔案
    config_file = Path("plc_points.json")
    if not config_file.exists():
        logger.warning("PLC 配置檔案不存在，將使用預設配置")

    # 啟動廣播線程
    broadcast_thread = threading.Thread(target=broadcast_updates, daemon=True)
    broadcast_thread.start()

    try:
        # 自動啟動監控（可選）
        global monitor
        monitor = SmartOvenMonitor()
        monitor.start_monitoring(interval=30)

        logger.info("Web 服務器啟動中...")
        print("\n🌐 Web 界面地址: http://localhost:5000")
        print("📊 API 文檔: http://localhost:5000/api/status")
        print("🔧 控制面板: http://localhost:5000")
        print("\n按 Ctrl+C 停止服務")

        # 啟動 Flask 應用
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)

    except KeyboardInterrupt:
        logger.info("收到停止信號")
    except Exception as e:
        logger.error(f"系統錯誤: {e}")
    finally:
        if monitor:
            monitor.stop_monitoring()
        print("\n✅ 系統已安全關閉")


if __name__ == "__main__":
    main()
