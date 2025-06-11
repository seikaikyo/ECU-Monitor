"""
ECU-1051 工業設備異常檢測模組 - 增強版
提供多層次異常檢測、趨勢預測和健康評分功能

主要改進：
1. 多演算法融合異常檢測
2. 即時異常檢測和批次訓練分離
3. 記憶體優化和效能提升
4. 完整的錯誤處理和記錄
5. 配置驅動的參數調整
6. 健康評分和趨勢預測整合
"""

import logging
import pickle
import time
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.covariance import EllipticEnvelope
import joblib

# 忽略 sklearn 的未來警告
warnings.filterwarnings('ignore', category=FutureWarning)

# 設定記錄器
logger = logging.getLogger(__name__)


class EnhancedAnomalyDetector:
    """
    增強版異常檢測器
    
    功能特點：
    - 多演算法融合檢測 (Isolation Forest + Elliptic Envelope)
    - 即時異常檢測和離線訓練分離
    - 自適應閾值調整
    - 趨勢預測和健康評分
    - 效能優化和記憶體管理
    """

    def __init__(self,
                 metrics_to_monitor: List[str],
                 config: Optional[Dict] = None,
                 model_path: Optional[str] = None):
        """
        初始化異常檢測器
        
        Args:
            metrics_to_monitor: 要監控的指標列表
            config: 配置參數字典
            model_path: 模型儲存路徑
        """
        self.metrics_to_monitor = metrics_to_monitor
        self.model_path = model_path or "models/anomaly_models"

        # 預設配置
        self.default_config = {
            'isolation_forest': {
                'contamination': 0.01,
                'n_estimators': 200,
                'max_samples': 'auto',
                'random_state': 42,
                'n_jobs': -1
            },
            'elliptic_envelope': {
                'contamination': 0.01,
                'random_state': 42
            },
            'scaler_type': 'robust',  # 'standard' or 'robust'
            'min_data_points': 100,
            'retrain_interval_hours': 24,
            'prediction_points': 10,
            'health_weights': {
                'temperature': 0.4,
                'current': 0.3,
                'pressure': 0.2,
                'other': 0.1
            },
            'anomaly_threshold': -0.5,
            'cache_size': 1000
        }

        # 合併用戶配置
        self.config = self.default_config.copy()
        if config:
            self._deep_update_dict(self.config, config)

        # 初始化模型和變數
        self.isolation_forest = None
        self.elliptic_envelope = None
        self.trend_predictor = None
        self.scaler = None
        self.is_trained = False
        self.last_train_time = None
        self.training_data_cache = pd.DataFrame()
        self.health_score_history = []

        # 效能監控
        self.detection_times = []
        self.training_times = []

        # 建立模型目錄
        Path(self.model_path).mkdir(parents=True, exist_ok=True)

        # 嘗試載入現有模型
        self._load_models()

        logger.info(f"異常檢測器初始化完成，監控指標: {metrics_to_monitor}")

    def _deep_update_dict(self, base_dict: Dict, update_dict: Dict) -> None:
        """
        深度更新字典
        
        Args:
            base_dict: 基礎字典
            update_dict: 更新字典
        """
        for key, value in update_dict.items():
            if key in base_dict and isinstance(
                    base_dict[key], dict) and isinstance(value, dict):
                self._deep_update_dict(base_dict[key], value)
            else:
                base_dict[key] = value

    def _create_scaler(self) -> Union[StandardScaler, RobustScaler]:
        """
        建立資料標準化器
        
        Returns:
            標準化器實例
        """
        try:
            if self.config['scaler_type'] == 'robust':
                return RobustScaler()
            else:
                return StandardScaler()
        except Exception as e:
            logger.warning(f"建立標準化器失敗，使用預設: {e}")
            return RobustScaler()

    def _validate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        驗證和清理輸入資料
        
        Args:
            data: 輸入資料
            
        Returns:
            清理後的資料
            
        Raises:
            ValueError: 資料驗證失敗時
        """
        if data is None or data.empty:
            raise ValueError("輸入資料為空")

        # 檢查必要的欄位
        missing_metrics = set(self.metrics_to_monitor) - set(data.columns)
        if missing_metrics:
            logger.warning(f"缺少監控指標: {missing_metrics}")

        # 過濾出存在的監控指標
        available_metrics = [
            m for m in self.metrics_to_monitor if m in data.columns
        ]
        if not available_metrics:
            raise ValueError("沒有可用的監控指標")

        # 選擇相關欄位
        data_cleaned = data[available_metrics].copy()

        # 處理無效值
        data_cleaned = data_cleaned.replace([np.inf, -np.inf], np.nan)
        initial_rows = len(data_cleaned)
        data_cleaned = data_cleaned.dropna()

        if len(data_cleaned) < initial_rows * 0.8:
            logger.warning(
                f"清理後資料減少 {(initial_rows - len(data_cleaned)) / initial_rows * 100:.1f}%"
            )

        if data_cleaned.empty:
            raise ValueError("清理後資料為空")

        return data_cleaned

    def train_model(self,
                    historical_data: pd.DataFrame,
                    force_retrain: bool = False) -> bool:
        """
        訓練異常檢測模型
        
        Args:
            historical_data: 歷史資料
            force_retrain: 是否強制重新訓練
            
        Returns:
            訓練是否成功
        """
        start_time = time.time()

        try:
            # 檢查是否需要重新訓練
            if not force_retrain and self._should_skip_training():
                logger.info("模型訓練間隔未到，跳過訓練")
                return True

            logger.info("開始訓練異常檢測模型...")

            # 驗證資料
            training_data = self._validate_data(historical_data)

            if len(training_data) < self.config['min_data_points']:
                logger.warning(
                    f"訓練資料不足: {len(training_data)} < {self.config['min_data_points']}"
                )
                return False

            # 資料預處理
            self.scaler = self._create_scaler()
            scaled_data = self.scaler.fit_transform(training_data)

            # 訓練 Isolation Forest
            self.isolation_forest = IsolationForest(
                **self.config['isolation_forest'])
            self.isolation_forest.fit(scaled_data)

            # 訓練 Elliptic Envelope
            try:
                self.elliptic_envelope = EllipticEnvelope(
                    **self.config['elliptic_envelope'])
                self.elliptic_envelope.fit(scaled_data)
            except Exception as e:
                logger.warning(f"Elliptic Envelope 訓練失敗: {e}")
                self.elliptic_envelope = None

            # 訓練趨勢預測模型
            self._train_trend_predictor(training_data)

            # 更新狀態
            self.is_trained = True
            self.last_train_time = datetime.now()
            self.training_data_cache = training_data.tail(
                self.config['cache_size'])

            # 儲存模型
            self._save_models()

            # 記錄效能
            training_time = time.time() - start_time
            self.training_times.append(training_time)

            logger.info(
                f"模型訓練完成，耗時: {training_time:.2f}秒，資料量: {len(training_data)}")
            return True

        except Exception as e:
            logger.error(f"模型訓練失敗: {e}")
            return False

    def _should_skip_training(self) -> bool:
        """
        檢查是否應跳過訓練
        
        Returns:
            是否跳過訓練
        """
        if not self.is_trained or self.last_train_time is None:
            return False

        time_since_last_train = datetime.now() - self.last_train_time
        retrain_interval = timedelta(
            hours=self.config['retrain_interval_hours'])

        return time_since_last_train < retrain_interval

    def _train_trend_predictor(self, data: pd.DataFrame) -> None:
        """
        訓練趨勢預測模型
        
        Args:
            data: 訓練資料
        """
        try:
            if len(data) < 20:  # 需要足夠的資料點
                logger.warning("趨勢預測訓練資料不足")
                return

            # 為每個指標建立時間序列特徵
            X_features = []
            y_targets = []

            for metric in self.metrics_to_monitor:
                if metric not in data.columns:
                    continue

                values = data[metric].values

                # 建立滑動窗口特徵 (使用過去5個點預測下一個點)
                window_size = 5
                for i in range(window_size, len(values)):
                    X_features.append(values[i - window_size:i])
                    y_targets.append(values[i])

            if not X_features:
                logger.warning("無法建立趨勢預測特徵")
                return

            X = np.array(X_features)
            y = np.array(y_targets)

            # 分割訓練和測試資料
            if len(X) > 10:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42)
            else:
                X_train, y_train = X, y
                X_test, y_test = X, y

            # 訓練線性回歸模型
            self.trend_predictor = LinearRegression()
            self.trend_predictor.fit(X_train, y_train)

            # 評估模型
            if len(X_test) > 0:
                y_pred = self.trend_predictor.predict(X_test)
                mse = mean_squared_error(y_test, y_pred)
                logger.info(f"趨勢預測模型 MSE: {mse:.4f}")

        except Exception as e:
            logger.warning(f"趨勢預測模型訓練失敗: {e}")
            self.trend_predictor = None

    def detect(self, current_data: pd.DataFrame) -> Dict:
        """
        執行即時異常檢測
        
        Args:
            current_data: 當前資料
            
        Returns:
            檢測結果字典
        """
        start_time = time.time()

        result = {
            'is_anomaly': False,
            'anomaly_score': 0.0,
            'anomaly_details': {},
            'health_score': 100.0,
            'predictions': {},
            'timestamp': datetime.now().isoformat(),
            'metrics_status': {},
            'confidence': 0.0
        }

        try:
            if not self.is_trained:
                result['error'] = "模型尚未訓練"
                logger.warning("嘗試使用未訓練的模型進行檢測")
                return result

            # 驗證資料
            data_cleaned = self._validate_data(current_data)

            # 資料標準化
            scaled_data = self.scaler.transform(data_cleaned)

            # 執行多演算法檢測
            anomaly_scores = self._multi_algorithm_detection(scaled_data)

            # 融合檢測結果
            final_score = self._fusion_anomaly_scores(anomaly_scores)
            result['anomaly_score'] = final_score
            result['is_anomaly'] = final_score < self.config[
                'anomaly_threshold']

            # 計算置信度
            result['confidence'] = self._calculate_confidence(anomaly_scores)

            # 個別指標異常詳情
            result['anomaly_details'] = self._analyze_individual_metrics(
                data_cleaned, scaled_data)

            # 計算健康評分
            result['health_score'] = self._calculate_health_score(
                data_cleaned, result['is_anomaly'], final_score)

            # 趨勢預測
            if self.trend_predictor is not None:
                result['predictions'] = self._predict_trends(data_cleaned)

            # 指標狀態評估
            result['metrics_status'] = self._evaluate_metrics_status(
                data_cleaned)

            # 記錄效能
            detection_time = time.time() - start_time
            self.detection_times.append(detection_time)

            # 清理效能記錄 (保留最近100次)
            if len(self.detection_times) > 100:
                self.detection_times = self.detection_times[-100:]

            logger.debug(f"異常檢測完成，耗時: {detection_time:.4f}秒")

        except Exception as e:
            logger.error(f"異常檢測失敗: {e}")
            result['error'] = str(e)

        return result

    def _multi_algorithm_detection(
            self, scaled_data: np.ndarray) -> Dict[str, float]:
        """
        多演算法異常檢測
        
        Args:
            scaled_data: 標準化後的資料
            
        Returns:
            各演算法的異常分數
        """
        scores = {}

        # Isolation Forest 檢測
        if self.isolation_forest is not None:
            try:
                if_score = self.isolation_forest.decision_function(
                    scaled_data)[0]
                scores['isolation_forest'] = if_score
            except Exception as e:
                logger.warning(f"Isolation Forest 檢測失敗: {e}")

        # Elliptic Envelope 檢測
        if self.elliptic_envelope is not None:
            try:
                ee_score = self.elliptic_envelope.decision_function(
                    scaled_data)[0]
                scores['elliptic_envelope'] = ee_score
            except Exception as e:
                logger.warning(f"Elliptic Envelope 檢測失敗: {e}")

        return scores

    def _fusion_anomaly_scores(self, scores: Dict[str, float]) -> float:
        """
        融合多個異常分數
        
        Args:
            scores: 各演算法分數
            
        Returns:
            融合後的分數
        """
        if not scores:
            return 0.0

        # 加權平均 (Isolation Forest 權重較高)
        weights = {'isolation_forest': 0.7, 'elliptic_envelope': 0.3}

        weighted_score = 0.0
        total_weight = 0.0

        for algo, score in scores.items():
            if algo in weights:
                weighted_score += score * weights[algo]
                total_weight += weights[algo]

        return weighted_score / total_weight if total_weight > 0 else 0.0

    def _calculate_confidence(self, scores: Dict[str, float]) -> float:
        """
        計算檢測置信度
        
        Args:
            scores: 各演算法分數
            
        Returns:
            置信度 (0-1)
        """
        if not scores:
            return 0.0

        # 如果多個演算法結果一致，置信度較高
        score_values = list(scores.values())
        if len(score_values) == 1:
            return 0.8  # 單一演算法中等置信度

        # 計算分數的標準差，標準差越小表示一致性越高
        std = np.std(score_values)
        confidence = max(0.0, min(1.0, 1.0 - std))

        return confidence

    def _analyze_individual_metrics(
            self, data: pd.DataFrame,
            scaled_data: np.ndarray) -> Dict[str, Dict]:
        """
        分析個別指標的異常情況
        
        Args:
            data: 原始資料
            scaled_data: 標準化資料
            
        Returns:
            個別指標分析結果
        """
        details = {}

        for i, metric in enumerate(data.columns):
            if i >= scaled_data.shape[1]:
                continue

            value = data.iloc[0, i]
            scaled_value = scaled_data[0, i]

            # 基於歷史資料計算統計資訊
            metric_details = {
                'current_value': value,
                'scaled_value': scaled_value,
                'is_outlier': abs(scaled_value) > 2.0,  # 超過2個標準差
                'severity': self._calculate_severity(scaled_value),
                'status': self._get_metric_status(scaled_value)
            }

            details[metric] = metric_details

        return details

    def _calculate_severity(self, scaled_value: float) -> str:
        """
        計算異常嚴重程度
        
        Args:
            scaled_value: 標準化值
            
        Returns:
            嚴重程度等級
        """
        abs_value = abs(scaled_value)

        if abs_value > 3.0:
            return "嚴重"
        elif abs_value > 2.0:
            return "中等"
        elif abs_value > 1.0:
            return "輕微"
        else:
            return "正常"

    def _get_metric_status(self, scaled_value: float) -> str:
        """
        獲取指標狀態
        
        Args:
            scaled_value: 標準化值
            
        Returns:
            狀態描述
        """
        if scaled_value > 2.0:
            return "偏高"
        elif scaled_value < -2.0:
            return "偏低"
        else:
            return "正常"

    def _calculate_health_score(self, data: pd.DataFrame, is_anomaly: bool,
                                anomaly_score: float) -> float:
        """
        計算系統健康評分
        
        Args:
            data: 當前資料
            is_anomaly: 是否異常
            anomaly_score: 異常分數
            
        Returns:
            健康評分 (0-100)
        """
        base_score = 100.0

        # 異常懲罰
        if is_anomaly:
            penalty = min(30.0, abs(anomaly_score) * 20)
            base_score -= penalty

        # 個別指標評估
        weights = self.config['health_weights']

        for metric in data.columns:
            metric_type = self._classify_metric_type(metric)
            weight = weights.get(metric_type, weights['other'])

            value = data.iloc[0][metric]

            # 基於指標類型的健康評估
            metric_penalty = self._calculate_metric_penalty(
                metric, value, metric_type)
            base_score -= metric_penalty * weight * 100

        # 限制評分範圍
        health_score = max(0.0, min(100.0, base_score))

        # 記錄歷史評分
        self.health_score_history.append(health_score)
        if len(self.health_score_history) > 100:
            self.health_score_history = self.health_score_history[-100:]

        return health_score

    def _classify_metric_type(self, metric_name: str) -> str:
        """
        分類指標類型
        
        Args:
            metric_name: 指標名稱
            
        Returns:
            指標類型
        """
        metric_lower = metric_name.lower()

        if 'temp' in metric_lower or '溫度' in metric_name:
            return 'temperature'
        elif 'current' in metric_lower or 'ct' in metric_lower or '電流' in metric_name:
            return 'current'
        elif 'pressure' in metric_lower or '壓力' in metric_name:
            return 'pressure'
        else:
            return 'other'

    def _calculate_metric_penalty(self, metric_name: str, value: float,
                                  metric_type: str) -> float:
        """
        計算指標懲罰分數
        
        Args:
            metric_name: 指標名稱
            value: 指標值
            metric_type: 指標類型
            
        Returns:
            懲罰分數 (0-1)
        """
        # 根據指標類型設定閾值
        thresholds = {
            'temperature': {
                'min': 0,
                'max': 100,
                'warning': 80
            },
            'current': {
                'min': 0,
                'max': 50,
                'warning': 40
            },
            'pressure': {
                'min': 0,
                'max': 10,
                'warning': 8
            },
            'other': {
                'min': -1000,
                'max': 1000,
                'warning': 800
            }
        }

        threshold = thresholds.get(metric_type, thresholds['other'])

        penalty = 0.0

        # 超出範圍懲罰
        if value > threshold['max'] or value < threshold['min']:
            penalty += 0.3
        elif value > threshold['warning']:
            penalty += 0.1

        # 極值懲罰
        if pd.isna(value) or np.isinf(value):
            penalty += 0.5

        return min(1.0, penalty)

    def _predict_trends(self, data: pd.DataFrame) -> Dict:
        """
        趨勢預測
        
        Args:
            data: 當前資料
            
        Returns:
            預測結果
        """
        predictions = {}

        if self.trend_predictor is None:
            return predictions

        try:
            # 使用快取的歷史資料加上當前資料
            combined_data = pd.concat(
                [self.training_data_cache.tail(10), data], ignore_index=True)

            for metric in self.metrics_to_monitor:
                if metric not in combined_data.columns:
                    continue

                values = combined_data[metric].values
                if len(values) < 5:
                    continue

                # 使用最近5個點預測未來點
                recent_values = values[-5:]

                # 預測多個未來時間點
                future_predictions = []
                current_window = recent_values.copy()

                for _ in range(self.config['prediction_points']):
                    try:
                        next_pred = self.trend_predictor.predict(
                            [current_window])[0]
                        future_predictions.append(float(next_pred))

                        # 滑動窗口
                        current_window = np.append(current_window[1:],
                                                   next_pred)
                    except Exception as e:
                        logger.warning(f"預測 {metric} 失敗: {e}")
                        break

                if future_predictions:
                    predictions[metric] = {
                        'values':
                        future_predictions,
                        'trend':
                        self._calculate_trend_direction(future_predictions),
                        'confidence':
                        self._calculate_prediction_confidence(
                            recent_values, future_predictions)
                    }

        except Exception as e:
            logger.warning(f"趨勢預測失敗: {e}")

        return predictions

    def _calculate_trend_direction(self, predictions: List[float]) -> str:
        """
        計算趨勢方向
        
        Args:
            predictions: 預測值列表
            
        Returns:
            趨勢方向
        """
        if len(predictions) < 2:
            return "穩定"

        # 計算線性回歸斜率
        x = np.arange(len(predictions))
        slope = np.polyfit(x, predictions, 1)[0]

        if slope > 0.1:
            return "上升"
        elif slope < -0.1:
            return "下降"
        else:
            return "穩定"

    def _calculate_prediction_confidence(self, historical: np.ndarray,
                                         predictions: List[float]) -> float:
        """
        計算預測置信度
        
        Args:
            historical: 歷史資料
            predictions: 預測值
            
        Returns:
            置信度 (0-1)
        """
        # 基於歷史資料的變異性計算置信度
        historical_std = np.std(historical)

        if historical_std == 0:
            return 0.9  # 數據穩定，預測可信

        # 預測變異性
        prediction_std = np.std(predictions) if len(predictions) > 1 else 0

        # 置信度與歷史穩定性成正比，與預測變異性成反比
        confidence = max(
            0.1, min(0.9, 1.0 / (1.0 + historical_std + prediction_std)))

        return confidence

    def _evaluate_metrics_status(self, data: pd.DataFrame) -> Dict[str, str]:
        """
        評估各指標狀態
        
        Args:
            data: 資料
            
        Returns:
            指標狀態字典
        """
        status = {}

        for metric in data.columns:
            value = data.iloc[0][metric]

            if pd.isna(value):
                status[metric] = "無數據"
            elif np.isinf(value):
                status[metric] = "數據異常"
            else:
                # 基於快取資料計算狀態
                if not self.training_data_cache.empty and metric in self.training_data_cache.columns:
                    historical_values = self.training_data_cache[metric]
                    mean_val = historical_values.mean()
                    std_val = historical_values.std()

                    if std_val > 0:
                        z_score = abs(value - mean_val) / std_val
                        if z_score > 2:
                            status[metric] = "異常"
                        elif z_score > 1:
                            status[metric] = "警告"
                        else:
                            status[metric] = "正常"
                    else:
                        status[metric] = "正常"
                else:
                    status[metric] = "待評估"

        return status

    def _save_models(self) -> None:
        """儲存訓練好的模型"""
        try:
            model_data = {
                'isolation_forest': self.isolation_forest,
                'elliptic_envelope': self.elliptic_envelope,
                'trend_predictor': self.trend_predictor,
                'scaler': self.scaler,
                'config': self.config,
                'metrics_to_monitor': self.metrics_to_monitor,
                'last_train_time': self.last_train_time,
                'training_data_cache': self.training_data_cache
            }

            model_file = Path(self.model_path) / "anomaly_models.pkl"
            with open(model_file, 'wb') as f:
                pickle.dump(model_data, f)

            logger.info(f"模型已儲存至: {model_file}")

        except Exception as e:
            logger.error(f"模型儲存失敗: {e}")

    def _load_models(self) -> None:
        """載入已儲存的模型"""
        try:
            model_file = Path(self.model_path) / "anomaly_models.pkl"

            if not model_file.exists():
                logger.info("未找到已儲存的模型檔案")
                return

            with open(model_file, 'rb') as f:
                model_data = pickle.load(f)

            self.isolation_forest = model_data.get('isolation_forest')
            self.elliptic_envelope = model_data.get('elliptic_envelope')
            self.trend_predictor = model_data.get('trend_predictor')
            self.scaler = model_data.get('scaler')
            self.last_train_time = model_data.get('last_train_time')
            self.training_data_cache = model_data.get('training_data_cache',
                                                      pd.DataFrame())

            # 檢查模型完整性
            if all([self.isolation_forest, self.scaler]):
                self.is_trained = True
                logger.info("模型載入成功")
            else:
                logger.warning("模型檔案不完整")

        except Exception as e:
            logger.warning(f"模型載入失敗: {e}")

    def get_model_info(self) -> Dict:
        """
        獲取模型資訊
        
        Returns:
            模型資訊字典
        """
        info = {
            'is_trained':
            self.is_trained,
            'last_train_time':
            self.last_train_time.isoformat() if self.last_train_time else None,
            'metrics_monitored':
            self.metrics_to_monitor,
            'cache_size':
            len(self.training_data_cache),
            'config':
            self.config,
            'performance': {
                'avg_detection_time':
                np.mean(self.detection_times) if self.detection_times else 0,
                'avg_training_time':
                np.mean(self.training_times) if self.training_times else 0,
                'total_detections':
                len(self.detection_times),
                'total_trainings':
                len(self.training_times)
            }
        }

        if self.health_score_history:
            info['health_score_stats'] = {
                'current': self.health_score_history[-1],
                'average': np.mean(self.health_score_history),
                'min': np.min(self.health_score_history),
                'max': np.max(self.health_score_history)
            }

        return info

    def update_config(self, new_config: Dict) -> None:
        """
        更新配置參數
        
        Args:
            new_config: 新的配置字典
        """
        try:
            self._deep_update_dict(self.config, new_config)
            logger.info("配置更新成功")

            # 如果更新了關鍵參數，標記需要重新訓練
            critical_params = [
                'isolation_forest', 'elliptic_envelope', 'scaler_type'
            ]
            if any(param in new_config for param in critical_params):
                self.is_trained = False
                logger.info("檢測到關鍵參數變更，需要重新訓練模型")

        except Exception as e:
            logger.error(f"配置更新失敗: {e}")

    def add_metric(self, metric_name: str) -> None:
        """
        新增監控指標
        
        Args:
            metric_name: 指標名稱
        """
        if metric_name not in self.metrics_to_monitor:
            self.metrics_to_monitor.append(metric_name)
            self.is_trained = False  # 需要重新訓練
            logger.info(f"新增監控指標: {metric_name}")

    def remove_metric(self, metric_name: str) -> None:
        """
        移除監控指標
        
        Args:
            metric_name: 指標名稱
        """
        if metric_name in self.metrics_to_monitor:
            self.metrics_to_monitor.remove(metric_name)
            self.is_trained = False  # 需要重新訓練
            logger.info(f"移除監控指標: {metric_name}")

    def clear_cache(self) -> None:
        """清理快取資料"""
        self.training_data_cache = pd.DataFrame()
        self.health_score_history = []
        self.detection_times = []
        self.training_times = []
        logger.info("快取資料已清理")

    def export_results(self, output_path: str) -> None:
        """
        匯出檢測結果
        
        Args:
            output_path: 輸出路徑
        """
        try:
            results = {
                'model_info': self.get_model_info(),
                'health_score_history': self.health_score_history,
                'detection_times': self.detection_times,
                'training_times': self.training_times,
                'export_time': datetime.now().isoformat()
            }

            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            logger.info(f"結果已匯出至: {output_path}")

        except Exception as e:
            logger.error(f"結果匯出失敗: {e}")

    def get_health_trend(self, days: int = 7) -> Dict:
        """
        獲取健康評分趨勢
        
        Args:
            days: 天數
            
        Returns:
            趨勢分析結果
        """
        if not self.health_score_history:
            return {'trend': '無數據'}

        recent_scores = self.health_score_history[-days * 24:] if len(
            self.health_score_history
        ) > days * 24 else self.health_score_history

        if len(recent_scores) < 2:
            return {'trend': '數據不足'}

        # 計算趨勢
        x = np.arange(len(recent_scores))
        slope = np.polyfit(x, recent_scores, 1)[0]

        trend_direction = "上升" if slope > 0.5 else "下降" if slope < -0.5 else "穩定"

        return {
            'trend': trend_direction,
            'slope': slope,
            'average_score': np.mean(recent_scores),
            'score_variance': np.var(recent_scores),
            'data_points': len(recent_scores)
        }

    def diagnose_system(self) -> Dict:
        """
        系統診斷
        
        Returns:
            診斷結果
        """
        diagnosis = {
            'model_status': '正常' if self.is_trained else '未訓練',
            'data_cache_status':
            '正常' if not self.training_data_cache.empty else '空',
            'performance_status': '正常',
            'recommendations': []
        }

        # 效能診斷
        if self.detection_times:
            avg_detection_time = np.mean(self.detection_times)
            if avg_detection_time > 1.0:
                diagnosis['performance_status'] = '緩慢'
                diagnosis['recommendations'].append('考慮優化檢測演算法或減少監控指標')

        # 記憶體診斷
        cache_size = len(self.training_data_cache)
        if cache_size > self.config['cache_size'] * 1.5:
            diagnosis['recommendations'].append('快取資料過多，建議清理')

        # 模型診斷
        if self.last_train_time:
            hours_since_train = (datetime.now() -
                                 self.last_train_time).total_seconds() / 3600
            if hours_since_train > self.config['retrain_interval_hours'] * 2:
                diagnosis['recommendations'].append('模型訓練時間過久，建議重新訓練')

        # 健康評分診斷
        if self.health_score_history:
            recent_avg = np.mean(self.health_score_history[-10:])
            if recent_avg < 70:
                diagnosis['recommendations'].append('系統健康評分偏低，需要檢查設備狀態')

        return diagnosis


# 輔助功能類別
class AnomalyDetectorFactory:
    """異常檢測器工廠類別"""

    @staticmethod
    def create_detector(
            detector_type: str,
            metrics: List[str],
            config: Optional[Dict] = None) -> EnhancedAnomalyDetector:
        """
        建立異常檢測器
        
        Args:
            detector_type: 檢測器類型
            metrics: 監控指標
            config: 配置參數
            
        Returns:
            異常檢測器實例
        """
        base_config = {}

        if detector_type == "industrial":
            # 工業設備專用配置
            base_config = {
                'isolation_forest': {
                    'contamination': 0.005,  # 較低的異常比例
                    'n_estimators': 300,
                    'max_samples': 0.8
                },
                'min_data_points': 200,
                'retrain_interval_hours': 12,
                'health_weights': {
                    'temperature': 0.5,
                    'current': 0.3,
                    'pressure': 0.2
                }
            }
        elif detector_type == "sensitive":
            # 高敏感度配置
            base_config = {
                'isolation_forest': {
                    'contamination': 0.02,
                    'n_estimators': 100
                },
                'anomaly_threshold': -0.3,
                'min_data_points': 50
            }
        elif detector_type == "robust":
            # 強健型配置
            base_config = {
                'isolation_forest': {
                    'contamination': 0.001,
                    'n_estimators': 500
                },
                'anomaly_threshold': -0.8,
                'min_data_points': 500
            }

        if config:
            base_config.update(config)

        return EnhancedAnomalyDetector(metrics, base_config)


# 使用範例和測試函數
def example_usage():
    """使用範例"""

    # 1. 建立檢測器
    metrics = [
        'left_main_temp_pv', 'left_aux1a_temp_pv', 'left_aux1a_ct',
        'right_main_temp_pv', 'right_aux1a_temp_pv', 'right_aux1a_ct'
    ]

    # 使用工廠建立工業級檢測器
    detector = AnomalyDetectorFactory.create_detector("industrial", metrics)

    # 2. 準備訓練資料 (示例)
    training_data = pd.DataFrame({
        'left_main_temp_pv':
        np.random.normal(75, 5, 1000),
        'left_aux1a_temp_pv':
        np.random.normal(60, 3, 1000),
        'left_aux1a_ct':
        np.random.normal(25, 2, 1000),
        'right_main_temp_pv':
        np.random.normal(74, 5, 1000),
        'right_aux1a_temp_pv':
        np.random.normal(61, 3, 1000),
        'right_aux1a_ct':
        np.random.normal(24, 2, 1000)
    })

    # 3. 訓練模型
    success = detector.train_model(training_data)
    if success:
        print("模型訓練成功")

    # 4. 執行檢測
    current_data = pd.DataFrame({
        'left_main_temp_pv': [76.0],
        'left_aux1a_temp_pv': [62.0],
        'left_aux1a_ct': [26.0],
        'right_main_temp_pv': [75.0],
        'right_aux1a_temp_pv': [61.0],
        'right_aux1a_ct': [24.0]
    })

    result = detector.detect(current_data)
    print(f"檢測結果: {result}")

    # 5. 獲取模型資訊
    info = detector.get_model_info()
    print(f"模型資訊: {info}")

    # 6. 系統診斷
    diagnosis = detector.diagnose_system()
    print(f"系統診斷: {diagnosis}")


if __name__ == "__main__":
    # 設定記錄器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 執行範例
    example_usage()
