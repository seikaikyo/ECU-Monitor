#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工業數據診斷工具
幫助診斷為什麼 Prometheus 中沒有工業設備數據
"""

import requests
import json
from config_loader import load_plc_points, load_devices
from metrics_only_client import MetricsOnlyPrometheusClient

def analyze_missing_industrial_data():
    """分析缺失的工業數據"""
    print("=== 工業數據診斷工具 ===\n")
    
    # 載入配置
    plc_config = load_plc_points()
    device_config = load_devices()
    
    if not plc_config or not device_config:
        print("❌ 無法載入配置檔案")
        return
    
    # 分析期望的指標
    expected_metrics = []
    metric_categories = {}
    
    for group in plc_config['metric_groups']:
        group_name = group['group_name']
        metric_categories[group_name] = []
        
        for metric in group['metrics']:
            expected_metrics.append(metric['id'])
            metric_categories[group_name].append({
                'id': metric['id'],
                'name': metric['name'],
                'unit': metric['unit']
            })
    
    print(f"📊 期望的工業指標分析:")
    print(f"總計: {len(expected_metrics)} 個指標")
    for category, metrics in metric_categories.items():
        print(f"  • {category}: {len(metrics)} 個")
    
    # 檢查 Prometheus 中的可用指標
    print(f"\n🔍 檢查 Prometheus 中的實際指標...")
    
    client = MetricsOnlyPrometheusClient("http://sn.yesiang.com:9090/metrics")
    if not client.available:
        print("❌ 無法連接到 Prometheus")
        return
    
    available_metrics = client.get_available_metrics()
    print(f"找到 {len(available_metrics)} 個可用指標")
    
    # 檢查匹配情況
    found_industrial = []
    missing_industrial = []
    
    for expected in expected_metrics:
        if expected in available_metrics:
            found_industrial.append(expected)
        else:
            missing_industrial.append(expected)
    
    print(f"\n📈 匹配結果:")
    print(f"✅ 找到的工業指標: {len(found_industrial)} 個")
    print(f"❌ 缺失的工業指標: {len(missing_industrial)} 個")
    
    if found_industrial:
        print(f"\n找到的工業指標:")
        for metric in found_industrial[:10]:
            print(f"  ✅ {metric}")
        if len(found_industrial) > 10:
            print(f"  ... 還有 {len(found_industrial) - 10} 個")
    
    if missing_industrial:
        print(f"\n缺失的工業指標 (前10個):")
        for metric in missing_industrial[:10]:
            # 找到對應的友好名稱
            for group in plc_config['metric_groups']:
                for m in group['metrics']:
                    if m['id'] == metric:
                        print(f"  ❌ {metric} ({m['name']})")
                        break
        if len(missing_industrial) > 10:
            print(f"  ... 還有 {len(missing_industrial) - 10} 個")
    
    return found_industrial, missing_industrial, available_metrics

def search_for_similar_metrics(missing_metrics, available_metrics):
    """搜尋相似的指標"""
    print(f"\n🔍 搜尋相似指標...")
    
    # 提取關鍵字
    keywords = set()
    for metric in missing_metrics:
        parts = metric.replace('_', ' ').split()
        keywords.update(parts)
    
    # 常見的工業監控關鍵字
    industrial_keywords = [
        'temp', 'temperature', 'motor', 'current', 'voltage', 'power',
        'pressure', 'flow', 'freq', 'frequency', 'speed', 'control',
        'left', 'right', 'main', 'aux', 'heater', 'fan', 'pump',
        'inlet', 'outlet', 'ct', 'mv', 'pv', 'sv'
    ]
    
    similar_metrics = {}
    
    for keyword in industrial_keywords:
        matches = [m for m in available_metrics if keyword.lower() in m.lower()]
        if matches:
            similar_metrics[keyword] = matches
    
    if similar_metrics:
        print("找到可能相關的指標:")
        for keyword, metrics in similar_metrics.items():
            print(f"\n{keyword.upper()} 相關:")
            for metric in metrics[:3]:
                print(f"  • {metric}")
            if len(metrics) > 3:
                print(f"  ... 還有 {len(metrics) - 3} 個")
    else:
        print("❌ 未找到相似的工業監控指標")
    
    return similar_metrics

def check_prometheus_targets():
    """檢查 Prometheus 目標"""
    print(f"\n🎯 檢查 Prometheus 抓取目標...")
    
    prometheus_base_url = "http://sn.yesiang.com:9090"
    
    try:
        # 檢查目標狀態
        response = requests.get(f"{prometheus_base_url}/api/v1/targets", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                targets = data['data']['activeTargets']
                print(f"找到 {len(targets)} 個抓取目標:")
                
                for target in targets:
                    job = target.get('labels', {}).get('job', 'unknown')
                    instance = target.get('labels', {}).get('instance', 'unknown') 
                    health = target.get('health', 'unknown')
                    last_error = target.get('lastError', '')
                    
                    status_icon = "✅" if health == 'up' else "❌"
                    print(f"  {status_icon} Job: {job}, Instance: {instance}, Health: {health}")
                    
                    if last_error:
                        print(f"      錯誤: {last_error}")
                
                # 檢查是否有工業數據相關的 job
                industrial_jobs = [t for t in targets if any(keyword in t.get('labels', {}).get('job', '').lower() 
                                                           for keyword in ['modbus', 'plc', 'industrial', 'device', 'sensor'])]
                
                if industrial_jobs:
                    print(f"\n🏭 找到工業數據相關的抓取目標:")
                    for job in industrial_jobs:
                        job_name = job.get('labels', {}).get('job', 'unknown')
                        health = job.get('health', 'unknown')
                        print(f"  • {job_name}: {health}")
                else:
                    print(f"\n⚠️ 未找到工業數據相關的抓取目標")
                    print("可能的原因:")
                    print("  1. Modbus Exporter 未啟動")
                    print("  2. Prometheus 配置中未添加工業數據源")
                    print("  3. 工業數據採集器使用了不同的 job 名稱")
                
                return targets
            else:
                print(f"❌ API 錯誤: {data}")
        else:
            print(f"❌ HTTP 錯誤: {response.status_code}")
    except Exception as e:
        print(f"❌ 檢查目標時發生錯誤: {e}")
    
    return None

def generate_troubleshooting_guide(found_industrial, missing_industrial):
    """生成故障排除指南"""
    print(f"\n🛠️ 故障排除指南")
    print("=" * 50)
    
    if len(found_industrial) == 0:
        print("❌ 完全沒有工業數據")
        print("\n可能的原因和解決方案:")
        print("\n1. 數據採集器未運行")
        print("   • 檢查 Modbus Exporter 或類似工具是否啟動")
        print("   • 檢查設備 IP 連線狀況")
        print("   • 確認 Modbus 通訊參數正確")
        
        print("\n2. Prometheus 配置問題")
        print("   • 檢查 prometheus.yml 中是否配置了工業數據源")
        print("   • 確認 scrape_configs 中的 job 配置")
        print("   • 檢查目標端點是否可達")
        
        print("\n3. 網路連線問題") 
        print("   • 檢查設備 IP 是否可達")
        print("   • 確認防火牆設置")
        print("   • 檢查 Modbus TCP 端口 (通常是 502)")
        
    elif len(found_industrial) < len(missing_industrial) / 2:
        print("⚠️ 部分工業數據缺失")
        print("\n可能的原因:")
        print("   • 部分設備離線或故障")
        print("   • 配置檔案中的指標 ID 與實際不匹配")
        print("   • 數據採集器配置不完整")
        
    else:
        print("✅ 大部分工業數據正常")
        print("   • 只有少數指標缺失，可能是特定設備問題")
    
    print(f"\n📋 建議的檢查步驟:")
    print("1. 執行: python check_device_connectivity.py")
    print("2. 檢查 Prometheus 配置檔案")
    print("3. 檢查 Modbus Exporter 日誌")
    print("4. 測試設備連線")
    print("5. 重啟數據採集服務")

def create_temporary_config(available_metrics):
    """建立臨時配置使用可用指標"""
    print(f"\n⚡ 建立臨時配置方案")
    
    # 從可用指標中挑選有用的
    useful_metrics = []
    
    # 系統狀態指標
    system_metrics = [m for m in available_metrics if any(keyword in m.lower() 
                     for keyword in ['up', 'cpu', 'memory', 'heap', 'gc'])][:5]
    
    # HTTP/網路指標
    network_metrics = [m for m in available_metrics if any(keyword in m.lower() 
                      for keyword in ['http', 'request', 'duration'])][:3]
    
    # Prometheus 內部指標
    prometheus_metrics = [m for m in available_metrics if 'prometheus' in m.lower()][:3]
    
    temp_config = {
        "metric_groups": [
            {
                "group_name": "系統監控 (臨時)",
                "metrics": [{"id": m, "name": m.replace('_', ' ').title(), "unit": ""} 
                           for m in system_metrics]
            },
            {
                "group_name": "網路監控 (臨時)", 
                "metrics": [{"id": m, "name": m.replace('_', ' ').title(), "unit": ""} 
                           for m in network_metrics]
            },
            {
                "group_name": "Prometheus 監控 (臨時)",
                "metrics": [{"id": m, "name": m.replace('_', ' ').title(), "unit": ""} 
                           for m in prometheus_metrics]
            }
        ]
    }
    
    print("建立臨時配置檔案: temp_plc_points.json")
    with open("temp_plc_points.json", "w", encoding="utf-8") as f:
        json.dump(temp_config, f, indent=2, ensure_ascii=False)
    
    print("您可以使用這個臨時配置來測試儀表板功能")
    print("執行: cp temp_plc_points.json plc_points.json")

def main():
    """主函數"""
    found_industrial, missing_industrial, available_metrics = analyze_missing_industrial_data()
    
    if found_industrial:
        print(f"\n🎉 好消息！找到了 {len(found_industrial)} 個工業指標")
    else:
        print(f"\n😟 未找到任何工業指標")
        
        # 搜尋相似指標
        search_for_similar_metrics(missing_industrial[:20], available_metrics)
        
        # 檢查 Prometheus 目標
        check_prometheus_targets()
        
        # 生成故障排除指南
        generate_troubleshooting_guide(found_industrial, missing_industrial)
        
        # 建立臨時配置
        create_temporary_config(available_metrics)
        
        print(f"\n💡 立即可行的解決方案:")
        print("1. 使用臨時配置測試儀表板: cp temp_plc_points.json plc_points.json")
        print("2. 重新啟動儀表板: python working_dashboard.py")
        print("3. 同時排查工業數據採集問題")

if __name__ == "__main__":
    main()