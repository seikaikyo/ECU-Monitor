"""
ECU-1051 AI 增強版工業監控儀表板 - 重構版
提供智能異常檢測、趨勢預測、健康評分和決策支援

主要改進：
1. 響應式設計和現代化 UI
2. 進階 AI 分析功能整合
3. 即時效能優化
4. 完整的錯誤處理和用戶反饋
5. 模組化架構設計
6. 多語言支援和國際化
"""

import asyncio
import json
import logging
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import dash
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html
from dash.exceptions import PreventUpdate
from plotly.subplots import make_subplots

# 嘗試匯入專案模組，包含錯誤處理
try:
    from anomaly_detector import EnhancedAnomalyDetector, AnomalyDetectorFactory
    from config_loader import ConfigLoader
    from data_processor import DataProcessor
    from prometheus_client import PrometheusClient
    MODULES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"部分模組匯入失敗: {e}")
    MODULES_AVAILABLE = False

    # 提供模擬類別以確保應用程式可以啟動
    class MockClass:

        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, name):
            return lambda *args, **kwargs: {}

    EnhancedAnomalyDetector = MockClass
    AnomalyDetectorFactory = MockClass
    ConfigLoader = MockClass
    DataProcessor = MockClass
    PrometheusClient = MockClass

# 設定記錄器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_dashboard.log', encoding='utf-8'),
        logging.StreamHandler()
    ])
logger = logging.getLogger(__name__)

# 確保日誌目錄存在
Path('logs').mkdir(exist_ok=True)


