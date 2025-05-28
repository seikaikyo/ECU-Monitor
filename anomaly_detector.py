import pandas as pd
from sklearn.ensemble import IsolationForest
import numpy as np


class AnomalyDetector:

    def __init__(self, metrics_to_monitor, model_path=None):
        """
        初始化異常檢測器。
        Args:
            metrics_to_monitor (list): 要監控的指標ID列表。
            model_path (str): 預訓練模型的路徑（可選）。
        """
        self.metrics_to_monitor = metrics_to_monitor
        self.model = None
        if model_path:
            # 實際應用中會載入訓練好的模型
            try:
                # self.model = joblib.load(model_path)
                print(f"警告: 模型載入功能未實作，請自行處理 {model_path} 的載入。")
            except Exception as e:
                print(f"載入模型時發生錯誤: {e}")
        else:
            # 如果沒有模型，將在第一次fit時訓練一個新模型
            pass

    def train_model(self, historical_data_df):
        """
        使用歷史數據訓練異常檢測模型。
        Args:
            historical_data_df (pd.DataFrame): 包含要監控指標的歷史數據。
        """
        if self.metrics_to_monitor and not historical_data_df.empty:
            data_for_training = historical_data_df[
                self.metrics_to_monitor].dropna()
            if not data_for_training.empty:
                self.model = IsolationForest(contamination=0.01,
                                             random_state=42)  # 假設 1% 的數據是異常
                self.model.fit(data_for_training)
                print(f"異常檢測模型已訓練，監控指標：{self.metrics_to_monitor}")
            else:
                print("用於訓練的歷史數據為空或不包含指定指標。")
        else:
            print("沒有指定要監控的指標或歷史數據為空，無法訓練模型。")

    def detect(self, current_data_df):
        """
        對當前數據進行異常檢測。
        Args:
            current_data_df (pd.DataFrame): 包含當前數據的 DataFrame（單行）。
        Returns:
            dict: 異常檢測結果，包含是否異常和異常分數。
        """
        if self.model is None:
            print("警告：異常檢測模型未訓練。無法進行檢測。")
            return {"is_anomaly": False, "anomaly_score": 0.0}

        if current_data_df.empty or not all(
                metric in current_data_df.columns
                for metric in self.metrics_to_monitor):
            print("警告：當前數據無效或不包含所有監控指標。")
            return {"is_anomaly": False, "anomaly_score": 0.0}

        # 確保數據順序與訓練時一致
        data_for_prediction = current_data_df[
            self.metrics_to_monitor].values.reshape(1, -1)

        # 預測異常分數 (-1為異常，1為正常)
        prediction = self.model.predict(data_for_prediction)

        # IsolationForest 的分數是負數，分數越小越異常
        anomaly_score = self.model.decision_function(data_for_prediction)[0]

        is_anomaly = (prediction[0] == -1)

        return {"is_anomaly": is_anomaly, "anomaly_score": anomaly_score}


if __name__ == "__main__":
    from config_loader import load_plc_points
    from modbus_client import ModbusPLCClient
    from data_processor import DataProcessor
    from devices import devices  # 假設 devices.json 的內容已載入

    plc_config = load_plc_points()
    device_info_test = devices[0]

    if plc_config and device_info_test:
        client = ModbusPLCClient(device_info_test, plc_config)
        processor = DataProcessor(plc_config)

        # 模擬一些歷史數據用於訓練
        historical_data_list = []
        for _ in range(100):  # 100 個數據點
            raw_data = client.read_data()
            if raw_data:
                processed_df = processor.process_raw_data(raw_data)
                historical_data_list.append(processed_df)
            time.sleep(0.01)  # 短暫延遲
        historical_df = pd.concat(historical_data_list, ignore_index=True)

        # 選擇要監控的指標
        metrics_to_monitor_example = [
            'left_main_temp_pv', 'left_aux1a_ct', 'motor_freq_left_1a'
        ]
        detector = AnomalyDetector(metrics_to_monitor_example)
        detector.train_model(historical_df)

        print("\n--- 異常檢測範例 ---")
        for i in range(5):
            raw_data = client.read_data()
            if raw_data:
                processed_df = processor.process_raw_data(raw_data)

                # 模擬一個異常數據 (例如，讓 left_main_temp_pv 異常高)
                if i == 2:
                    print("模擬異常數據...")
                    processed_df['left_main_temp_pv'] = 1000.0  # 正常值約在200-500
                    processed_df['left_aux1a_ct'] = 500.0
                    processed_df['motor_freq_left_1a'] = 1.0  # 頻率異常低

                detection_result = detector.detect(processed_df)
                print(
                    f"時間: {processed_df['timestamp'].iloc[0]}, 異常狀態: {detection_result['is_anomaly']}, 分數: {detection_result['anomaly_score']:.2f}"
                )

        client.close()
