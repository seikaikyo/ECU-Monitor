#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Prometheus 原始數據分析
直接分析 /metrics 端點的原始內容，尋找 ECU-1051 的 Modbus 數據
"""

import requests
import re
import json

def fetch_raw_metrics():
    """獲取原始 metrics 數據"""
    print("=== 獲取 Prometheus 原始數據 ===\n")
    
    try:
        response = requests.get("http://sn.yesiang.com:9090/metrics", timeout=15)
        if response.status_code == 200:
            content = response.text
            print(f"✅ 成功獲取數據，大小: {len(content)} 字元")
            return content
        else:
            print(f"❌ HTTP 錯誤: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 獲取數據時發生錯誤: {e}")
        return None

def analyze_raw_content(content):
    """分析原始內容"""
    print("=== 分析原始內容 ===\n")
    
    lines = content.split('\n')
    
    # 統計信息
    total_lines = len(lines)
    help_lines = [line for line in lines if line.startswith('# HELP')]
    type_lines = [line for line in lines if line.startswith('# TYPE')]
    metric_lines = [line for line in lines if line and not line.startswith('#')]
    
    print(f"📊 內容統計:")
    print(f"  • 總行數: {total_lines}")
    print(f"  • HELP 行: {len(help_lines)}")
    print(f"  • TYPE 行: {len(type_lines)}")
    print(f"  • 指標數據行: {len(metric_lines)}")
    
    return help_lines, type_lines, metric_lines

def extract_metric_info(help_lines, type_lines, metric_lines):
    """提取指標資訊"""
    print(f"\n=== 提取指標資訊 ===\n")
    
    # 解析 HELP 信息
    help_info = {}
    for line in help_lines:
        match = re.match(r'# HELP (\S+) (.+)', line)
        if match:
            metric_name, description = match.groups()
            help_info[metric_name] = description
    
    # 解析 TYPE 信息
    type_info = {}
    for line in type_lines:
        match = re.match(r'# TYPE (\S+) (\S+)', line)
        if match:
            metric_name, metric_type = match.groups()
            type_info[metric_name] = metric_type
    
    # 解析指標數據
    metric_data = {}
    for line in metric_lines:
        if ' ' in line:
            parts = line.split(' ', 1)
            if len(parts) == 2:
                metric_part, value_part = parts
                
                # 提取指標名稱和標籤
                if '{' in metric_part:
                    metric_name = metric_part.split('{')[0]
                    labels = metric_part[metric_part.find('{'):]
                else:
                    metric_name = metric_part
                    labels = ""
                
                try:
                    value = float(value_part.strip())
                    
                    if metric_name not in metric_data:
                        metric_data[metric_name] = []
                    
                    metric_data[metric_name].append({
                        'labels': labels,
                        'value': value,
                        'raw_line': line
                    })
                except ValueError:
                    continue
    
    print(f"解析結果:")
    print(f"  • 有描述的指標: {len(help_info)}")
    print(f"  • 有類型的指標: {len(type_info)}")
    print(f"  • 有數據的指標: {len(metric_data)}")
    
    return help_info, type_info, metric_data

def search_for_industrial_data(help_info, type_info, metric_data):
    """搜尋工業數據相關指標"""
    print(f"\n=== 搜尋工業數據 ===\n")
    
    # 工業數據相關關鍵字
    industrial_keywords = [
        # ECU/設備相關
        'ecu', 'modbus', 'plc', 'hmi', 'device',
        # 溫度相關
        'temp', 'temperature', 'thermal', 'heat',
        # 電氣相關
        'current', 'voltage', 'power', 'motor', 'amp', 'volt',
        # 機械相關
        'pressure', 'flow', 'frequency', 'speed', 'rpm',
        # 控制相關
        'control', 'set', 'actual', 'pv', 'sv', 'mv',
        # 位置相關
        'left', 'right', 'main', 'aux', 'inlet', 'outlet',
        # 數字標識
        '1051', '4000', '3000'
    ]
    
    found_industrial = {}
    
    # 搜尋指標名稱
    for keyword in industrial_keywords:
        matches = []
        
        for metric_name in metric_data.keys():
            if keyword.lower() in metric_name.lower():
                matches.append(metric_name)
        
        if matches:
            found_industrial[keyword] = matches
    
    # 搜尋描述
    description_matches = {}
    for keyword in industrial_keywords:
        matches = []
        
        for metric_name, description in help_info.items():
            if keyword.lower() in description.lower():
                matches.append((metric_name, description))
        
        if matches:
            description_matches[keyword] = matches
    
    print(f"🔍 按指標名稱搜尋結果:")
    if found_industrial:
        for keyword, metrics in found_industrial.items():
            print(f"  {keyword.upper()}: {len(metrics)} 個")
            for metric in metrics[:3]:
                print(f"    • {metric}")
            if len(metrics) > 3:
                print(f"    ... 還有 {len(metrics) - 3} 個")
    else:
        print("  ❌ 未找到明顯的工業數據指標")
    
    print(f"\n🔍 按描述搜尋結果:")
    if description_matches:
        for keyword, matches in description_matches.items():
            print(f"  {keyword.upper()}: {len(matches)} 個")
            for metric_name, description in matches[:3]:
                print(f"    • {metric_name}: {description}")
    else:
        print("  ❌ 未在描述中找到工業數據關鍵字")
    
    return found_industrial, description_matches

def analyze_metric_values(metric_data, found_industrial):
    """分析指標數值"""
    print(f"\n=== 分析指標數值 ===\n")
    
    # 收集所有可能的工業指標
    all_industrial_metrics = set()
    for metrics_list in found_industrial.values():
        all_industrial_metrics.update(metrics_list)
    
    if not all_industrial_metrics:
        print("沒有找到工業指標，分析所有指標的數值範圍")
        # 分析前20個指標
        sample_metrics = list(metric_data.keys())[:20]
    else:
        print(f"分析 {len(all_industrial_metrics)} 個可能的工業指標")
        sample_metrics = list(all_industrial_metrics)[:15]
    
    print(f"指標數值分析:")
    for metric_name in sample_metrics:
        if metric_name in metric_data:
            values = [item['value'] for item in metric_data[metric_name]]
            
            if values:
                min_val = min(values)
                max_val = max(values)
                avg_val = sum(values) / len(values)
                
                print(f"  • {metric_name}:")
                print(f"    數值範圍: {min_val:.2f} ~ {max_val:.2f} (平均: {avg_val:.2f})")
                print(f"    數據點: {len(values)} 個")
                
                # 顯示一些實際數值
                if len(values) <= 3:
                    print(f"    實際值: {[v for v in values]}")
                else:
                    print(f"    實際值範例: {values[:3]}")
    
    return sample_metrics

def generate_mapping_suggestions(found_industrial, metric_data):
    """生成映射建議"""
    print(f"\n=== 生成映射建議 ===\n")
    
    # 載入期望的指標
    try:
        from config_loader import load_plc_points
        plc_config = load_plc_points()
        
        if plc_config:
            expected_metrics = {}
            for group in plc_config['metric_groups']:
                for metric in group['metrics']:
                    expected_metrics[metric['id']] = {
                        'name': metric['name'],
                        'unit': metric['unit'],
                        'register_offset': metric.get('register_offset')
                    }
            
            print(f"期望指標: {len(expected_metrics)} 個")
            
            # 嘗試建立映射
            possible_mappings = []
            
            # 收集所有找到的工業指標
            all_found_metrics = set()
            for metrics_list in found_industrial.values():
                all_found_metrics.update(metrics_list)
            
            if all_found_metrics:
                print(f"找到的可能工業指標: {len(all_found_metrics)} 個")
                
                # 生成建議的配置
                suggested_config = {
                    "metric_groups": [
                        {
                            "group_name": "發現的工業指標",
                            "device_id": 1,
                            "metrics": []
                        }
                    ]
                }
                
                for metric_name in list(all_found_metrics)[:20]:  # 限制20個
                    # 生成友好名稱
                    friendly_name = metric_name.replace('_', ' ').title()
                    
                    # 猜測單位
                    unit = ""
                    if any(keyword in metric_name.lower() for keyword in ['temp', 'temperature']):
                        unit = "℃"
                    elif any(keyword in metric_name.lower() for keyword in ['current', 'amp']):
                        unit = "A"
                    elif any(keyword in metric_name.lower() for keyword in ['voltage', 'volt']):
                        unit = "V"
                    elif any(keyword in metric_name.lower() for keyword in ['power']):
                        unit = "W"
                    elif any(keyword in metric_name.lower() for keyword in ['pressure']):
                        unit = "Pa"
                    elif any(keyword in metric_name.lower() for keyword in ['freq', 'hz']):
                        unit = "Hz"
                    
                    suggested_config["metric_groups"][0]["metrics"].append({
                        "id": metric_name,
                        "name": friendly_name,
                        "unit": unit
                    })
                
                # 保存配置
                with open("discovered_metrics.json", "w", encoding="utf-8") as f:
                    json.dump(suggested_config, f, indent=2, ensure_ascii=False)
                
                print(f"✅ 已生成發現的指標配置: discovered_metrics.json")
                
            else:
                print("❌ 未找到明顯的工業指標")
                print("可能的原因:")
                print("1. Modbus Exporter 未正確配置指標名稱")
                print("2. ECU-1051 數據未正確匯出到 Prometheus")
                print("3. 指標使用了不同的命名規則")
        
    except ImportError:
        print("❌ 無法載入配置檔案")

def main():
    """主函數"""
    print("=== ECU-1051 Prometheus 原始數據分析 ===\n")
    
    # 獲取原始數據
    raw_content = fetch_raw_metrics()
    if not raw_content:
        return
    
    # 分析內容結構
    help_lines, type_lines, metric_lines = analyze_raw_content(raw_content)
    
    # 提取指標資訊
    help_info, type_info, metric_data = extract_metric_info(help_lines, type_lines, metric_lines)
    
    # 搜尋工業數據
    found_industrial, description_matches = search_for_industrial_data(help_info, type_info, metric_data)
    
    # 分析數值
    sample_metrics = analyze_metric_values(metric_data, found_industrial)
    
    # 生成映射建議
    generate_mapping_suggestions(found_industrial, metric_data)
    
    print(f"\n=== 分析完成 ===")
    total_found = sum(len(metrics) for metrics in found_industrial.values())
    print(f"發現可能的工業指標: {total_found} 個")
    
    if total_found > 0:
        print("✅ 建議使用 discovered_metrics.json 配置")
        print("執行: cp discovered_metrics.json plc_points.json")
    else:
        print("❌ 未發現明顯的工業指標，可能需要檢查 Modbus Exporter 配置")

if __name__ == "__main__":
    main()