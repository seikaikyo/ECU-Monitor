#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修正數據存取問題
解決儀表板能找到指標但無法獲取數值的問題
"""

import requests
import json
import time

def test_metric_access():
    """測試指標存取"""
    print("=== 測試指標存取 ===\n")
    
    # 從截圖中看到的指標
    test_metrics = [
        "Right Aux2A Temp Pv",
        "Right Heater2A Temp", 
        "Right Outlet Temp Inner Top"
    ]
    
    # 可能的 Prometheus 端點
    endpoints_to_test = [
        "http://localhost:9090",
        "http://127.0.0.1:9090",
        "http://sn.yesiang.com:9090",
        "http://10.6.35.90:9090"
    ]
    
    working_endpoint = None
    
    for endpoint in endpoints_to_test:
        print(f"🔍 測試端點: {endpoint}")
        
        try:
            # 測試基本連接
            response = requests.get(f"{endpoint}/api/v1/status/config", timeout=3)
            if response.status_code == 200:
                print(f"✅ 端點可用")
                
                # 獲取所有指標
                metrics_response = requests.get(f"{endpoint}/api/v1/label/__name__/values", timeout=5)
                if metrics_response.status_code == 200:
                    data = metrics_response.json()
                    if data.get('status') == 'success':
                        all_metrics = data.get('data', [])
                        print(f"✅ 找到 {len(all_metrics)} 個指標")
                        
                        # 尋找相似的指標名稱
                        similar_metrics = find_similar_metrics(test_metrics, all_metrics)
                        
                        if similar_metrics:
                            print(f"🎯 找到相似指標:")
                            for expected, actual in similar_metrics.items():
                                print(f"  期望: {expected}")
                                print(f"  實際: {actual}")
                                
                                # 測試數值獲取
                                value = query_metric_value(endpoint, actual)
                                if value is not None:
                                    print(f"  數值: {value}")
                                else:
                                    print(f"  數值: 無法獲取")
                                print()
                            
                            working_endpoint = endpoint
                            return working_endpoint, similar_metrics
                        else:
                            print(f"❌ 未找到相似指標")
                else:
                    print(f"❌ 無法獲取指標列表")
            else:
                print(f"❌ 端點不可用 (HTTP {response.status_code})")
                
        except Exception as e:
            print(f"❌ 連接失敗: {e}")
        
        print()
    
    return None, {}

def find_similar_metrics(expected_metrics, actual_metrics):
    """尋找相似的指標名稱"""
    similar_mapping = {}
    
    for expected in expected_metrics:
        # 提取關鍵字
        expected_words = expected.lower().replace(' ', '_').split('_')
        
        best_match = None
        best_score = 0
        
        for actual in actual_metrics:
            actual_lower = actual.lower()
            
            # 計算匹配分數
            score = sum(1 for word in expected_words if word in actual_lower)
            
            if score > best_score:
                best_score = score
                best_match = actual
        
        if best_match and best_score > 0:
            similar_mapping[expected] = best_match
    
    return similar_mapping

def query_metric_value(endpoint, metric_name):
    """查詢指標數值"""
    try:
        response = requests.get(f"{endpoint}/api/v1/query", 
                              params={'query': metric_name}, 
                              timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                result = data.get('data', {}).get('result', [])
                if result:
                    return float(result[0]['value'][1])
        return None
    except:
        return None

def create_corrected_client():
    """建立修正的客戶端"""
    print("=== 建立修正的客戶端 ===\n")
    
    corrected_client_code = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修正的 Prometheus 客戶端
使用正確的端點和指標名稱映射
"""

import requests
import pandas as pd
import time
import re
from datetime import datetime


