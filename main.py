import time
import threading
import sys
import os
import pandas as pd

# 引入核心模組
from config_loader import load_plc_points, load_devices
from prometheus_client import PrometheusClient
from data_processor import DataProcessor
from anomaly_detector import AnomalyDetector

# 加載配置
plc_config = load_plc_points()
device_config = load_devices()

# 初始化客戶端和處理器
prometheus_client = PrometheusClient(
    prometheus_url="http://sn.yesiang.com:9090")
data_processor = DataProcessor(plc_config)

# 初始化異常檢測器 (與 dashboard_app.py 中一致)
metrics_for_anomaly = [
    'left_main_temp_pv', 'left_aux1a_temp_pv', 'left_aux1a_ct',
    'right_main_temp_pv', 'right_aux1a_temp_pv', 'right_aux1a_ct'
]
anomaly_detector = AnomalyDetector(metrics_for_anomaly)


def data_collection_and_processing_loop():
    """數據採集和處理循環"""
    print("\n--- 開始模擬數據採集和處理循環 ---")

    # 獲取所有指標 ID
    all_metric_ids = []
    for group in plc_config['metric_groups']:
        for metric in group['metrics']:
            all_metric_ids.append(metric['id'])

    if not device_config['devices']:
        print("未找到任何設備配置。")
        return

    first_device_id = device_config['devices'][0]['id']

    while True:
        try:
            # 從 Prometheus 獲取最新數據
            latest_raw_data = prometheus_client.get_latest_data_for_metrics(
                all_metric_ids)

            if latest_raw_data:
                # 處理數據，轉換為 DataFrame
                processed_df = data_processor.process_latest_data(
                    latest_raw_data, device_id=first_device_id)

                if not processed_df.empty:
                    print(
                        f"[{time.strftime('%H:%M:%S')}] 成功採集和處理來自設備 {first_device_id} 的數據。"
                    )

                    # 進行異常檢測
                    try:
                        # 確保所有需要的指標都存在
                        available_metrics = [
                            m for m in metrics_for_anomaly
                            if m in processed_df.columns
                        ]
                        if available_metrics and anomaly_detector.model is not None:
                            current_data_for_anomaly = processed_df[
                                available_metrics]
                            detection_result = anomaly_detector.detect(
                                current_data_for_anomaly)

                            if detection_result['is_anomaly']:
                                print(
                                    f"!!! 警告: 檢測到設備 {first_device_id} 異常！"
                                    f"異常分數: {detection_result['anomaly_score']:.2f}"
                                )
                        else:
                            print("異常檢測模型未就緒或缺少必要指標")
                    except Exception as e:
                        print(f"異常檢測時發生錯誤: {e}")
                else:
                    print(
                        f"[{time.strftime('%H:%M:%S')}] 未能處理來自設備 {first_device_id} 的數據。"
                    )
            else:
                print(
                    f"[{time.strftime('%H:%M:%S')}] 未能從 Prometheus 獲取設備 {first_device_id} 的數據。"
                )

        except Exception as e:
            print(f"數據採集和處理循環中發生錯誤: {e}")

        time.sleep(5)  # 每 5 秒執行一次循環


def train_anomaly_model():
    """訓練異常檢測模型"""
    print("--- 正在確保異常檢測模型已初始化和訓練 ---")

    end_time_train = int(time.time())
    start_time_train = end_time_train - 24 * 3600  # 過去 24 小時
    training_data_list = []

    # 逐一查詢每個設備的每個監控指標的歷史數據
    for device in device_config['devices']:
        for metric_id in metrics_for_anomaly:
            try:
                query_result = prometheus_client.query_range(
                    f'{metric_id}{{device_id="{device["id"]}"}}',
                    start_time_train, end_time_train, '5m')
                if query_result:
                    df_temp = data_processor.process_range_data(
                        query_result, device_id=device['id'])
                    if not df_temp.empty:
                        training_data_list.append(df_temp)
            except Exception as e:
                print(f"查詢設備 {device['id']} 指標 {metric_id} 時發生錯誤: {e}")

    if training_data_list:
        try:
            historical_training_df = pd.concat(training_data_list,
                                               ignore_index=True)
            historical_training_df = historical_training_df.groupby(
                ['timestamp', 'device_id']).first().reset_index()
            anomaly_detector.train_model(historical_training_df)
            print("異常檢測模型初始化和訓練完成。")
        except Exception as e:
            print(f"訓練異常檢測模型時發生錯誤: {e}")
    else:
        print("未能載入足夠的歷史數據以訓練異常檢測模型。異常檢測功能可能無法使用。")


def run_dash_app():
    """啟動 Dash 儀表板應用"""
    print("\n--- 啟動 Dash 儀表板應用 ---")
    try:
        # 直接匯入並執行 dashboard_app，而不是使用 subprocess
        print("正在匯入 dashboard_app...")
        import dashboard_app
        print("dashboard_app 匯入成功，準備啟動...")

        # 檢查 app 物件是否存在
        if hasattr(dashboard_app, 'app') and dashboard_app.app is not None:
            print("使用現有的 app 物件啟動伺服器...")
            # 使用新版 Dash 的 app.run 方法
            dashboard_app.app.run(debug=True, host='0.0.0.0', port=8050)
        else:
            print("app 物件不存在，呼叫 main 函數...")
            dashboard_app.main()

    except ImportError as e:
        print(f"匯入 dashboard_app 時發生錯誤: {e}")
        print("請確認 dashboard_app.py 檔案存在且語法正確")
        return False
    except Exception as e:
        print(f"啟動 Dash 應用時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def run_dash_app_subprocess():
    """使用子程序啟動 Dash 儀表板應用（替代方案）"""
    print("\n--- 使用子程序啟動 Dash 儀表板應用 ---")
    try:
        import subprocess
        # 使用當前 Python 解譯器的完整路徑
        python_executable = sys.executable
        subprocess.run([python_executable, "dashboard_app.py"])
    except Exception as e:
        print(f"使用子程序啟動 Dash 應用時發生錯誤: {e}")


if __name__ == "__main__":
    try:
        # 首先訓練異常檢測模型
        train_anomaly_model()

        # 啟動數據採集和處理的後台線程（可選）
        # 如果您需要後端持續進行複雜的AI分析或數據清理，則此線程有用
        data_thread = threading.Thread(
            target=data_collection_and_processing_loop)
        data_thread.daemon = True  # 設定為守護線程，主程序退出時自動結束
        data_thread.start()
        print("後台數據處理線程已啟動")

        # 啟動 Dash 儀表板應用
        # 這會阻塞主線程，直到儀表板關閉
        print("\n嘗試直接匯入方式啟動 Dash 應用...")
        run_dash_app()

    except KeyboardInterrupt:
        print("\n收到中斷信號，正在關閉應用...")
    except Exception as e:
        print(f"主程序發生錯誤: {e}")
        print("\n嘗試使用子程序方式啟動 Dash 應用...")
        run_dash_app_subprocess()
    finally:
        print("\n--- 應用程序已退出 ---")
