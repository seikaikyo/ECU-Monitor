import pandas as pd


class DataProcessor:

    def __init__(self, plc_points_config):
        """
        初始化資料處理器。
        Args:
            plc_points_config (dict): PLC 點位配置資料。
        """
        self.plc_points_config = plc_points_config
        # 建立一個 id 到 unit 和 name 的映射，方便查找
        self.metric_info_map = {}
        for group in plc_points_config['metric_groups']:
            for metric in group['metrics']:
                self.metric_info_map[metric['id']] = {
                    'name': metric['name'],
                    'unit': metric['unit'],
                    'data_type': metric['data_type'],  # 可能仍用於浮點數處理提醒
                    'scale_factor': metric['scale_factor']  # 可能仍用於驗證或後處理
                }

    def process_latest_data(self,
                            latest_data_dict,
                            device_id="unknown_device"):
        """
        處理從 Prometheus 獲取的最新數據。
        Args:
            latest_data_dict (dict): 從 PrometheusClient 獲取的最新數據字典。
                                     範例: {'left_main_temp_pv': 25.5, ...}
            device_id (str): 設備ID，用於標識資料來源。
        Returns:
            pd.DataFrame: 處理後的單行數據，包含時間戳、設備ID和各種指標。
        """
        if not latest_data_dict:
            return pd.DataFrame()

        processed_record = {}
        for metric_id, value in latest_data_dict.items():
            processed_record[metric_id] = value
            # Prometheus 通常已經處理了 scale_factor，所以這裡不再重複
            # 但我們可以記錄單位資訊或其他元數據
            if metric_id in self.metric_info_map:
                processed_record[f'{metric_id}_unit'] = self.metric_info_map[
                    metric_id]['unit']
                processed_record[f'{metric_id}_name'] = self.metric_info_map[
                    metric_id]['name']

        df = pd.DataFrame([processed_record])
        df['timestamp'] = pd.to_datetime('now')  # 獲取處理時的當前時間
        df['device_id'] = device_id
        return df

    def process_range_data(self, range_data_list, device_id="unknown_device"):
        """
        處理從 Prometheus 範圍查詢獲取的歷史數據。
        Args:
            range_data_list (list): Prometheus 範圍查詢的結果，通常是一個列表，
                                    每個元素包含 'metric' 和 'values'。
                                    範例: [{'metric': {'__name__': 'metric_name', ...}, 'values': [[timestamp, value_str], ...]}, ...]
            device_id (str): 設備ID，用於標識資料來源。
        Returns:
            pd.DataFrame: 包含歷史數據的 DataFrame。
        """
        if not range_data_list:
            return pd.DataFrame()

        all_records = []
        for entry in range_data_list:
            metric_id = entry['metric'].get(
                '__name__')  # PromQL 預設的 metric 名稱鍵
            if not metric_id:
                continue

            for timestamp_str, value_str in entry['values']:
                try:
                    record = {
                        'timestamp': pd.to_datetime(float(timestamp_str),
                                                    unit='s'),
                        'device_id':
                        device_id,  # 您可能需要更複雜的邏輯來從Prometheus標籤中提取device_id
                        metric_id: float(value_str)
                    }
                    if metric_id in self.metric_info_map:
                        record[f'{metric_id}_unit'] = self.metric_info_map[
                            metric_id]['unit']
                        record[f'{metric_id}_name'] = self.metric_info_map[
                            metric_id]['name']
                    all_records.append(record)
                except (ValueError, TypeError) as e:
                    print(f"處理歷史數據時解析值錯誤: {e}")
                    continue

        if not all_records:
            return pd.DataFrame()

        # 將多個指標的歷史數據合併到一個 DataFrame 中，可能需要 pivot
        df = pd.DataFrame(all_records)
        # 通常 PromQL 範圍查詢會為每個 metric 返回一個 series，這裡需要考慮合併
        # 對於多個指標，可能需要手動 pivot
        if 'timestamp' in df.columns and 'device_id' in df.columns:
            # 確保 'timestamp' 和 'device_id' 是索引，然後 unstack
            df = df.set_index(['timestamp', 'device_id'])
            # 這裡簡單地將所有指標列保留，如果 PromQL 查詢單一指標，則只有該列
            # 如果查詢多個指標，且它們在不同行，需要進一步處理
            # 最常見的處理方式是為每個 metric 獨立調用 process_range_data，然後合併結果
            pass
        return df


if __name__ == "__main__":
    from config_loader import load_plc_points
    from prometheus_client import PrometheusClient
    import time

    plc_config = load_plc_points()
    client = PrometheusClient()
    processor = DataProcessor(plc_config)

    # 假設您知道哪些 metric_ids 是溫度控制器的一部分
    temp_controller_metric_ids = []
    for group in plc_config['metric_groups']:
        if group['group_name'] == '溫度控制器':
            temp_controller_metric_ids = [m['id'] for m in group['metrics']]
            break

    if plc_config and temp_controller_metric_ids:
        print("\n--- 處理最新數據範例 ---")
        latest_raw_data = client.get_latest_data_for_metrics(
            temp_controller_metric_ids[:5])  # 獲取部分指標
        if latest_raw_data:
            processed_latest_df = processor.process_latest_data(
                latest_raw_data, device_id="ecu1051_1")
            print("處理後的最新 DataFrame 範例:")
            print(processed_latest_df.head())
        else:
            print("未能獲取最新數據，無法處理。")

        print("\n--- 處理範圍查詢數據範例 ---")
        end_time = int(time.time())
        start_time = end_time - 3600  # 1 小時前
        # 查詢單一指標的歷史數據，然後處理
        if temp_controller_metric_ids:
            history_query = f'{temp_controller_metric_ids[0]}'
            history_raw_data = client.query_range(history_query, start_time,
                                                  end_time, '1m')
            if history_raw_data:
                # 處理範圍查詢結果可能需要更複雜的合併邏輯，這裡簡化處理單一 metric
                # 如果您查詢了多個 metric，需要為每個 metric 調用 process_range_data 或修改其邏輯
                processed_history_df = processor.process_range_data(
                    history_raw_data, device_id="ecu1051_1")
                print(
                    f"處理後的歷史 DataFrame 範例 (針對 {temp_controller_metric_ids[0]}):"
                )
                print(processed_history_df.head())
            else:
                print("未能獲取歷史數據，無法處理。")
    else:
        print("未載入 PLC 配置或溫度控制器指標。")
        print("請檢查 PLC 配置文件或 Prometheus 服務。")