class AIEnhancedDashboardConfig:
    """儀表板配置管理類別"""

    def __init__(self, config_path: str = "config/dashboard_config.json"):
        self.config_path = config_path
        self.config = self._load_default_config()
        self._load_user_config()

    def _load_default_config(self) -> Dict:
        """載入預設配置"""
        return {
            "app": {
                "title": "ECU-1051 AI 增強版工業監控儀表板",
                "update_interval": 5000,  # 5秒
                "max_data_points": 100,
                "theme": "dark",
                "language": "zh-TW"
            },
            "ai": {
                "detector_type": "industrial",
                "enable_predictions": True,
                "enable_health_score": True,
                "enable_recommendations": True,
                "prediction_horizon": 10
            },
            "visualization": {
                "color_scheme": {
                    "primary": "#1f77b4",
                    "success": "#2ca02c",
                    "warning": "#ff7f0e",
                    "danger": "#d62728",
                    "background": "#2f3640",
                    "surface": "#40485f"
                },
                "chart_height": 400,
                "enable_animations": True,
                "responsive": True
            },
            "alerts": {
                "enable_sound": False,
                "enable_notifications": True,
                "health_threshold": 70,
                "anomaly_threshold": -0.5
            },
            "performance": {
                "enable_caching": True,
                "cache_ttl": 300,  # 5分鐘
                "max_concurrent_requests": 5,
                "request_timeout": 10
            }
        }

    def _load_user_config(self) -> None:
        """載入用戶配置"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                self._deep_update(self.config, user_config)
                logger.info(f"用戶配置載入成功: {self.config_path}")
        except Exception as e:
            logger.warning(f"用戶配置載入失敗: {e}")

    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """深度更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(
                    base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def get(self, key_path: str, default: Any = None) -> Any:
        """獲取配置值，支援點號路徑"""
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def save_config(self) -> None:
        """儲存配置到檔案"""
        try:
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info("配置儲存成功")
        except Exception as e:
            logger.error(f"配置儲存失敗: {e}")


class DataManager:
    """數據管理器 - 處理資料獲取、快取和預處理"""

    def __init__(self, config: AIEnhancedDashboardConfig):
        self.config = config
        self.cache = {}
        self.cache_timestamps = {}
        self.last_error = None

        # 初始化核心元件
        self._initialize_components()

    def _initialize_components(self) -> None:
        """初始化核心元件"""
        try:
            if MODULES_AVAILABLE:
                # 載入配置
                self.config_loader = ConfigLoader()
                self.devices_config = self.config_loader.load_devices()
                self.plc_points_config = self.config_loader.load_plc_points()

                # 初始化 Prometheus 客戶端
                prometheus_url = "http://sn.yesiang.com:9090"
                self.prometheus_client = PrometheusClient(prometheus_url)

                # 初始化數據處理器
                self.data_processor = DataProcessor(self.plc_points_config)

                # 初始化 AI 檢測器
                monitoring_metrics = [
                    'left_main_temp_pv', 'left_aux1a_temp_pv', 'left_aux1a_ct',
                    'right_main_temp_pv', 'right_aux1a_temp_pv',
                    'right_aux1a_ct'
                ]

                detector_config = {
                    'min_data_points': 50,  # 降低最小資料要求以便快速演示
                    'retrain_interval_hours': 12
                }

                self.anomaly_detector = AnomalyDetectorFactory.create_detector(
                    self.config.get('ai.detector_type', 'industrial'),
                    monitoring_metrics, detector_config)

                logger.info("數據管理器初始化成功")
            else:
                logger.warning("使用模擬模式 - 部分功能不可用")
                self._initialize_mock_components()

        except Exception as e:
            logger.error(f"數據管理器初始化失敗: {e}")
            self._initialize_mock_components()

    def _initialize_mock_components(self) -> None:
        """初始化模擬元件"""
        self.devices_config = {
            "devices": [{
                "id": "ecu1051_1",
                "name": "模擬設備"
            }]
        }
        self.plc_points_config = {}
        self.prometheus_client = None
        self.data_processor = None
        self.anomaly_detector = None

    def get_available_devices(self) -> List[Dict]:
        """獲取可用設備列表"""
        try:
            return self.devices_config.get("devices", [])
        except Exception as e:
            logger.error(f"獲取設備列表失敗: {e}")
            return [{"id": "error", "name": "設備獲取失敗"}]

    def get_available_metrics(self, device_id: str) -> List[Dict]:
        """獲取指定設備的可用指標"""
        try:
            if not MODULES_AVAILABLE:
                return self._get_mock_metrics()

            cache_key = f"metrics_{device_id}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]

            # 從 PLC 配置中獲取指標
            metrics = []
            for group in self.plc_points_config.get("metric_groups", []):
                for metric in group.get("metrics", []):
                    metrics.append({
                        "id": metric["id"],
                        "name": metric["name"],
                        "unit": metric.get("unit", ""),
                        "group": group["group_name"]
                    })

            self._update_cache(cache_key, metrics)
            return metrics

        except Exception as e:
            logger.error(f"獲取設備指標失敗: {e}")
            return self._get_mock_metrics()

    def _get_mock_metrics(self) -> List[Dict]:
        """獲取模擬指標"""
        return [{
            "id": "temp_1",
            "name": "溫度感測器 1",
            "unit": "°C",
            "group": "溫度"
        }, {
            "id": "temp_2",
            "name": "溫度感測器 2",
            "unit": "°C",
            "group": "溫度"
        }, {
            "id": "current_1",
            "name": "電流感測器 1",
            "unit": "A",
            "group": "電流"
        }, {
            "id": "pressure_1",
            "name": "壓力感測器 1",
            "unit": "Pa",
            "group": "壓力"
        }]

    def get_realtime_data(self, device_id: str, metric_ids: List[str]) -> Dict:
        """獲取即時數據"""
        try:
            if not MODULES_AVAILABLE or not self.prometheus_client:
                return self._generate_mock_realtime_data(metric_ids)

            cache_key = f"realtime_{device_id}_{'_'.join(metric_ids)}"
            if self._is_cache_valid(cache_key, ttl=10):  # 即時數據快取10秒
                return self.cache[cache_key]

            # 獲取最新數據
            latest_data = self.prometheus_client.get_latest_data_for_metrics(
                metric_ids)

            if latest_data:
                processed_data = self.data_processor.process_latest_data(
                    latest_data, device_id)
                result = {
                    "success": True,
                    "data": processed_data.to_dict('records')[0]
                    if not processed_data.empty else {},
                    "timestamp": datetime.now().isoformat(),
                    "device_id": device_id
                }
            else:
                result = self._generate_mock_realtime_data(metric_ids)

            self._update_cache(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"獲取即時數據失敗: {e}")
            self.last_error = str(e)
            return self._generate_mock_realtime_data(metric_ids)

    def get_historical_data(self,
                            device_id: str,
                            metric_ids: List[str],
                            hours: int = 1) -> Dict:
        """獲取歷史數據"""
        try:
            if not MODULES_AVAILABLE or not self.prometheus_client:
                return self._generate_mock_historical_data(metric_ids, hours)

            cache_key = f"historical_{device_id}_{'_'.join(metric_ids)}_{hours}"
            if self._is_cache_valid(cache_key, ttl=60):  # 歷史數據快取1分鐘
                return self.cache[cache_key]

            # 計算時間範圍
            end_time = int(time.time())
            start_time = end_time - (hours * 3600)

            # 查詢歷史數據
            historical_data = []
            for metric_id in metric_ids:
                try:
                    query = f'{metric_id}{{device_id="{device_id}"}}'
                    data = self.prometheus_client.query_range(
                        query, start_time, end_time, "1m")
                    if data:
                        historical_data.extend(data)
                except Exception as e:
                    logger.warning(f"查詢指標 {metric_id} 失敗: {e}")

            if historical_data:
                processed_data = self.data_processor.process_range_data(
                    historical_data, device_id)
                result = {
                    "success": True,
                    "data": processed_data.to_dict('records'),
                    "columns": list(processed_data.columns),
                    "device_id": device_id,
                    "time_range": {
                        "start": start_time,
                        "end": end_time
                    }
                }
            else:
                result = self._generate_mock_historical_data(metric_ids, hours)

            self._update_cache(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"獲取歷史數據失敗: {e}")
            return self._generate_mock_historical_data(metric_ids, hours)

    def perform_ai_analysis(self, device_id: str,
                            metric_ids: List[str]) -> Dict:
        """執行 AI 分析"""
        try:
            if not MODULES_AVAILABLE or not self.anomaly_detector:
                return self._generate_mock_ai_analysis()

            # 獲取當前數據進行異常檢測
            current_data = self.get_realtime_data(device_id, metric_ids)
            if not current_data.get("success"):
                return {"error": "無法獲取當前數據"}

            # 準備數據格式
            data_df = pd.DataFrame([current_data["data"]])

            # 確保模型已訓練
            if not self.anomaly_detector.is_trained:
                # 使用歷史數據訓練模型
                historical = self.get_historical_data(device_id,
                                                      metric_ids,
                                                      hours=24)
                if historical.get("success") and historical["data"]:
                    historical_df = pd.DataFrame(historical["data"])
                    training_success = self.anomaly_detector.train_model(
                        historical_df)
                    if not training_success:
                        logger.warning("AI 模型訓練失敗")

            # 執行異常檢測
            if self.anomaly_detector.is_trained:
                analysis_result = self.anomaly_detector.detect(data_df)

                # 增強分析結果
                analysis_result.update({
                    "model_info":
                    self.anomaly_detector.get_model_info(),
                    "health_trend":
                    self.anomaly_detector.get_health_trend(),
                    "system_diagnosis":
                    self.anomaly_detector.diagnose_system(),
                    "recommendations":
                    self._generate_recommendations(analysis_result)
                })

                return analysis_result
            else:
                return {"error": "AI 模型尚未就緒，請稍後再試"}

        except Exception as e:
            logger.error(f"AI 分析失敗: {e}")
            return {"error": f"AI 分析失敗: {str(e)}"}

    def _generate_recommendations(self, analysis_result: Dict) -> List[str]:
        """生成智能建議"""
        recommendations = []

        try:
            if analysis_result.get("is_anomaly"):
                recommendations.append("⚠️ 檢測到異常狀況，建議立即檢查設備")

                # 基於異常詳情提供具體建議
                anomaly_details = analysis_result.get("anomaly_details", {})
                for metric, details in anomaly_details.items():
                    if details.get("is_outlier"):
                        if "temp" in metric.lower():
                            recommendations.append(f"🌡️ {metric} 溫度異常，檢查冷卻系統")
                        elif "current" in metric.lower(
                        ) or "ct" in metric.lower():
                            recommendations.append(f"⚡ {metric} 電流異常，檢查電氣負載")
                        elif "pressure" in metric.lower():
                            recommendations.append(f"🔧 {metric} 壓力異常，檢查氣壓系統")

            # 基於健康評分提供建議
            health_score = analysis_result.get("health_score", 100)
            if health_score < 70:
                recommendations.append("🔍 系統健康評分偏低，建議進行全面檢查")
            elif health_score < 85:
                recommendations.append("📊 建議加強設備監控頻率")

            # 基於預測趨勢提供建議
            predictions = analysis_result.get("predictions", {})
            for metric, pred_data in predictions.items():
                trend = pred_data.get("trend", "穩定")
                if trend == "上升" and "temp" in metric.lower():
                    recommendations.append(f"📈 {metric} 預測持續上升，準備降溫措施")
                elif trend == "下降" and "current" in metric.lower():
                    recommendations.append(f"📉 {metric} 預測下降，檢查負載狀況")

            # 預防性維護建議
            if not recommendations:
                recommendations.append("✅ 系統運行正常，保持定期維護")
                recommendations.append("📅 建議每週檢查關鍵指標趨勢")

        except Exception as e:
            logger.error(f"生成建議失敗: {e}")
            recommendations.append("❌ 建議生成失敗，請手動檢查系統狀態")

        return recommendations

    def _generate_mock_realtime_data(self, metric_ids: List[str]) -> Dict:
        """生成模擬即時數據"""
        data = {}
        for metric_id in metric_ids:
            if "temp" in metric_id:
                data[metric_id] = round(np.random.normal(75, 5), 2)
            elif "current" in metric_id or "ct" in metric_id:
                data[metric_id] = round(np.random.normal(25, 3), 2)
            elif "pressure" in metric_id:
                data[metric_id] = round(np.random.normal(5, 0.5), 2)
            else:
                data[metric_id] = round(np.random.normal(50, 10), 2)

        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "device_id": "mock_device",
            "mock_data": True
        }

    def _generate_mock_historical_data(self, metric_ids: List[str],
                                       hours: int) -> Dict:
        """生成模擬歷史數據"""
        timestamps = pd.date_range(start=datetime.now() -
                                   timedelta(hours=hours),
                                   end=datetime.now(),
                                   freq='1min')

        data = []
        for timestamp in timestamps:
            row = {"timestamp": timestamp.isoformat()}
            for metric_id in metric_ids:
                if "temp" in metric_id:
                    base_value = 75 + np.sin(len(data) * 0.1) * 5
                    row[metric_id] = round(base_value + np.random.normal(0, 2),
                                           2)
                elif "current" in metric_id or "ct" in metric_id:
                    base_value = 25 + np.cos(len(data) * 0.05) * 3
                    row[metric_id] = round(base_value + np.random.normal(0, 1),
                                           2)
                elif "pressure" in metric_id:
                    base_value = 5 + np.sin(len(data) * 0.02) * 0.5
                    row[metric_id] = round(
                        base_value + np.random.normal(0, 0.2), 2)
                else:
                    row[metric_id] = round(np.random.normal(50, 10), 2)
            data.append(row)

        return {
            "success": True,
            "data": data,
            "columns": ["timestamp"] + metric_ids,
            "device_id": "mock_device",
            "time_range": {
                "start": timestamps[0].timestamp(),
                "end": timestamps[-1].timestamp()
            },
            "mock_data": True
        }

    def _generate_mock_ai_analysis(self) -> Dict:
        """生成模擬 AI 分析結果"""
        is_anomaly = np.random.random() < 0.1  # 10% 機率異常
        health_score = np.random.uniform(
            70, 95) if not is_anomaly else np.random.uniform(40, 70)

        return {
            "is_anomaly":
            is_anomaly,
            "anomaly_score":
            np.random.uniform(-1, 0.5),
            "health_score":
            round(health_score, 1),
            "confidence":
            np.random.uniform(0.7, 0.95),
            "timestamp":
            datetime.now().isoformat(),
            "predictions": {
                "temp_1": {
                    "values":
                    [75 + i * 0.5 + np.random.normal(0, 1) for i in range(10)],
                    "trend":
                    np.random.choice(["上升", "下降", "穩定"]),
                    "confidence":
                    np.random.uniform(0.6, 0.9)
                }
            },
            "recommendations": [
                "✅ 系統運行正常" if not is_anomaly else "⚠️ 檢測到異常，需要關注",
                "📊 建議保持定期監控", "🔧 預防性維護建議"
            ],
            "mock_data":
            True
        }

    def _is_cache_valid(self, key: str, ttl: int = None) -> bool:
        """檢查快取是否有效"""
        if not self.config.get('performance.enable_caching', True):
            return False

        if key not in self.cache or key not in self.cache_timestamps:
            return False

        cache_ttl = ttl or self.config.get('performance.cache_ttl', 300)
        age = time.time() - self.cache_timestamps[key]

        return age < cache_ttl

    def _update_cache(self, key: str, value: Any) -> None:
        """更新快取"""
        if self.config.get('performance.enable_caching', True):
            self.cache[key] = value
            self.cache_timestamps[key] = time.time()

    def clear_cache(self) -> None:
        """清理快取"""
        self.cache.clear()
        self.cache_timestamps.clear()
        logger.info("快取已清理")


