import requests
import pandas as pd
import time
import re


class PrometheusClient:

    def __init__(self, prometheus_url="http://sn.yesiang.com:9090"):
        """
        初始化 Prometheus 客戶端，支援多種 URL 格式
        Args:
            prometheus_url (str): Prometheus 服務的 URL
        """
        # 標準化 URL
        self.prometheus_url = prometheus_url.rstrip('/')

        # 如果 URL 以 /metrics 結尾，提取基礎 URL
        if self.prometheus_url.endswith('/metrics'):
            self.base_url = self.prometheus_url[:-8]
            self.metrics_url = self.prometheus_url
        else:
            self.base_url = self.prometheus_url
            self.metrics_url = f"{self.prometheus_url}/metrics"

        self.query_api_url = f"{self.base_url}/api/v1/query"
        self.query_range_api_url = f"{self.base_url}/api/v1/query_range"

        print(f"初始化 Prometheus 客戶端")
        print(f"  基礎 URL: {self.base_url}")
        print(f"  Metrics URL: {self.metrics_url}")
        print(f"  API URL: {self.query_api_url}")

        # 檢測可用的端點
        self.api_available = self._test_api_endpoint()
        self.metrics_available = self._test_metrics_endpoint()

        if not self.api_available and not self.metrics_available:
            print("⚠️ 警告: 無法連接到任何 Prometheus 端點")

    def _test_api_endpoint(self):
        """測試 API 端點是否可用"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/status/config",
                                    timeout=3)
            if response.status_code == 200:
                print("✅ Prometheus API 端點可用")
                return True
        except:
            pass

        print("❌ Prometheus API 端點不可用")
        return False

    def _test_metrics_endpoint(self):
        """測試 /metrics 端點是否可用"""
        try:
            response = requests.get(self.metrics_url, timeout=3)
            if response.status_code == 200 and ("# HELP" in response.text
                                                or "# TYPE" in response.text):
                print("✅ Prometheus /metrics 端點可用")
                return True
        except:
            pass

        print("❌ Prometheus /metrics 端點不可用")
        return False

    def query_instant(self, query):
        """
        執行 Prometheus 瞬時查詢（即時值）
        """
        if not self.api_available:
            print("API 端點不可用，無法執行查詢")
            return None

        try:
            response = requests.get(self.query_api_url,
                                    params={'query': query},
                                    timeout=5)
            response.raise_for_status()
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
        執行 Prometheus 範圍查詢（歷史趨勢）
        """
        if not self.api_available:
            print("API 端點不可用，無法執行範圍查詢")
            return []

        try:
            params = {
                'query': query,
                'start': start_time,
                'end': end_time,
                'step': step
            }
            response = requests.get(self.query_range_api_url,
                                    params=params,
                                    timeout=10)
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
        獲取指定 metric_ids 的最新數據
        """
        if self.api_available:
            return self._get_data_via_api(metric_ids)
        elif self.metrics_available:
            return self._get_data_via_metrics_endpoint(metric_ids)
        else:
            print("沒有可用的數據端點")
            return {metric_id: None for metric_id in metric_ids}

    def _get_data_via_api(self, metric_ids):
        """透過 API 獲取數據"""
        latest_data = {}

        for metric_id in metric_ids:
            # 嘗試不同的查詢格式
            queries_to_try = [
                metric_id,  # 基本查詢
                f'{metric_id}{{}}',  # 帶空標籤
                f'{{__name__="{metric_id}"}}',  # 使用 __name__ 選擇器
            ]

            found_data = False
            for query in queries_to_try:
                result = self.query_instant(query)
                if result and len(result) > 0:
                    try:
                        value = float(result[0]['value'][1])
                        latest_data[metric_id] = value
                        found_data = True
                        break
                    except (ValueError, IndexError, KeyError):
                        continue

            if not found_data:
                latest_data[metric_id] = None

        return latest_data

    def _get_data_via_metrics_endpoint(self, metric_ids):
        """透過 /metrics 端點獲取數據"""
        try:
            response = requests.get(self.metrics_url, timeout=10)
            if response.status_code != 200:
                return {metric_id: None for metric_id in metric_ids}

            metrics_text = response.text
            latest_data = {}

            for metric_id in metric_ids:
                # 使用正則表達式搜尋指標
                # 匹配格式: metric_name{labels} value
                # 修正 f-string 中的大括號轉義問題
                escaped_metric = re.escape(metric_id)
                pattern = r'^' + escaped_metric + r'(?:\{[^}]*\})?\s+([0-9.-]+(?:[eE][+-]?[0-9]+)?)'
                matches = re.findall(pattern, metrics_text, re.MULTILINE)

                if matches:
                    try:
                        # 取最後一個匹配的值
                        latest_data[metric_id] = float(matches[-1])
                    except ValueError:
                        latest_data[metric_id] = None
                else:
                    latest_data[metric_id] = None

            return latest_data

        except Exception as e:
            print(f"從 /metrics 端點獲取數據失敗: {e}")
            return {metric_id: None for metric_id in metric_ids}

    def get_available_metrics(self):
        """獲取所有可用的指標名稱"""
        metrics = []

        # 優先嘗試 API 方式
        if self.api_available:
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/label/__name__/values",
                    timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data['status'] == 'success':
                        metrics.extend(data['data'])
            except Exception as e:
                print(f"透過 API 獲取指標列表失敗: {e}")

        # 如果 API 沒有結果，嘗試 /metrics 端點
        if not metrics and self.metrics_available:
            try:
                response = requests.get(self.metrics_url, timeout=10)
                if response.status_code == 200:
                    lines = response.text.split('\n')
                    metric_names = set()

                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if ' ' in line:
                                metric_part = line.split(' ')[0]
                                if '{' in metric_part:
                                    metric_name = metric_part.split('{')[0]
                                else:
                                    metric_name = metric_part
                                metric_names.add(metric_name)

                    metrics = list(metric_names)
            except Exception as e:
                print(f"透過 /metrics 端點獲取指標列表失敗: {e}")

        return sorted(metrics)


if __name__ == "__main__":
    from config_loader import load_plc_points

    # 測試不同的 URL 格式
    test_urls = [
        "http://sn.yesiang.com:9090", "http://sn.yesiang.com:9090/metrics"
    ]

    for url in test_urls:
        print(f"\n{'='*50}")
        print(f"測試 URL: {url}")
        print('=' * 50)

        client = PrometheusClient(url)

        if client.api_available or client.metrics_available:
            print(f"✅ 連接成功！")

            # 獲取可用指標
            available_metrics = client.get_available_metrics()
            print(f"找到 {len(available_metrics)} 個可用指標")

            if available_metrics:
                print("前10個指標:")
                for i, metric in enumerate(available_metrics[:10]):
                    print(f"  {i+1}. {metric}")

            # 測試配置中的指標
            plc_config = load_plc_points()
            if plc_config:
                test_metrics = []
                for group in plc_config['metric_groups']:
                    for metric in group['metrics'][:3]:  # 只測試前3個
                        test_metrics.append(metric['id'])

                print(f"\n測試配置指標: {test_metrics}")
                latest_data = client.get_latest_data_for_metrics(test_metrics)

                for metric_id, value in latest_data.items():
                    if value is not None:
                        print(f"  {metric_id}: {value}")
                    else:
                        print(f"  {metric_id}: 無數據")

            break  # 找到可用的 URL 就停止測試
        else:
            print(f"❌ 無法連接到 {url}")

    else:
        print("\n❌ 所有 URL 都無法连接")
