#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
尋找相關指標工具
幫助您找到 Prometheus 中實際可用的指標
"""

from metrics_only_client import MetricsOnlyPrometheusClient
from config_loader import load_plc_points

def analyze_available_metrics():
    """分析可用指標"""
    print("=== 分析可用指標 ===\n")
    
    client = MetricsOnlyPrometheusClient("http://sn.yesiang.com:9090/metrics")
    
    if not client.available:
        print("❌ 無法連接到 Prometheus")
        return
    
    # 獲取所有可用指標
    available_metrics = client.get_available_metrics()
    print(f"✅ 找到 {len(available_metrics)} 個可用指標\n")
    
    # 分類指標
    categories = {
        '系統相關': ['go_', 'process_', 'net_'],
        'HTTP相關': ['http_', 'promhttp_'],
        'Prometheus相關': ['prometheus_'],
        '資料庫相關': ['tsdb_'],
        '監控相關': ['up', 'scrape_'],
        '其他': []
    }
    
    categorized_metrics = {cat: [] for cat in categories.keys()}
    
    for metric in available_metrics:
        categorized = False
        for category, prefixes in categories.items():
            if any(metric.startswith(prefix) for prefix in prefixes):
                categorized_metrics[category].append(metric)
                categorized = True
                break
        if not categorized:
            categorized_metrics['其他'].append(metric)
    
    # 顯示分類結果
    for category, metrics in categorized_metrics.items():
        if metrics:
            print(f"📊 {category} ({len(metrics)} 個):")
            for metric in metrics[:10]:  # 只顯示前10個
                print(f"  - {metric}")
            if len(metrics) > 10:
                print(f"  ... 還有 {len(metrics) - 10} 個")
            print()
    
    return available_metrics

def find_industrial_metrics(available_metrics):
    """尋找可能的工業監控指標"""
    print("=== 尋找工業監控相關指標 ===\n")
    
    # 工業監控常見關鍵字
    industrial_keywords = [
        'temp', 'temperature', '溫度',
        'current', '電流', 'amp', 'ampere',
        'voltage', '電壓', 'volt',
        'pressure', '壓力', 'press',
        'flow', '流量', 'rate',
        'frequency', '頻率', 'freq', 'hz',
        'power', '功率', 'watt',
        'motor', '馬達', 'engine',
        'pump', '泵', 'fan', '風扇',
        'valve', '閥', 'actuator',
        'sensor', '感測器',
        'control', '控制',
        'plc', 'scada', 'hmi',
        'alarm', '警報', 'alert',
        'status', '狀態', 'state'
    ]
    
    found_industrial = {}
    
    for keyword in industrial_keywords:
        matches = [m for m in available_metrics if keyword.lower() in m.lower()]
        if matches:
            found_industrial[keyword] = matches
    
    if found_industrial:
        print("找到可能的工業監控指標:")
        for keyword, metrics in found_industrial.items():
            print(f"\n🔍 {keyword.upper()} 相關 ({len(metrics)} 個):")
            for metric in metrics[:5]:
                print(f"  - {metric}")
            if len(metrics) > 5:
                print(f"  ... 還有 {len(metrics) - 5} 個")
    else:
        print("❌ 未找到明顯的工業監控指標")
        print("這可能是一個標準的 Prometheus 系統監控實例")
    
    return found_industrial

def suggest_alternative_config(available_metrics):
    """建議替代配置"""
    print("\n=== 建議的替代配置 ===\n")
    
    # 選擇一些有趣的系統指標作為監控對象
    suggested_metrics = []
    
    # CPU 相關
    cpu_metrics = [m for m in available_metrics if 'cpu' in m.lower()]
    if cpu_metrics:
        suggested_metrics.extend(cpu_metrics[:2])
    
    # 記憶體相關
    memory_metrics = [m for m in available_metrics if any(keyword in m.lower() for keyword in ['memory', 'heap', 'alloc'])]
    if memory_metrics:
        suggested_metrics.extend(memory_metrics[:2])
    
    # 網路相關
    network_metrics = [m for m in available_metrics if any(keyword in m.lower() for keyword in ['net', 'http', 'request'])]
    if network_metrics:
        suggested_metrics.extend(network_metrics[:2])
    
    # GC 相關
    gc_metrics = [m for m in available_metrics if 'gc' in m.lower()]
    if gc_metrics:
        suggested_metrics.extend(gc_metrics[:2])
    
    # 其他有趣的指標
    interesting_patterns = ['up', 'duration', 'total', 'rate', 'size', 'count']
    for pattern in interesting_patterns:
        matches = [m for m in available_metrics if pattern in m.lower() and m not in suggested_metrics]
        if matches:
            suggested_metrics.append(matches[0])
    
    # 限制數量
    suggested_metrics = suggested_metrics[:12]
    
    if suggested_metrics:
        print("建議的監控指標配置:")
        print("```json")
        print('{')
        print('  "metric_groups": [')
        print('    {')
        print('      "group_name": "系統監控",')
        print('      "metrics": [')
        
        for i, metric in enumerate(suggested_metrics):
            # 生成友好的名稱
            name = metric.replace('_', ' ').title()
            unit = ""
            
            if 'bytes' in metric:
                unit = "bytes"
            elif 'seconds' in metric:
                unit = "秒"
            elif 'total' in metric:
                unit = "次"
            elif 'percent' in metric:
                unit = "%"
            
            print(f'        {{')
            print(f'          "id": "{metric}",')
            print(f'          "name": "{name}",')
            print(f'          "unit": "{unit}"')
            print(f'        }}{"," if i < len(suggested_metrics)-1 else ""}')
        
        print('      ]')
        print('    }')
        print('  ]')
        print('}')
        print("```")
        
        print(f"\n這些指標都在您的 Prometheus 中可用，可以立即監控。")
    
    return suggested_metrics

def test_suggested_metrics(client, suggested_metrics):
    """測試建議的指標"""
    print("\n=== 測試建議的指標 ===\n")
    
    if not suggested_metrics:
        print("沒有建議的指標可供測試")
        return
    
    # 測試前5個指標
    test_metrics = suggested_metrics[:5]
    print(f"測試指標: {test_metrics}")
    
    latest_data = client.get_latest_data_for_metrics(test_metrics)
    
    print("\n測試結果:")
    for metric_id, value in latest_data.items():
        if value is not None:
            print(f"✅ {metric_id}: {value}")
        else:
            print(f"❌ {metric_id}: 無數據")

def main():
    """主函數"""
    print("=== Prometheus 指標分析工具 ===\n")
    
    # 分析可用指標
    available_metrics = analyze_available_metrics()
    
    if not available_metrics:
        return
    
    # 尋找工業監控指標
    industrial_metrics = find_industrial_metrics(available_metrics)
    
    # 建議替代配置
    suggested_metrics = suggest_alternative_config(available_metrics)
    
    # 測試建議的指標
    if suggested_metrics:
        client = MetricsOnlyPrometheusClient("http://sn.yesiang.com:9090/metrics")
        test_suggested_metrics(client, suggested_metrics)
    
    print("\n=== 總結 ===")
    print(f"• 總共找到 {len(available_metrics)} 個可用指標")
    print(f"• 工業監控相關: {len(industrial_metrics)} 個類別")
    print(f"• 建議監控指標: {len(suggested_metrics)} 個")
    print("\n建議:")
    print("1. 如果這是工業設備監控系統，可能需要檢查數據採集器配置")
    print("2. 如果只是系統監控，可以使用建議的指標進行監控")
    print("3. 可以將建議的配置保存為新的 plc_points.json 檔案")

if __name__ == "__main__":
    main()