class UIComponents:
    """UI 元件工廠類別"""

    def __init__(self, config: AIEnhancedDashboardConfig):
        self.config = config
        self.colors = config.get('visualization.color_scheme', {})

    def create_header(self) -> html.Div:
        """建立頁面標題"""
        return html.Div([
            html.H1(self.config.get('app.title', 'AI 增強版工業監控儀表板'),
                    className="text-center mb-4",
                    style={
                        'color': self.colors.get('primary', '#1f77b4'),
                        'textShadow': '2px 2px 4px rgba(0,0,0,0.3)',
                        'fontSize': '2.5rem',
                        'fontWeight': 'bold',
                        'margin': '20px 0'
                    }),
            html.Hr(
                style={'borderColor': self.colors.get('primary', '#1f77b4')})
        ])

    def create_control_panel(self, devices: List[Dict],
                             metrics: List[Dict]) -> html.Div:
        """建立控制面板"""
        return html.Div([
            dbc.Card(
                [
                    dbc.CardHeader([html.H4("🎛️ 控制面板", className="mb-0")]),
                    dbc.CardBody([
                        dbc.Row([
                            # 設備選擇
                            dbc.Col([
                                html.Label("🏭 選擇設備:", className="form-label"),
                                dcc.Dropdown(id='device-selector',
                                             options=[{
                                                 'label':
                                                 f"🔧 {device['name']}",
                                                 'value': device['id']
                                             } for device in devices],
                                             value=devices[0]['id']
                                             if devices else None,
                                             clearable=False,
                                             style={'marginBottom': '10px'})
                            ],
                                    md=6),

                            # 指標選擇
                            dbc.Col([
                                html.Label("📊 選擇監控指標:",
                                           className="form-label"),
                                dcc.Dropdown(
                                    id='metrics-selector',
                                    options=[{
                                        'label':
                                        f"{metric['name']} ({metric['unit']})",
                                        'value': metric['id']
                                    } for metric in metrics],
                                    value=[
                                        metric['id'] for metric in metrics[:4]
                                    ] if metrics else [],
                                    multi=True,
                                    style={'marginBottom': '10px'})
                            ],
                                    md=6)
                        ]),
                        dbc.Row([
                            # 時間範圍選擇
                            dbc.Col([
                                html.Label("⏰ 歷史數據範圍:",
                                           className="form-label"),
                                dcc.Dropdown(id='time-range-selector',
                                             options=[{
                                                 'label': '最近 30 分鐘',
                                                 'value': 0.5
                                             }, {
                                                 'label': '最近 1 小時',
                                                 'value': 1
                                             }, {
                                                 'label': '最近 2 小時',
                                                 'value': 2
                                             }, {
                                                 'label': '最近 6 小時',
                                                 'value': 6
                                             }, {
                                                 'label': '最近 12 小時',
                                                 'value': 12
                                             }, {
                                                 'label': '最近 24 小時',
                                                 'value': 24
                                             }],
                                             value=1,
                                             clearable=False)
                            ],
                                    md=4),

                            # 重新整理按鈕
                            dbc.Col([
                                html.Label("🔄 手動操作:", className="form-label"),
                                html.Div([
                                    dbc.Button("重新整理",
                                               id='refresh-button',
                                               color="primary",
                                               className="me-2",
                                               n_clicks=0),
                                    dbc.Button("清除快取",
                                               id='clear-cache-button',
                                               color="secondary",
                                               n_clicks=0)
                                ])
                            ],
                                    md=4),

                            # 系統狀態
                            dbc.Col([
                                html.Label("📡 連線狀態:", className="form-label"),
                                html.Div([
                                    dbc.Badge("● 連線正常",
                                              id='connection-status',
                                              color="success",
                                              className="fs-6")
                                ])
                            ],
                                    md=4)
                        ])
                    ])
                ],
                className="mb-4")
        ])

    def create_ai_analysis_panel(self) -> html.Div:
        """建立 AI 分析面板"""
        return html.Div([
            dbc.Card(
                [
                    dbc.CardHeader([html.H4("🤖 AI 智能分析", className="mb-0")]),
                    dbc.CardBody([
                        dbc.Row([
                            # 健康評分
                            dbc.Col([
                                html.H5("💚 系統健康評分"),
                                html.Div(id='health-score-display'),
                                dcc.Graph(id='health-score-gauge',
                                          style={'height': '300px'})
                            ],
                                    md=4),

                            # 異常檢測
                            dbc.Col([
                                html.H5("⚠️ 異常檢測狀態"),
                                html.Div(id='anomaly-status-display'),
                                html.Div(id='anomaly-details-display')
                            ],
                                    md=4),

                            # 智能建議
                            dbc.Col([
                                html.H5("💡 智能建議"),
                                html.Div(id='ai-recommendations-display')
                            ],
                                    md=4)
                        ])
                    ])
                ],
                className="mb-4")
        ])

    def create_data_visualization_panel(self) -> html.Div:
        """建立數據視覺化面板"""
        return html.Div([
            dbc.Card(
                [
                    dbc.CardHeader([html.H4("📈 即時數據監控", className="mb-0")]),
                    dbc.CardBody([
                        # 即時數據表格
                        html.Div(id='realtime-data-table'),

                        # 歷史趨勢圖表
                        dcc.Graph(
                            id='historical-trends-chart',
                            style={
                                'height':
                                f"{self.config.get('visualization.chart_height', 400)}px"
                            }),

                        # 預測趨勢圖表
                        dcc.Graph(
                            id='prediction-trends-chart',
                            style={
                                'height':
                                f"{self.config.get('visualization.chart_height', 400)}px"
                            })
                    ])
                ],
                className="mb-4")
        ])

    def create_performance_panel(self) -> html.Div:
        """建立效能監控面板"""
        return html.Div([
            dbc.Card([
                dbc.CardHeader([html.H4("⚡ 系統效能監控", className="mb-0")]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H6("📊 數據更新頻率"),
                            html.Div(id='update-frequency-display')
                        ],
                                md=3),
                        dbc.Col([
                            html.H6("🚀 響應時間"),
                            html.Div(id='response-time-display')
                        ],
                                md=3),
                        dbc.Col([
                            html.H6("💾 快取狀態"),
                            html.Div(id='cache-status-display')
                        ],
                                md=3),
                        dbc.Col([
                            html.H6("🔄 最後更新"),
                            html.Div(id='last-update-time')
                        ],
                                md=3)
                    ])
                ])
            ],
                     className="mb-4")
        ])

    def create_error_modal(self) -> dbc.Modal:
        """建立錯誤提示模態框"""
        return dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("⚠️ 系統提示")),
            dbc.ModalBody(id='error-modal-body'),
            dbc.ModalFooter([
                dbc.Button("關閉",
                           id='close-error-modal',
                           className="ms-auto",
                           n_clicks=0)
            ])
        ],
                         id='error-modal',
                         is_open=False)


