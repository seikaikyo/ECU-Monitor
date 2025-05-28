#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Docker Prometheus 查詢工具
嘗試連接正確的 Prometheus 實例
"""

import requests
import json
import socket

def resolve_prometheus_endpoint():
    """解析 Prometheus 端點"""
    print("=== 解析 Prometheus 端點 ===\n")
    
    # 可能的端點列表
    possible_endpoints = [
        "http://prometheus:9090",           # Docker 內部主機名
        "http://localhost:9090",            # 本地端口映射
        "http://127.0.0.1:9090",           # 本地 IP
        "http://sn.yesiang.com:9090",      # 之前嘗試的端點
        "http://10.6.35.90:9090",          # 您的本機 IP
        "http://172.17.0.1:9090",          # Docker 網橋 IP
        "http://192.168.1.1:9090",         # 常見的內網 IP
    ]
    
    working_endpoints = []
    
    for endpoint in possible_endpoints:
        print(f"🔍 測試端點: {endpoint}")
        
        try:
            # 測試連接
            response = requests.get(f"{endpoint}/api/v1/status/config", timeout=3)
            if response.status_code == 200:
                print(f"✅ 連接成功!")
                
                # 測試獲取指標
                metrics_response = requests.get(f"{endpoint}/api/v1/label/__name__/values", timeout=5)
                if metrics_response.status_code == 200:
                    metrics_data = metrics_response.json()
                    if metrics_data.get('status') == 'success':
                        metrics = metrics_data.get('data', [])
                        print(f"✅ 找到 {len(metrics)} 個指標")
                        
                        # 檢查是否有工業數據
                        industrial_count = sum(1 for m in metrics if any(keyword in m.lower() 
                                             for keyword in ['temp', 'motor', 'current', 'pressure', 'device']))
                        
                        if industrial_count > 0:
                            print(f"🏭 找到 {industrial_count} 個可能的工業指標!")
                            working_endpoints.append({
                                'url': endpoint,
                                'total_metrics': len(metrics),
                                'industrial_metrics': industrial_count,
                                'all_metrics': metrics
                            })
                        else:
                            print(f"⚠️ 只有系統指標，沒有工業數據")
                    else:
                        print(f"❌ 指標 API 錯誤")
                else:
                    print(f"❌ 無法獲取指標列表")
            else:
                print(f"❌ 連接失敗 (HTTP {response.status_code})")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ 連接被拒絕")
        except requests.exceptions.Timeout:
            print(f"❌ 連接逾時")
        except Exception as e:
            print(f"❌ 其他錯誤: {e}")
        
        print()
    
    return working_endpoints

def check_docker_network():
    """檢查 Docker 網路設定"""
    print("=== 檢查 Docker 網路設定 ===\n")
    
    try:
        # 嘗試解析 prometheus 主機名
        prometheus_ip = socket.gethostbyname('prometheus')
        print(f"✅ 解析到 prometheus 主機: {prometheus_ip}")
        
        # 嘗試連接
        endpoint = f"http://{prometheus_ip}:9090"
        response = requests.get(f"{endpoint}/api/v1/status/config", timeout=3)
        if response.status_code == 200:
            print(f"✅ 可以連接到 {endpoint}")
            return endpoint
        else:
            print(f"❌ 無法連接到 {endpoint}")
            
    except socket.gaierror:
        print("❌ 無法解析 prometheus 主機名")
    except Exception as e:
        print(f"❌ 檢查 Docker 網路時發生錯誤: {e}")
    
    return None

def analyze_industrial_metrics(endpoint, all_metrics):
    """分析工業指標"""
    print(f"=== 分析工業指標 ===\n")
    print(f"使用端點: {endpoint}")
    
    # 工業指標關鍵字 (根據您的 Grafana 截圖)
    industrial_keywords = {
        '溫度': ['temp', 'temperature'],
        '馬達': ['motor', 'freq'],  
        '電流': ['current', 'amp'],
        '壓力': ['pressure', 'cda', 'hepa'],
        '設備': ['device', 'ecu', 'left', 'right', 'main', 'aux'],
        '控制': ['pv', 'sv', 'mv', 'ct']
    }
    
    found_categories = {}
    
    for category, keywords in industrial_keywords.items():
        matches = []
        for metric in all_metrics:
            for keyword in keywords:
                if keyword.lower() in metric.lower():
                    matches.append(metric)
                    break
        
        if matches:
            found_categories[category] = list(set(matches))  # 去重
    
    if found_categories:
        print("找到的工業指標分類:")
        total_industrial = 0
        
        for category, metrics in found_categories.items():
            print(f"\n📊 {category} ({len(metrics)} 個):")
            for metric in metrics[:8]:  # 每類顯示前8個
                print(f"  • {metric}")
            if len(metrics) > 8:
                print(f"  ... 還有 {len(metrics) - 8} 個")
            total_industrial += len(metrics)
        
        print(f"\n🎉 總計找到 {total_industrial} 個工業指標!")
        
        # 測試一些指標的實際數值
        print(f"\n📊 測試指標數值:")
        test_metrics = []
        for metrics in list(found_categories.values())[:3]:
            test_metrics.extend(metrics[:2])
        
        for metric in test_metrics[:6]:
            value = query_single_metric(endpoint, metric)
            if value is not None:
                print(f"  ✅ {metric}: {value}")
            else:
                print(f"  ❌ {metric}: 無數據")
        
        return found_categories
    else:
        print("❌ 未找到工業指標")
        return {}

def query_single_metric(endpoint, metric_name):
    """查詢單個指標的值"""
    try:
        response = requests.get(f"{endpoint}/api/v1/query", 
                              params={'query': metric_name}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                result = data.get('data', {}).get('result', [])
                if result:
                    return float(result[0]['value'][1])
        return None
    except:
        return None

def generate_correct_config(found_categories, endpoint):
    """生成正確的配置檔案"""
    print(f"\n⚡ 生成正確的配置檔案...")
    
    if not found_categories:
        print("❌ 沒有工業指標可用")
        return False
    
    config = {
        "metric_groups": []
    }
    
    # 根據找到的分類建立配置
    device_id = 1
    for category, metrics in found_categories.items():
        if metrics:  # 確保有指標
            group_metrics = []
            
            for metric in metrics[:10]:  # 每組最多10個指標
                # 生成友好的名稱
                friendly_name = metric.replace('_', ' ').title()
                
                # 根據指標名稱推測單位
                unit = ""
                if any(keyword in metric.lower() for keyword in ['temp', 'temperature']):
                    unit = "℃"
                elif any(keyword in metric.lower() for keyword in ['current', 'amp']):
                    unit = "A"
                elif any(keyword in metric.lower() for keyword in ['freq', 'frequency']):
                    unit = "Hz"
                elif any(keyword in metric.lower() for keyword in ['pressure']):
                    unit = "Pa"
                elif any(keyword in metric.lower() for keyword in ['voltage', 'volt']):
                    unit = "V"
                elif any(keyword in metric.lower() for keyword in ['power']):
                    unit = "W"
                
                group_metrics.append({
                    "id": metric,
                    "name": friendly_name,
                    "unit": unit
                })
            
            if group_metrics:
                config["metric_groups"].append({
                    "group_name": f"{category}監控",
                    "device_id": device_id,
                    "metrics": group_metrics
                })
                device_id += 1
    
    if config["metric_groups"]:
        # 保存配置
        with open("correct_plc_points.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        total_metrics = sum(len(group["metrics"]) for group in config["metric_groups"])
        print(f"✅ 已生成正確配置: correct_plc_points.json")
        print(f"包含 {len(config['metric_groups'])} 個組別，{total_metrics} 個指標")
        
        # 同時更新客戶端配置以使用正確的端點
        client_config = {
            "prometheus_url": endpoint,
            "note": "這是正確的 Prometheus 端點"
        }
        
        with open("prometheus_config.json", "w", encoding="utf-8") as f:
            json.dump(client_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已保存端點配置: prometheus_config.json")
        
        print(f"\n🚀 使用方法:")
        print("1. cp correct_plc_points.json plc_points.json")
        print("2. 修改 working_dashboard.py 使用正確的端點")
        print("3. python working_dashboard.py")
        
        return True
    
    return False

def main():
    """主函數"""
    print("=== Docker Prometheus 查詢工具 ===\n")
    
    # 檢查 Docker 網路
    docker_endpoint = check_docker_network()
    
    # 解析所有可能的端點
    working_endpoints = resolve_prometheus_endpoint()
    
    if working_endpoints:
        # 使用第一個有工業數據的端點
        best_endpoint = working_endpoints[0]
        endpoint_url = best_endpoint['url']
        
        print(f"🎉 找到最佳端點: {endpoint_url}")
        print(f"總指標: {best_endpoint['total_metrics']}")
        print(f"工業指標: {best_endpoint['industrial_metrics']}")
        
        # 深度分析工業指標
        found_categories = analyze_industrial_metrics(
            endpoint_url, 
            best_endpoint['all_metrics']
        )
        
        # 生成配置
        if generate_correct_config(found_categories, endpoint_url):
            print(f"\n✅ 成功找到您的 ECU-1051 數據!")
            print(f"端點: {endpoint_url}")
        else:
            print(f"\n⚠️ 找到數據但無法生成配置")
            
    else:
        print("❌ 未找到任何可用的 Prometheus 端點")
        print("\n可能的解決方案:")
        print("1. 檢查 Docker 容器狀態")
        print("2. 檢查端口映射")
        print("3. 嘗試從 Docker 容器內部連接")

if __name__ == "__main__":
    main()