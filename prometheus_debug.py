#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Prometheus 連線除錯工具
用於檢查 Prometheus 連線狀況和可用指標
"""

import requests
import json
import time
from config_loader import load_plc_points

def test_prometheus_connection(prometheus_url="http://sn.yesiang.com:9090"):
    """測試 Prometheus 連線"""
    print(f"=== 測試 Prometheus 連線 ===")
    print(f"目標 URL: {prometheus_url}")
    
    try:
        # 測試基本連線
        response = requests.get(f"{prometheus_url}/api/v1/status/config", timeout=5)
        if response.status_code == 200:
            print("✅ Prometheus 伺服器連線成功")
            return True
        else:
            print(f"❌ Prometheus 伺服器回應異常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 無法連線到 Prometheus 伺服器")
        return False
    except requests.exceptions.Timeout:
        print("❌ 連線 Prometheus 伺服器逾時")
        return False
    except Exception as e:
        print(f"❌ 連線測試時發生錯誤: {e}")
        return False

def get_available_metrics(prometheus_url="http://sn.yesiang.com:9090"):
    """獲取 Prometheus 中可用的指標列表"""
    print(f"\n=== 獲取可用指標 ===")
    
    try:
        response = requests.get(f"{prometheus_url}/api/v1/label/__name__/values", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                metrics = data['data']
                print(f"✅ 找到 {len(metrics)} 個指標")
                return metrics
            else:
                print(f"❌ API 回應錯誤: {data}")
                return []
        else:
            print(f"❌ HTTP 錯誤: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 獲取指標時發生錯誤: {e}")
        return []

def search_metrics_by_pattern(metrics, pattern):
    """根據模式搜尋指標"""
    matching = [m for m in metrics if pattern.lower() in m.lower()]
    return matching

def test_specific_metrics(prometheus_url="http://sn.yesiang.com:9090"):
    """測試特定指標的查詢"""
    print(f"\n=== 測試指標查詢 ===")
    
    # 載入配置中的指標
    plc_config = load_plc_points()
    if not plc_config:
        print("❌ 無法載入 PLC 配置")
        return
    
    test_metrics = []
    for group in plc_config['metric_groups']:
        for metric in group['metrics'][:3]:  # 只測試前3個指標
            test_metrics.append(metric['id'])
    
    print(f"測試指標: {test_metrics}")
    
    for metric_id in test_metrics:
        try:
            response = requests.get(
                f"{prometheus_url}/api/v1/query",
                params={'query': metric_id},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success' and data['data']['result']:
                    print(f"✅ {metric_id}: 有數據")
                    # 顯示最新值
                    result = data['data']['result'][0]
                    value = result['value'][1]
                    print(f"   最新值: {value}")
                else:
                    print(f"⚠️ {metric_id}: 查詢成功但無數據")
            else:
                print(f"❌ {metric_id}: HTTP 錯誤 {response.status_code}")
        except Exception as e:
            print(f"❌ {metric_id}: 查詢錯誤 - {e}")

def suggest_alternative_metrics(available_metrics):
    """建議可能的替代指標"""
    print(f"\n=== 建議的指標 ===")
    
    # 常見的工業監控指標模式
    patterns = [
        'temp', 'temperature', '溫度',
        'current', '電流', 'amp',
        'voltage', '電壓', 'volt',
        'pressure', '壓力',
        'flow', '流量',
        'frequency', '頻率', 'freq',
        'power', '功率',
        'motor', '馬達',
        'fan', '風扇'
    ]
    
    suggestions = {}
    for pattern in patterns:
        matches = search_metrics_by_pattern(available_metrics, pattern)
        if matches:
            suggestions[pattern] = matches[:5]  # 限制每個模式最多5個建議
    
    if suggestions:
        print("找到以下可能相關的指標:")
        for pattern, metrics in suggestions.items():
            print(f"\n{pattern.upper()} 相關:")
            for metric in metrics:
                print(f"  - {metric}")
    else:
        print("未找到明顯相關的指標")

def create_test_data_source():
    """建立測試數據源"""
    print(f"\n=== 建立測試數據源 ===")
    
    # 建立一個簡單的測試 Prometheus 查詢
    test_data = {
        'left_main_temp_pv': 25.5,
        'left_aux1a_temp_pv': 30.2,
        'left_aux1a_ct': 12.8,
        'right_main_temp_pv': 28.1,
        'right_aux1a_temp_pv': 31.5,
        'right_aux1a_ct': 11.9
    }
    
    print("建議的測試數據:")
    for metric, value in test_data.items():
        print(f"  {metric}: {value}")
    
    return test_data

def main():
    """主函數"""
    print("=== Prometheus 除錯工具 ===\n")
    
    prometheus_url = "http://sn.yesiang.com:9090"
    
    # 1. 測試連線
    if not test_prometheus_connection(prometheus_url):
        print("\n建議:")
        print("1. 檢查 Prometheus 伺服器是否運行")
        print("2. 檢查網路連線")
        print("3. 確認 URL 是否正確")
        print("4. 嘗試在瀏覽器中開啟: http://sn.yesiang.com:9090")
        return
    
    # 2. 獲取可用指標
    available_metrics = get_available_metrics(prometheus_url)
    if not available_metrics:
        print("無法獲取指標列表")
        return
    
    # 3. 顯示前20個指標作為範例
    print(f"\n前20個可用指標:")
    for i, metric in enumerate(available_metrics[:20]):
        print(f"  {i+1}. {metric}")
    if len(available_metrics) > 20:
        print(f"  ... 還有 {len(available_metrics) - 20} 個指標")
    
    # 4. 測試配置中的指標
    test_specific_metrics(prometheus_url)
    
    # 5. 建議替代指標
    suggest_alternative_metrics(available_metrics)
    
    # 6. 建立測試數據
    test_data = create_test_data_source()
    
    print(f"\n=== 總結 ===")
    print(f"Prometheus 伺服器: {'✅ 正常' if available_metrics else '❌ 異常'}")
    print(f"可用指標數量: {len(available_metrics)}")
    print(f"建議: 檢查指標名稱是否與配置檔案中的 ID 匹配")

if __name__ == "__main__":
    main()