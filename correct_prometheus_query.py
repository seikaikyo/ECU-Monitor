#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
正確的 Prometheus 查詢工具
使用與 Grafana 相同的方式查詢 Prometheus API
"""

import requests
import json
import time

def query_prometheus_api(prometheus_url, query_path="/api/v1/label/__name__/values"):
    """查詢 Prometheus API"""
    try:
        full_url = f"{prometheus_url}{query_path}"
        print(f"查詢 URL: {full_url}")
        
        response = requests.get(full_url, timeout=10)
        print(f"HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"回應狀態: {data.get('status', 'unknown')}")
            
            if data.get('status') == 'success':
                return data.get('data', [])
            else:
                print(f"API 錯誤: {data.get('error', 'unknown')}")
                return []
        else:
            print(f"HTTP 錯誤內容: {response.text[:200]}")
            return []
            
    except Exception as e:
        print(f"查詢時發生錯誤: {e}")
        return []

def test_multiple_endpoints():
    """測試多個可能的端點"""
    print("=== 測試多個 Prometheus 端點 ===\n")
    
    # 可能的 Prometheus 端點
    endpoints_to_test = [
        "http://sn.yesiang.com:9090",  # 您提供的端點
        "http://sn.yesiang.com:3001",  # Grafana 的端點，可能有 Prometheus
        "http://sn.yesiang.com:9091",  # 備用端口
        "http://sn.yesiang.com:8080",  # 其他可能的端口
    ]
    
    results = {}
    
    for base_url in endpoints_to_test:
        print(f"🔍 測試端點: {base_url}")
        
        # 測試 API 可用性
        try:
            response = requests.get(f"{base_url}/api/v1/status/config", timeout=5)
            if response.status_code == 200:
                print(f"✅ API 端點可用")
                
                # 獲取指標列表
                metrics = query_prometheus_api(base_url)
                if metrics:
                    print(f"✅ 找到 {len(metrics)} 個指標")
                    
                    # 尋找工業數據指標
                    industrial_metrics = []
                    industrial_keywords = [
                        'temp', 'motor', 'current', 'pressure', 'pv', 'sv', 'mv',
                        'left', 'right', 'main', 'aux', 'ecu', 'device',
                        'heater', 'fan', 'inlet', 'outlet', 'cda', 'hepa'
                    ]
                    
                    for metric in metrics:
                        for keyword in industrial_keywords:
                            if keyword.lower() in metric.lower():
                                industrial_metrics.append(metric)
                                break
                    
                    if industrial_metrics:
                        print(f"🏭 找到 {len(industrial_metrics)} 個可能的工業指標!")
                        print("前10個工業指標:")
                        for metric in industrial_metrics[:10]:
                            print(f"  • {metric}")
                        
                        results[base_url] = {
                            'total_metrics': len(metrics),
                            'industrial_metrics': industrial_metrics,
                            'all_metrics': metrics
                        }
                        
                        # 測試一個指標的實際數值
                        test_metric = industrial_metrics[0]
                        test_value = query_single_metric(base_url, test_metric)
                        if test_value is not None:
                            print(f"✅ 測試指標 {test_metric}: {test_value}")
                        
                        break  # 找到工業數據就停止
                    else:
                        print(f"❌ 未找到工業指標")
                else:
                    print(f"❌ 無法獲取指標列表")
            else:
                print(f"❌ API 不可用 (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ 連接失敗: {e}")
        
        print()
    
    return results

def query_single_metric(prometheus_url, metric_name):
    """查詢單個指標的值"""
    try:
        query_url = f"{prometheus_url}/api/v1/query"
        params = {'query': metric_name}
        
        response = requests.get(query_url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                result = data.get('data', {}).get('result', [])
                if result and len(result) > 0:
                    value = result[0].get('value', [None, None])[1]
                    return float(value) if value else None
        return None
    except:
        return None

def search_for_expected_metrics(prometheus_url, all_metrics):
    """搜尋期望的指標"""
    print(f"=== 搜尋期望的工業指標 ===\n")
    
    # 從 Grafana 截圖中看到的指標模式
    expected_patterns = [
        # 溫度相關
        'temp_pv', 'temp_sv', 'temperature', 
        # 馬達相關
        'motor', 'freq', 'current',
        # 壓力相關  
        'pressure', 'cda', 'hepa',
        # 位置相關
        'left', 'right', 'main', 'aux',
        # 設備相關
        'device1', 'device2', 'device3', 'device4',
        'ecu1051'
    ]
    
    found_matches = {}
    
    for pattern in expected_patterns:
        matches = [m for m in all_metrics if pattern.lower() in m.lower()]
        if matches:
            found_matches[pattern] = matches
    
    if found_matches:
        print("找到匹配的指標模式:")
        for pattern, matches in found_matches.items():
            print(f"\n{pattern.upper()} 相關 ({len(matches)} 個):")
            for match in matches[:8]:  # 顯示前8個
                print(f"  • {match}")
            if len(matches) > 8:
                print(f"  ... 還有 {len(matches) - 8} 個")
                
        # 測試一些指標的實際數值
        print(f"\n📊 測試指標數值:")
        test_metrics = []
        for matches in list(found_matches.values())[:3]:
            test_metrics.extend(matches[:2])
        
        for metric in test_metrics[:6]:
            value = query_single_metric(prometheus_url, metric)
            if value is not None:
                print(f"  ✅ {metric}: {value}")
            else:
                print(f"  ❌ {metric}: 無數據")
                
    else:
        print("❌ 未找到匹配的指標模式")
    
    return found_matches

def generate_working_config(found_matches, prometheus_url):
    """生成可用的配置檔案"""
    print(f"\n⚡ 生成可用的配置檔案...")
    
    if not found_matches:
        print("❌ 沒有找到工業指標，無法生成配置")
        return False
    
    # 建立配置
    config = {
        "metric_groups": []
    }
    
    # 按類別組織指標
    categories = {
        "溫度監控": ["temp", "temperature"],
        "馬達監控": ["motor", "freq", "current"],  
        "壓力監控": ["pressure", "cda", "hepa"],
        "設備狀態": ["device", "ecu", "left", "right"]
    }
    
    for category_name, keywords in categories.items():
        category_metrics = []
        
        for keyword in keywords:
            if keyword in found_matches:
                for metric in found_matches[keyword][:5]:  # 每類最多5個
                    if metric not in [m['id'] for m in category_metrics]:
                        # 生成友好名稱
                        friendly_name = metric.replace('_', ' ').title()
                        
                        # 推測單位
                        unit = ""
                        if any(t in metric.lower() for t in ['temp', 'temperature']):
                            unit = "℃"
                        elif any(t in metric.lower() for t in ['current', 'amp']):
                            unit = "A"
                        elif any(t in metric.lower() for t in ['freq', 'hz']):
                            unit = "Hz"
                        elif any(t in metric.lower() for t in ['pressure']):
                            unit = "Pa"
                        elif any(t in metric.lower() for t in ['voltage', 'volt']):
                            unit = "V"
                        
                        category_metrics.append({
                            "id": metric,
                            "name": friendly_name,
                            "unit": unit
                        })
        
        if category_metrics:
            config["metric_groups"].append({
                "group_name": category_name,
                "device_id": len(config["metric_groups"]) + 1,
                "metrics": category_metrics
            })
    
    if config["metric_groups"]:
        # 保存配置
        with open("working_plc_points.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        total_metrics = sum(len(group["metrics"]) for group in config["metric_groups"])
        print(f"✅ 已生成工作配置: working_plc_points.json")
        print(f"包含 {len(config['metric_groups'])} 個組別，{total_metrics} 個指標")
        
        print(f"\n🚀 立即使用:")
        print("1. cp working_plc_points.json plc_points.json")
        print("2. python working_dashboard.py")
        
        return True
    
    return False

def main():
    """主函數"""
    print("=== 正確的 Prometheus 查詢工具 ===\n")
    
    # 測試多個端點
    results = test_multiple_endpoints()
    
    if results:
        # 使用第一個成功的端點
        working_endpoint = list(results.keys())[0]
        working_data = results[working_endpoint]
        
        print(f"🎉 找到工作的端點: {working_endpoint}")
        print(f"總指標: {working_data['total_metrics']} 個")
        print(f"工業指標: {len(working_data['industrial_metrics'])} 個")
        
        # 搜尋期望的指標
        found_matches = search_for_expected_metrics(
            working_endpoint, 
            working_data['all_metrics']
        )
        
        # 生成配置
        if generate_working_config(found_matches, working_endpoint):
            print(f"\n✅ 成功！現在您可以使用真實的 ECU-1051 數據了！")
        else:
            print(f"\n⚠️ 雖然找到了數據，但無法自動生成配置")
            print("請手動檢查找到的指標")
            
    else:
        print("❌ 未找到任何可用的 Prometheus 端點")
        print("建議檢查:")
        print("1. Prometheus 服務狀態")
        print("2. 網路連接")  
        print("3. 端口配置")

if __name__ == "__main__":
    main()