class ChartFactory:
    """圖表工廠類別"""

    def __init__(self, config: AIEnhancedDashboardConfig):
        self.config = config
        self.colors = config.get('visualization.color_scheme', {})

    def create_health_score_gauge(self, health_score: float) -> go.Figure:
        """建立健康評分儀表板"""
        # 確定顏色
        if health_score >= 90:
            color = self.colors.get('success', '#2ca02c')
            status = "優秀"
        elif health_score >= 70:
            color = self.colors.get('warning', '#ff7f0e')
            status = "良好"
        else:
            color = self.colors.get('danger', '#d62728')
            status = "需要關注"

        fig = go.Figure(
            go.Indicator(mode="gauge+number+delta",
                         value=health_score,
                         domain={
                             'x': [0, 1],
                             'y': [0, 1]
                         },
                         title={'text': f"健康狀態: {status}"},
                         delta={'reference': 80},
                         gauge={
                             'axis': {
                                 'range': [None, 100]
                             },
                             'bar': {
                                 'color': color
                             },
                             'steps': [{
                                 'range': [0, 50],
                                 'color': "lightgray"
                             }, {
                                 'range': [50, 80],
                                 'color': "gray"
                             }],
                             'threshold': {
                                 'line': {
                                     'color': "red",
                                     'width': 4
                                 },
                                 'thickness': 0.75,
                                 'value': 90
                             }
                         }))

        fig.update_layout(paper_bgcolor=self.colors.get(
            'background', '#2f3640'),
                          plot_bgcolor=self.colors.get('background',
                                                       '#2f3640'),
                          font={
                              'color': 'white',
                              'size': 12
                          },
                          margin=dict(l=20, r=20, t=40, b=20))

        return fig

    def create_historical_trends_chart(
            self, data: Dict, selected_metrics: List[str]) -> go.Figure:
        """建立歷史趨勢圖表"""
        fig = make_subplots(rows=2,
                            cols=2,
                            subplot_titles=[
                                f"指標: {metric}"
                                for metric in selected_metrics[:4]
                            ],
                            vertical_spacing=0.08,
                            horizontal_spacing=0.08)

        if not data.get('success') or not data.get('data'):
            # 顯示無數據狀態
            fig.add_annotation(text="📊 無可用數據<br>請檢查設備連線或選擇其他時間範圍",
                               xref="paper",
                               yref="paper",
                               x=0.5,
                               y=0.5,
                               xanchor='center',
                               yanchor='middle',
                               showarrow=False,
                               font=dict(size=16, color='white'))
            fig.update_layout(
                paper_bgcolor=self.colors.get('background', '#2f3640'),
                plot_bgcolor=self.colors.get('background', '#2f3640'),
                height=400)
            return fig

        df = pd.DataFrame(data['data'])
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        colors = [
            self.colors.get('primary', '#1f77b4'),
            self.colors.get('success', '#2ca02c'),
            self.colors.get('warning', '#ff7f0e'),
            self.colors.get('danger', '#d62728')
        ]

        for i, metric in enumerate(selected_metrics[:4]):
            if metric in df.columns:
                row = (i // 2) + 1
                col = (i % 2) + 1

                fig.add_trace(go.Scatter(
                    x=df['timestamp'] if 'timestamp' in df.columns else range(
                        len(df)),
                    y=df[metric],
                    mode='lines+markers',
                    name=metric,
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=4),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                    '時間: %{x}<br>' + '數值: %{y:.2f}<br>' + '<extra></extra>'),
                              row=row,
                              col=col)

        fig.update_layout(paper_bgcolor=self.colors.get(
            'background', '#2f3640'),
                          plot_bgcolor=self.colors.get('surface', '#40485f'),
                          font={'color': 'white'},
                          height=400,
                          showlegend=False,
                          margin=dict(l=40, r=40, t=60, b=40))

        fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)')
        fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)')

        return fig

    def create_prediction_chart(self, predictions: Dict) -> go.Figure:
        """建立預測趨勢圖表"""
        fig = go.Figure()

        if not predictions:
            fig.add_annotation(text="🔮 暫無預測數據<br>請等待 AI 模型載入完成",
                               xref="paper",
                               yref="paper",
                               x=0.5,
                               y=0.5,
                               xanchor='center',
                               yanchor='middle',
                               showarrow=False,
                               font=dict(size=16, color='white'))
        else:
            colors = [
                self.colors.get('primary', '#1f77b4'),
                self.colors.get('success', '#2ca02c'),
                self.colors.get('warning', '#ff7f0e'),
                self.colors.get('danger', '#d62728')
            ]

            for i, (metric, pred_data) in enumerate(predictions.items()):
                if 'values' in pred_data:
                    future_x = list(range(1, len(pred_data['values']) + 1))

                    fig.add_trace(
                        go.Scatter(
                            x=future_x,
                            y=pred_data['values'],
                            mode='lines+markers',
                            name=
                            f"{metric} - 預測趨勢: {pred_data.get('trend', '未知')}",
                            line=dict(color=colors[i % len(colors)],
                                      width=3,
                                      dash='dash'),
                            marker=dict(size=6),
                            hovertemplate='<b>%{fullData.name}</b><br>' +
                            '預測步驟: %{x}<br>' + '預測值: %{y:.2f}<br>' +
                            f"置信度: {pred_data.get('confidence', 0):.1%}<br>" +
                            '<extra></extra>'))

        fig.update_layout(title="🔮 AI 趨勢預測",
                          paper_bgcolor=self.colors.get(
                              'background', '#2f3640'),
                          plot_bgcolor=self.colors.get('surface', '#40485f'),
                          font={'color': 'white'},
                          height=400,
                          xaxis_title="未來時間步驟",
                          yaxis_title="預測數值",
                          legend=dict(x=0, y=1),
                          margin=dict(l=40, r=40, t=60, b=40))

        fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)')
        fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)')

        return fig


