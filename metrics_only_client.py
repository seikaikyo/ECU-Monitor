import requests
import pandas as pd
import time
import re
from datetime import datetime


class MetricsOnlyPrometheusClient:
    """
    專門處理 Prometheus /metrics 端點的客戶端
    適用於只有 /metrics 端點可用的情況
    """

    def __init__(self, metrics_url="http://sn.yesiang.com:9090/metrics"):
        """
        初始化客戶端
        Args:
            metrics_url (str): Prometheus metrics 端點的完整 URL
        """
        self.metrics_url = metrics_url
        self.cached_metrics = {}
        self.last_fetch_time = 0
        self.cache_duration = 5  # 快取 5 秒
        
        print(f"初始化 Metrics-Only Prometheus 客戶端")
        print(f"Metrics URL: {self.metrics_url}")
        
        # 測試連線
        self.available = self._test_connection()
        if self.available:
            print("✅ Metrics 端點連線成功")
        else:
            print("❌ Metrics 端點連線失敗")

    def _test_connection(self):
        """測試連線"""
        try:
            response = requests.get(self.metrics_url, timeout=5)
            return response.status_code == 200 and "# HELP" in response.text
        except:
            return False

    def _fetch_all_metrics(self):
        """獲取所有指標數據並快取"""
        current_time = time.time()
        
        # 如果快取仍有效，直接返回
        if current_time - self.last_fetch_time < self.cache_duration and self.cached_metrics:
            return self.cached_metrics
        
        try:
            response = requests.get(self.metrics_url, timeout=10)
            if response.status_code != 200:
                print(f"HTTP 錯誤: {response.status_code}")
                return {}
            
            metrics_text = response.text
            parsed_metrics = {}
            
            # 解析 metrics 格式
            lines = metrics_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        # 分割指標名稱和值
                        if ' ' in line:
                            parts = line.split(' ', 1)
                            if len(parts) == 2:
                                metric_part = parts[0]
                                value_str = parts[1]
                                
                                # 提取指標名稱（移除標籤）
                                if '{' in metric_part:
                                    metric_name = metric_part.split('{')[0]
                                    labels = metric_part[metric_part.find('{'):]
                                else:
                                    metric_name = metric_part
                                    labels = ""
                                
                                # 轉換值
                                try:
                                    value = float(value_str)
                                    
                                    # 儲存指標（如果有多個相同名稱的指標，保留最新的）
                                    parsed_metrics[metric_name] = {
                                        'value': value,
                                        'labels': labels,
                                        'raw_line': line
                                    }
                                except ValueError:
                                    continue
                    except Exception as e:
                        continue
            
            self.cached_metrics = parsed_metrics
            self.last_fetch_time = current_time
            print(f"✅ 成功解析 {len(parsed_metrics)} 個指標")
            return parsed_metrics
            
        except Exception as e:
            print(f"獲取指標數據失敗: {e}")
            return {}

    def get_latest_data_for_metrics(self, metric_ids):
        """
        獲取指定指標的最新數據
        Args:
            metric_ids (list): 指標 ID 列表
        Returns:
            dict: 指標名稱到數值的映射
        """
        if not self.available:
            print("❌ Metrics 端點不可用")
            return {metric_id: None for metric_id in metric_ids}
        
        all_metrics = self._fetch_all_metrics()
        latest_data = {}
        
        for metric_id in metric_ids:
            if metric_id in all_metrics:
                latest_data[metric_id] = all_metrics[metric_id]['value']
                print(f"✅ {metric_id}: {all_metrics[metric_id]['value']}")
            else:
                latest_data[metric_id] = None
                print(f"❌ {metric_id}: 未找到")
        
        return latest_data

    def query_instant(self, query):
        """
        模擬瞬時查詢（實際上從 /metrics 獲取）
        Args:
            query (str): 指標名稱
        Returns:
            list: 模擬 Prometheus API 的回應格式
        """
        all_metrics = self._fetch_all_metrics()
        
        if query in all_metrics:
            current_timestamp = time.time()
            return [{
                'metric': {'__name__': query},
                'value': [current_timestamp, str(all_metrics[query]['value'])]
            }]
        else:
            return []

    def query_range(self, query, start_time, end_time, step):
        """
        模擬範圍查詢（生成假的歷史數據）
        Args:
            query (str): 指標名稱
            start_time (int): 開始時間戳
            end_time (int): 結束時間戳  
            step (str): 步長
        Returns:   
            list: 模擬 Prometheus API 的回應格式
        """
        # 從查詢中提取指標名稱
        metric_name = query.split('{')[0] if '{' in query else query
        
        all_metrics = self._fetch_all_metrics()
        
        if metric_name not in all_metrics:
            return []
        
        current_value = all_metrics[metric_name]['value']
        
        # 生成模擬的歷史數據
        values = []
        step_seconds = self._parse_step_to_seconds(step)
        
        timestamp = start_time
        while timestamp <= end_time:
            # 在當前值基礎上添加一些隨機變化
            import random
            variation = random.uniform(-0.05, 0.05)  # ±5% 變化
            simulated_value = current_value * (1 + variation)
            
            values.append([timestamp, str(round(simulated_value, 2))])
            timestamp += step_seconds
        
        return [{
            'metric': {'__name__': metric_name},
            'values': values
        }]

    def _parse_step_to_seconds(self, step):
        """將步長字串轉換為秒數"""
        if step.endswith('s'):
            return int(step[:-1])
        elif step.endswith('m'):
            return int(step[:-1]) * 60
        elif step.endswith('h'):
            return int(step[:-1]) * 3600
        else:
            return 60  # 預設 1 分鐘

    def get_available_metrics(self):
        """獲取所有可用指標的列表"""
        all_metrics = self._fetch_all_metrics() 
        return sorted(list(all_metrics.keys()))

    def search_metrics(self, pattern):
        """搜尋包含特定模式的指標"""
        all_metrics = self._fetch_all_metrics()
        matching = []
        
        for metric_name in all_metrics.keys():
            if pattern.lower() in metric_name.lower():
                matching.append(metric_name)
        
        return sorted(matching)