class CorrectedPrometheusClient:
    """修正的 Prometheus 客戶端"""
    
    def __init__(self, prometheus_url="http://localhost:9090"):
        """
        初始化客戶端
        Args:
            prometheus_url (str): Prometheus 端點 URL
        """
        self.prometheus_url = prometheus_url.rstrip('/')
        self.available = self._test_connection()
        
        # 指標名稱映射（從您的配置映射到實際指標）
        self.metric_mapping = {}
        
        if self.available:
            print(f"✅ 成功連接到 {self.prometheus_url}")
            self._load_metric_mapping()
        else:
            print(f"❌ 無法連接到 {self.prometheus_url}")

    def _test_connection(self):
        """測試連接"""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/status/config", timeout=3)
            return response.status_code == 200
        except:
            return False

    def _load_metric_mapping(self):
        """載入指標映射"""
        try:
            # 獲取所有可用指標
            response = requests.get(f"{self.prometheus_url}/api/v1/label/__name__/values", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    all_metrics = data.get('data', [])
                    
                    # 建立映射關係
                    self._create_mapping(all_metrics)
        except Exception as e:
            print(f"載入指標映射時發生錯誤: {e}")

    def _create_mapping(self, all_metrics):
        """建立指標映射"""
        # 常見的映射模式
        mapping_patterns = {
            # 從您的配置檔案格式到可能的實際格式
            'right_aux2a_temp_pv': ['right_aux2a_temp_pv', 'Right_Aux2A_Temp_Pv', 'right_aux_2a_temp_pv'],
            'right_heater2a_temp': ['right_heater2a_temp', 'Right_Heater2A_Temp', 'right_heater_2a_temp'],
            'right_outlet_temp_inner_top': ['right_outlet_temp_inner_top', 'Right_Outlet_Temp_Inner_Top'],
            # 可以根據需要添加更多映射
        }
        
        for config_name, possible_names in mapping_patterns.items():
            for possible_name in possible_names:
                if possible_name in all_metrics:
                    self.metric_mapping[config_name] = possible_name
                    break
            
            # 如果沒有精確匹配，嘗試模糊匹配
            if config_name not in self.metric_mapping:
                keywords = config_name.split('_')
                for metric in all_metrics:
                    metric_lower = metric.lower()
                    if sum(1 for keyword in keywords if keyword in metric_lower) >= len(keywords) * 0.6:
                        self.metric_mapping[config_name] = metric
                        break

    def get_latest_data_for_metrics(self, metric_ids):
        """獲取指定指標的最新數據"""
        if not self.available:
            return {metric_id: None for metric_id in metric_ids}
        
        latest_data = {}
        
        for metric_id in metric_ids:
            # 嘗試直接查詢
            actual_metric = self.metric_mapping.get(metric_id, metric_id)
            
            value = self._query_single_metric(actual_metric)
            if value is None and actual_metric != metric_id:
                # 如果映射的指標沒有數據，嘗試原始名稱
                value = self._query_single_metric(metric_id)
            
            latest_data[metric_id] = value
            
            if value is not None:
                print(f"✅ {metric_id} -> {actual_metric}: {value}")
            else:
                print(f"❌ {metric_id}: 無數據")
        
        return latest_data

    def _query_single_metric(self, metric_name):
        """查詢單個指標"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': metric_name},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    result = data.get('data', {}).get('result', [])
                    if result:
                        return float(result[0]['value'][1])
            return None
        except:
            return None

    def query_range(self, query, start_time, end_time, step):
        """範圍查詢"""
        if not self.available:
            return []
        
        # 映射指標名稱
        actual_metric = query.split('{')[0] if '{' in query else query
        mapped_metric = self.metric_mapping.get(actual_metric, actual_metric)
        
        # 重建查詢
        if '{' in query:
            mapped_query = query.replace(actual_metric, mapped_metric)
        else:
            mapped_query = mapped_metric
        
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query_range",
                params={
                    'query': mapped_query,
                    'start': start_time,
                    'end': end_time,
                    'step': step
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data.get('data', {}).get('result', [])
            return []
        except:
            return []


if __name__ == "__main__":
    # 測試客戶端
    client = CorrectedPrometheusClient()
    
    if client.available:
        # 測試一些指標
        test_metrics = ['right_aux2a_temp_pv', 'right_heater2a_temp']
        data = client.get_latest_data_for_metrics(test_metrics)
        
        print("\\n測試結果:")
        for metric, value in data.items():
            print(f"  {metric}: {value}")
    else:
        print("客戶端連接失敗")
'''
    
    # 保存修正的客戶端
    with open("corrected_prometheus_client.py", "w", encoding="utf-8") as f:
        f.write(corrected_client_code)
    
    print("✅ 已建立修正的客戶端: corrected_prometheus_client.py")

def create_updated_dashboard():
    """建立更新的儀表板"""
    print("=== 建立更新的儀表板 ===\n")
    
    # 讀取現有的 working_dashboard.py 並修改
    try:
        with open("working_dashboard.py", "r", encoding="utf-8") as f:
            dashboard_code = f.read()
        
        # 替換客戶端匯入
        updated_code = dashboard_code.replace(
            "from metrics_only_client import MetricsOnlyPrometheusClient",
            "from corrected_prometheus_client import CorrectedPrometheusClient as MetricsOnlyPrometheusClient"
        )
        
        # 更新初始化
        updated_code = updated_code.replace(
            'MetricsOnlyPrometheusClient("http://sn.yesiang.com:9090/metrics")',
            'MetricsOnlyPrometheusClient("http://localhost:9090")'
        )
        
        # 保存更新的儀表板
        with open("updated_working_dashboard.py", "w", encoding="utf-8") as f:
            f.write(updated_code)
        
        print("✅ 已建立更新的儀表板: updated_working_dashboard.py")
        return True
        
    except Exception as e:
        print(f"❌ 更新儀表板時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    print("=== 修正數據存取問題 ===\n")
    
    # 測試指標存取
    working_endpoint, similar_metrics = test_metric_access()
    
    if working_endpoint and similar_metrics:
        print(f"🎉 找到工作的端點: {working_endpoint}")
        print(f"找到 {len(similar_metrics)} 個指標映射")
        
        # 建立修正的客戶端
        create_corrected_client()
        
        # 建立更新的儀表板
        if create_updated_dashboard():
            print(f"\n🚀 解決方案:")
            print("1. 測試修正的客戶端: python corrected_prometheus_client.py")
            print("2. 啟動更新的儀表板: python updated_working_dashboard.py")
            print("3. 或者手動修改 working_dashboard.py 中的端點 URL")
        
    else:
        print("❌ 未找到可用的指標映射")
        print("\n建議:")
        print("1. 檢查 Prometheus 服務狀態")
        print("2. 確認指標名稱格式")
        print("3. 檢查網路連接")

if __name__ == "__main__":
    main()