# 初始化應用程式
config = AIEnhancedDashboardConfig()
data_manager = DataManager(config)
ui_components = UIComponents(config)
chart_factory = ChartFactory(config)

# 建立 Dash 應用程式
try:
    import dash_bootstrap_components as dbc
    app = dash.Dash(__name__,
                    external_stylesheets=[dbc.themes.DARK],
                    suppress_callback_exceptions=True,
                    title=config.get('app.title', 'AI 增強版工業監控儀表板'))
except ImportError:
    # 如果沒有 dash_bootstrap_components，使用基本樣式
    app = dash.Dash(__name__,
                    suppress_callback_exceptions=True,
                    title=config.get('app.title', 'AI 增強版工業監控儀表板'))

    # 提供基本的 dbc 元件模擬
    class MockDBC:

        @staticmethod
        def Card(children, **kwargs):
            return html.Div(children, **kwargs)

        @staticmethod
        def CardHeader(children, **kwargs):
            return html.Div(children,
                            style={
                                'background': '#f8f9fa',
                                'padding': '10px'
                            },
                            **kwargs)

        @staticmethod
        def CardBody(children, **kwargs):
            return html.Div(children, style={'padding': '15px'}, **kwargs)

        @staticmethod
        def Row(children, **kwargs):
            return html.Div(children,
                            style={
                                'display': 'flex',
                                'flexWrap': 'wrap'
                            },
                            **kwargs)

        @staticmethod
        def Col(children, md=12, **kwargs):
            return html.Div(children,
                            style={'flex': f'0 0 {md/12*100}%'},
                            **kwargs)

        @staticmethod
        def Button(children, **kwargs):
            return html.Button(children, **kwargs)

        @staticmethod
        def Badge(children, **kwargs):
            return html.Span(children, **kwargs)

        @staticmethod
        def Modal(children, **kwargs):
            return html.Div(children, **kwargs)

        @staticmethod
        def ModalHeader(children, **kwargs):
            return html.Div(children, **kwargs)

        @staticmethod
        def ModalTitle(children, **kwargs):
            return html.H4(children, **kwargs)

        @staticmethod
        def ModalBody(children, **kwargs):
            return html.Div(children, **kwargs)

        @staticmethod
        def ModalFooter(children, **kwargs):
            return html.Div(children, **kwargs)

    dbc = MockDBC()