if __name__ == "__main__":
    print("=== 測試 Metrics-Only Prometheus 客戶端 ===\n")
    
    client = MetricsOnlyPrometheusClient()
    
    if client.available:
        print("✅ 客戶端初始化成功")
        
        # 獲取所有可用指標
        available_metrics = client.get_available_metrics()
        print(f"\n找到 {len(available_metrics)} 個可用指標")
        
        # 顯示前20個指標
        print("\n前20個指標:")
        for i, metric in enumerate(available_metrics[:20]):
            print(f"  {i+1}. {metric}")
        
        if len(available_metrics) > 20:
            print(f"  ... 還有 {len(available_metrics) - 20} 個指標")
        
        # 搜尋可能相關的指標
        print(f"\n搜尋相關指標:")
        patterns = ['temp', 'current', 'motor', 'pressure', 'voltage', 'power']
        
        for pattern in patterns:
            matches = client.search_metrics(pattern)
            if matches:
                print(f"  {pattern.upper()}: {len(matches)} 個")
                for match in matches[:3]:
                    print(f"    - {match}")
                if len(matches) > 3:
                    print(f"    ... 還有 {len(matches) - 3} 個")
        
        # 測試數據獲取
        if available_metrics:
            print(f"\n測試數據獲取 (前5個指標):")
            test_metrics = available_metrics[:5]
            latest_data = client.get_latest_data_for_metrics(test_metrics)
            
            for metric_id, value in latest_data.items():
                if value is not None:
                    print(f"  {metric_id}: {value}")
                else:
                    print(f"  {metric_id}: 無數據")
    
    else:
        print("❌ 客戶端初始化失敗")
        print("請檢查 URL 和網路連線")