import requests
import pandas as pd
import time


class PrometheusClient:

    def __init__(self, prometheus_url="http://sn.yesiang.com:9090/metrics"):
        """
        初始化 Prometheus 客戶端。
        Args:
            prometheus_url (str): Prometheus 服務的 URL。
        """
        self.prometheus_url = prometheus_url
        self.query_api_url = f"{self.prometheus_url}/api/v1/query"
        self.query_range_api_url = f"{self.prometheus_url}/api/v1/query_range"
        print(f"初始化 Prometheus 客戶端，URL: {self.prometheus_url}")

    def query_instant(self, query):
        """
        執行 Prometheus 瞬時查詢（即時值）。
        Args:
            query (str): PromQL 查詢語句。
        Returns:
            dict: 查詢結果，如果失敗則為 None。
        """
        try:
            response = requests.get(self.query_api_url,
                                    params={'query': query})
            response.raise_for_status()  # 如果請求不成功則拋出 HTTPError
            result = response.json()
            if result['status'] == 'success':
                return result['data']['result']
            else:
                print(f"Prometheus 查詢失敗: {result.get('error', '未知錯誤')}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Prometheus 查詢請求錯誤: {e}")
            return None

    def query_range(self, query, start_time, end_time, step):
        """
        執行 Prometheus 範圍查詢（歷史趨勢）。
        Args:
            query (str): PromQL 查詢語句。
            start_time (int/str): 起始時間戳 (Unix timestamp) 或 'YYYY-MM-DDTHH:MM:SSZ' 格式。
            end_time (int/str): 結束時間戳 (Unix timestamp) 或 'YYYY-MM-DDTHH:MM:SSZ' 格式。
            step (str): 時間步長，例如 '1m', '5m', '1h'。
        Returns:
            list: 查詢結果列表，如果失敗則為空列表。
        """
        try:
            params = {
                'query': query,
                'start': start_time,
                'end': end_time,
                'step': step
            }
            response = requests.get(self.query_range_api_url, params=params)
            response.raise_for_status()
            result = response.json()
            if result['status'] == 'success':
                return result['data']['result']
            else:
                print(f"Prometheus 範圍查詢失敗: {result.get('error', '未知錯誤')}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"Prometheus 範圍查詢請求錯誤: {e}")
            return []

    def get_latest_data_for_metrics(self, metric_ids):
        """
        獲取指定 metric_ids 的最新數據。
        此處假設您的 Prometheus 標籤與 `plc_points.json` 中的 `id` 相符。
        例如，如果 `id` 是 `left_main_temp_pv`，Prometheus 中的 metric 名稱也是 `left_main_temp_pv`。
        Args:
            metric_ids (list): 要查詢的指標 ID 列表 (對應 `plc_points.json` 中的 `id`)。
        Returns:
            dict: 包含每個指標最新值的字典，例如 {'left_main_temp_pv': 25.5, ...}
        """
        latest_data = {}
        for metric_id in metric_ids:
            # 簡單的 PromQL 查詢，假設 metric_id 就是 PromQL 中的 metric 名稱
            query = f'{metric_id}'
            result = self.query_instant(query)
            if result and len(result) > 0:
                # result 結構通常是 [{'metric': {...}, 'value': [timestamp, value_str]}]
                # 我們取第一個結果的值
                try:
                    value = float(result[0]['value'][1])
                    latest_data[metric_id] = value
                except (ValueError, IndexError) as e:
                    print(f"解析指標 {metric_id} 的值時發生錯誤: {e}")
            else:
                latest_data[metric_id] = None  # 或 NaN
        return latest_data


if __name__ == "__main__":
    from config_loader import load_plc_points

    # 確保您的 Prometheus 服務正在運行
    client = PrometheusClient()

    plc_config = load_plc_points()
    if plc_config:
        all_metric_ids = []
        for group in plc_config['metric_groups']:
            for metric in group['metrics']:
                all_metric_ids.append(metric['id'])

        print("\n--- 獲取最新數據範例 ---")
        # 僅查詢前幾個指標以進行測試
        test_metric_ids = all_metric_ids[:5] if len(
            all_metric_ids) > 5 else all_metric_ids
        latest_values = client.get_latest_data_for_metrics(test_metric_ids)
        if latest_values:
            print("最新數據:")
            for metric_id, value in latest_values.items():
                print(f"  {metric_id}: {value}")
        else:
            print("未能從 Prometheus 獲取任何最新數據。請檢查 Prometheus 服務和指標名稱。")

        print("\n--- 範圍查詢範例 (最近1小時，每1分鐘一個點) ---")
        end_time = int(time.time())
        start_time = end_time - 3600  # 1 小時前
        # 查詢一個單一指標的歷史數據
        if test_metric_ids:
            history_query = f'{test_metric_ids[0]}'  # 查詢第一個測試指標
            history_data = client.query_range(history_query, start_time,
                                              end_time, '1m')
            if history_data:
                print(
                    f"指標 '{test_metric_ids[0]}' 的歷史數據點數: {len(history_data[0]['values']) if history_data else 0}"
                )
                # print("前 5 個歷史數據點:")
                # for ts, val in history_data[0]['values'][:5]:
                #     print(f"  時間: {pd.to_datetime(float(ts), unit='s')}, 值: {val}")
            else:
                print(f"未能從 Prometheus 獲取指標 '{test_metric_ids[0]}' 的歷史數據。")
        else:
            print("無指標可供歷史查詢。")