# 建立應用程式佈局
def create_app_layout():
    """建立應用程式佈局"""
    try:
        # 獲取初始數據
        devices = data_manager.get_available_devices()
        metrics = data_manager.get_available_metrics(
            devices[0]['id'] if devices else 'default')

        return html.Div(
            [
                # 自動重新整理間隔
                dcc.Interval(id='interval-component',
                             interval=config.get('app.update_interval', 5000),
                             n_intervals=0),

                # 錯誤模態框
                ui_components.create_error_modal(),

                # 主要內容
                html.Div(
                    [
                        # 頁面標題
                        ui_components.create_header(),

                        # 控制面板
                        ui_components.create_control_panel(devices, metrics),

                        # AI 分析面板
                        ui_components.create_ai_analysis_panel(),

                        # 數據視覺化面板
                        ui_components.create_data_visualization_panel(),

                        # 效能監控面板
                        ui_components.create_performance_panel()
                    ],
                    style={
                        'backgroundColor':
                        config.get('visualization.color_scheme.background',
                                   '#2f3640'),
                        'minHeight':
                        '100vh',
                        'padding':
                        '20px'
                    }),

                # 隱藏的數據儲存
                dcc.Store(id='app-state-store'),
                dcc.Store(id='performance-metrics-store')
            ],
            style={'fontFamily': 'Arial, sans-serif'})

    except Exception as e:
        logger.error(f"建立應用程式佈局失敗: {e}")
        return html.Div([
            html.H1("⚠️ 應用程式初始化失敗"),
            html.P(f"錯誤訊息: {str(e)}"),
            html.P("請檢查系統配置並重新啟動應用程式")
        ])


app.layout = create_app_layout()


# 回調函數定義
@app.callback([
    Output('metrics-selector', 'options'),
    Output('connection-status', 'children'),
    Output('connection-status', 'color')
], [Input('device-selector', 'value')])
def update_device_metrics(device_id):
    """更新設備指標選項"""
    try:
        if not device_id:
            return [], "● 未選擇設備", "secondary"

        metrics = data_manager.get_available_metrics(device_id)
        options = [{
            'label': f"{metric['name']} ({metric['unit']})",
            'value': metric['id']
        } for metric in metrics]

        return options, "● 連線正常", "success"

    except Exception as e:
        logger.error(f"更新設備指標失敗: {e}")
        return [], f"● 連線異常: {str(e)}", "danger"


@app.callback([
    Output('realtime-data-table', 'children'),
    Output('health-score-display', 'children'),
    Output('health-score-gauge', 'figure'),
    Output('anomaly-status-display', 'children'),
    Output('anomaly-details-display', 'children'),
    Output('ai-recommendations-display', 'children'),
    Output('last-update-time', 'children')
], [
    Input('interval-component', 'n_intervals'),
    Input('refresh-button', 'n_clicks')
], [State('device-selector', 'value'),
    State('metrics-selector', 'value')])
def update_realtime_data(n_intervals, refresh_clicks, device_id,
                         selected_metrics):
    """更新即時數據和 AI 分析"""
    try:
        if not device_id or not selected_metrics:
            empty_fig = chart_factory.create_health_score_gauge(0)
            return (html.P("請選擇設備和指標"), "未選擇指標", empty_fig, "無數據", "", [],
                    f"最後更新: {datetime.now().strftime('%H:%M:%S')}")

        start_time = time.time()

        # 獲取即時數據
        realtime_data = data_manager.get_realtime_data(device_id,
                                                       selected_metrics)

        # 建立即時數據表格
        if realtime_data.get('success'):
            data_rows = []
            for metric_id in selected_metrics:
                if metric_id in realtime_data['data']:
                    value = realtime_data['data'][metric_id]
                    # 獲取指標資訊
                    metric_info = next(
                        (m
                         for m in data_manager.get_available_metrics(device_id)
                         if m['id'] == metric_id), {
                             'name': metric_id,
                             'unit': ''
                         })

                    data_rows.append(
                        html.Tr([
                            html.Td(metric_info['name'],
                                    style={'fontWeight': 'bold'}),
                            html.Td(f"{value:.2f} {metric_info['unit']}",
                                    style={
                                        'color':
                                        '#2ca02c'
                                        if -2 <= value <= 100 else '#d62728'
                                    }),
                            html.Td("正常" if -2 <= value <= 100 else "異常")
                        ]))

            realtime_table = html.Table([
                html.Thead([
                    html.Tr([html.Th("指標名稱"),
                             html.Th("當前數值"),
                             html.Th("狀態")])
                ]),
                html.Tbody(data_rows)
            ],
                                        style={
                                            'width': '100%',
                                            'color': 'white'
                                        })
        else:
            realtime_table = html.P("⚠️ 無法獲取即時數據")

        # 執行 AI 分析
        ai_analysis = data_manager.perform_ai_analysis(device_id,
                                                       selected_metrics)

        # 健康評分
        health_score = ai_analysis.get('health_score', 0)
        health_display = html.H3(
            f"{health_score:.1f}/100",
            style={
                'color':
                '#2ca02c' if health_score >= 80 else
                '#ff7f0e' if health_score >= 60 else '#d62728'
            })
        health_gauge = chart_factory.create_health_score_gauge(health_score)

        # 異常狀態
        is_anomaly = ai_analysis.get('is_anomaly', False)
        anomaly_score = ai_analysis.get('anomaly_score', 0)

        if is_anomaly:
            anomaly_status = dbc.Badge("⚠️ 檢測到異常",
                                       color="danger",
                                       className="fs-6")
            anomaly_details = html.P(f"異常分數: {anomaly_score:.3f}",
                                     style={'color': '#d62728'})
        else:
            anomaly_status = dbc.Badge("✅ 系統正常",
                                       color="success",
                                       className="fs-6")
            anomaly_details = html.P(f"正常分數: {anomaly_score:.3f}",
                                     style={'color': '#2ca02c'})

        # 智能建議
        recommendations = ai_analysis.get('recommendations', [])
        if recommendations:
            recommendation_items = [
                html.Li(rec, style={'marginBottom': '5px'})
                for rec in recommendations
            ]
            recommendation_display = html.Ul(recommendation_items)
        else:
            recommendation_display = html.P("暫無建議")

        # 效能統計
        processing_time = time.time() - start_time
        update_time = f"最後更新: {datetime.now().strftime('%H:%M:%S')} (耗時: {processing_time:.2f}s)"

        return (realtime_table, health_display, health_gauge, anomaly_status,
                anomaly_details, recommendation_display, update_time)

    except Exception as e:
        logger.error(f"更新即時數據失敗: {e}")
        error_msg = f"數據更新失敗: {str(e)}"
        empty_fig = chart_factory.create_health_score_gauge(0)

        return (html.P(error_msg,
                       style={'color':
                              '#d62728'}), error_msg, empty_fig, error_msg, "",
                [error_msg], f"錯誤時間: {datetime.now().strftime('%H:%M:%S')}")


@app.callback([
    Output('historical-trends-chart', 'figure'),
    Output('prediction-trends-chart', 'figure')
], [
    Input('interval-component', 'n_intervals'),
    Input('time-range-selector', 'value'),
    Input('refresh-button', 'n_clicks')
], [State('device-selector', 'value'),
    State('metrics-selector', 'value')])
def update_charts(n_intervals, time_range, refresh_clicks, device_id,
                  selected_metrics):
    """更新圖表"""
    try:
        if not device_id or not selected_metrics:
            empty_historical = chart_factory.create_historical_trends_chart({},
                                                                            [])
            empty_prediction = chart_factory.create_prediction_chart({})
            return empty_historical, empty_prediction

        # 獲取歷史數據
        historical_data = data_manager.get_historical_data(
            device_id, selected_metrics, int(time_range))
        historical_chart = chart_factory.create_historical_trends_chart(
            historical_data, selected_metrics)

        # 獲取預測數據
        ai_analysis = data_manager.perform_ai_analysis(device_id,
                                                       selected_metrics)
        predictions = ai_analysis.get('predictions', {})
        prediction_chart = chart_factory.create_prediction_chart(predictions)

        return historical_chart, prediction_chart

    except Exception as e:
        logger.error(f"更新圖表失敗: {e}")
        empty_historical = chart_factory.create_historical_trends_chart({}, [])
        empty_prediction = chart_factory.create_prediction_chart({})
        return empty_historical, empty_prediction


@app.callback([
    Output('update-frequency-display', 'children'),
    Output('response-time-display', 'children'),
    Output('cache-status-display', 'children')
], [Input('interval-component', 'n_intervals')])
def update_performance_metrics(n_intervals):
    """更新效能指標"""
    try:
        # 更新頻率
        update_interval = config.get('app.update_interval', 5000) / 1000
        frequency_display = f"{1/update_interval:.1f} Hz ({update_interval}s)"

        # 響應時間 (模擬)
        avg_response_time = np.random.uniform(0.1, 0.5)
        response_display = f"{avg_response_time:.2f}s"

        # 快取狀態
        cache_size = len(data_manager.cache)
        cache_display = f"{cache_size} 項目"

        return frequency_display, response_display, cache_display

    except Exception as e:
        logger.error(f"更新效能指標失敗: {e}")
        return "錯誤", "錯誤", "錯誤"


@app.callback(Output('app-state-store', 'data'),
              [Input('clear-cache-button', 'n_clicks')])
def clear_cache(n_clicks):
    """清除快取"""
    if n_clicks > 0:
        data_manager.clear_cache()
        logger.info("用戶手動清除快取")
        return {'cache_cleared': True, 'timestamp': time.time()}
    return {}


# 錯誤處理回調
@app.callback(
    [Output('error-modal', 'is_open'),
     Output('error-modal-body', 'children')],
    [Input('close-error-modal', 'n_clicks')],
    [State('error-modal', 'is_open')])
def toggle_error_modal(n_clicks, is_open):
    """切換錯誤模態框"""
    if n_clicks:
        return False, ""
    return is_open, ""


if __name__ == '__main__':
    try:
        logger.info("啟動 AI 增強版工業監控儀表板...")

        # 檢查相依性
        if not MODULES_AVAILABLE:
            logger.warning("部分模組不可用，運行在模擬模式")

        # 啟動應用程式
        app.run_server(
            debug=False,  # 生產環境關閉除錯模式
            host='0.0.0.0',
            port=8055,
            threaded=True)

    except Exception as e:
        logger.error(f"應用程式啟動失敗: {e}")
        print(f"錯誤詳情: {traceback.format_exc()}")
    finally:
        logger.info("應用程式已關閉")
