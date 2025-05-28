#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
尋找 Modbus 指標工具
分析 Prometheus 中的實際指標，找出哪些是來自 ECU-1051 的 Modbus 數據
"""

import requests
import json
import re
from metrics_only_client import MetricsOnlyPrometheusClient
from config_loader import load_plc_points


def analyze_prometheus_metrics():
    """分析 Prometheus 中的所有指標"""
    print("=== 分析 Prometheus 指標 ===\n")

    client = MetricsOnlyPrometheusClient("http://sn.yesiang.com:9090/metrics")
    if not client.available:
        print("❌ 無法連接到 Prometheus")
        return []

    all_metrics = client.get_available_metrics()
    print(f"總共找到 {len(all_metrics)} 個指標")

    # 分析指標來源
    metric_categories = {
        'Go語言系統指標': [],
        'Prometheus內部指標': [],
        'HTTP/網路指標': [],
        '可能的Modbus指標': [],
        '未分類指標': []
    }

    for metric in all_metrics:
        if metric.startswith('go_'):
            metric_categories['Go語言系統指標'].append(metric)
        elif metric.startswith('prometheus_'):
            metric_categories['Prometheus內部指標'].append(metric)
        elif any(keyword in metric.lower()
                 for keyword in ['http', 'net_', 'promhttp']):
            metric_categories['HTTP/網路指標'].append(metric)
        elif any(keyword in metric.lower() for keyword in [
                'modbus', 'ecu', 'temp', 'motor', 'current', 'voltage',
                'pressure'
        ]):
            metric_categories['可能的Modbus指標'].append(metric)
        else:
            metric_categories['未分類指標'].append(metric)

    print(f"\n📊 指標分類:")
    for category, metrics in metric_categories.items():
        print(f"  • {category}: {len(metrics)} 個")
        if category == '可能的Modbus指標' and metrics:
            print("    範例指標:")
            for metric in metrics[:5]:
                print(f"      - {metric}")

    return all_metrics, metric_categories


def search_for_ecu_metrics(all_metrics):
    """搜尋可能來自 ECU-1051 的指標"""
    print(f"\n🔍 搜尋 ECU-1051 相關指標...")

    # ECU/Modbus 相關關鍵字
    ecu_keywords = [
        'ecu', 'modbus', 'plc', 'hmi', 'temp', 'temperature', 'motor',
        'current', 'voltage', 'power', 'pressure', 'flow', 'frequency',
        'speed', 'control', 'left', 'right', 'main', 'aux', 'heater', 'fan',
        'inlet', 'outlet', 'pv', 'sv', 'mv', 'ct'
    ]

    potential_ecu_metrics = {}

    for keyword in ecu_keywords:
        matches = [m for m in all_metrics if keyword.lower() in m.lower()]
        if matches:
            potential_ecu_metrics[keyword] = matches

    if potential_ecu_metrics:
        print("找到可能的 ECU 指標:")
        for keyword, metrics in potential_ecu_metrics.items():
            print(f"\n{keyword.upper()} 相關 ({len(metrics)} 個):")
            for metric in metrics[:10]:  # 限制顯示數量
                print(f"  • {metric}")
            if len(metrics) > 10:
                print(f"  ... 還有 {len(metrics) - 10} 個")
    else:
        print("❌ 未找到明顯的 ECU 相關指標")

    return potential_ecu_metrics


def analyze_metric_patterns(all_metrics):
    """分析指標命名模式"""
    print(f"\n🔍 分析指標命名模式...")

    # 尋找可能的設備或實例標識
    device_patterns = []

    for metric in all_metrics:
        # 尋找包含數字的指標（可能表示設備編號）
        if re.search(r'\d+', metric):
            device_patterns.append(metric)

    if device_patterns:
        print(f"包含數字的指標 ({len(device_patterns)} 個):")
        for metric in device_patterns[:15]:
            print(f"  • {metric}")
        if len(device_patterns) > 15:
            print(f"  ... 還有 {len(device_patterns) - 15} 個")

    # 尋找可能的 Modbus 寄存器模式
    register_patterns = []
    for metric in all_metrics:
        if any(pattern in metric.lower() for pattern in
               ['4000', '3000', 'holding', 'input', 'register']):
            register_patterns.append(metric)

    if register_patterns:
        print(f"\n可能的寄存器相關指標:")
        for metric in register_patterns:
            print(f"  • {metric}")

    return device_patterns, register_patterns


def get_sample_values(client, metrics_list):
    """獲取指標的實際數值"""
    print(f"\n📊 獲取指標實際數值...")

    if not metrics_list:
        print("沒有指標可供測試")
        return {}

    # 取前10個指標進行測試
    test_metrics = metrics_list[:10]

    values = client.get_latest_data_for_metrics(test_metrics)

    print("指標數值範例:")
    for metric, value in values.items():
        if value is not None:
            print(f"  • {metric}: {value}")
        else:
            print(f"  • {metric}: 無數據")

    return values


def create_metric_mapping(potential_ecu_metrics, expected_metrics):
    """建立指標映射"""
    print(f"\n🔗 建立指標映射...")

    # 載入期望的指標
    plc_config = load_plc_points()
    if not plc_config:
        print("❌ 無法載入 PLC 配置")
        return {}

    expected_mapping = {}
    for group in plc_config['metric_groups']:
        for metric in group['metrics']:
            expected_mapping[metric['id']] = {
                'name': metric['name'],
                'unit': metric['unit'],
                'register_offset': metric.get('register_offset', 0)
            }

    print(f"期望的指標: {len(expected_mapping)} 個")

    # 尋找可能的映射
    possible_mappings = {}

    # 集合所有可能的 ECU 指標
    all_ecu_candidates = []
    for metrics_list in potential_ecu_metrics.values():
        all_ecu_candidates.extend(metrics_list)

    # 去重
    all_ecu_candidates = list(set(all_ecu_candidates))

    print(f"可能的 ECU 指標候選: {len(all_ecu_candidates)} 個")

    # 嘗試關鍵字匹配
    for expected_id, expected_info in expected_mapping.items():
        # 提取關鍵字
        keywords = expected_id.split('_')

        # 尋找包含這些關鍵字的指標
        matches = []
        for candidate in all_ecu_candidates:
            score = sum(1 for keyword in keywords
                        if keyword in candidate.lower())
            if score > 0:
                matches.append((candidate, score))

        # 按得分排序
        matches.sort(key=lambda x: x[1], reverse=True)

        if matches:
            possible_mappings[expected_id] = {
                'expected_name': expected_info['name'],
                'candidates': matches[:3]  # 只保留前3個候選
            }

    if possible_mappings:
        print(f"\n可能的指標映射:")
        for expected_id, mapping_info in list(possible_mappings.items())[:10]:
            print(f"  期望: {expected_id} ({mapping_info['expected_name']})")
            print(f"  候選:")
            for candidate, score in mapping_info['candidates']:
                print(f"    • {candidate} (得分: {score})")
            print()
    else:
        print("❌ 未找到明顯的指標映射")

    return possible_mappings


def generate_updated_config(all_metrics, potential_ecu_metrics):
    """生成更新的配置檔案"""
    print(f"\n⚡ 生成更新的配置檔案...")

    # 選擇最有可能的指標
    selected_metrics = []

    # 從各個類別中選擇指標
    for category, metrics in potential_ecu_metrics.items():
        if category in ['temp', 'motor', 'current', 'voltage', 'pressure']:
            selected_metrics.extend(metrics[:5])  # 每類取前5個

    # 如果沒找到明顯的ECU指標，就用一些系統指標作為替代
    if not selected_metrics:
        print("未找到明顯的 ECU 指標，使用系統指標作為替代")
        system_metrics = [
            m for m in all_metrics
            if any(keyword in m.lower()
                   for keyword in ['up', 'cpu', 'memory', 'duration', 'total'])
        ][:15]
        selected_metrics = system_metrics

    # 去重並限制數量
    selected_metrics = list(set(selected_metrics))[:20]

    if selected_metrics:
        updated_config = {
            "metric_groups": [{
                "group_name": "實際可用指標",
                "device_id": 1,
                "metrics": []
            }]
        }

        for metric in selected_metrics:
            # 生成友好的名稱
            friendly_name = metric.replace('_', ' ').title()

            # 猜測單位
            unit = ""
            if any(keyword in metric.lower()
                   for keyword in ['temp', 'temperature']):
                unit = "℃"
            elif any(keyword in metric.lower()
                     for keyword in ['current', 'amp']):
                unit = "A"
            elif any(keyword in metric.lower()
                     for keyword in ['voltage', 'volt']):
                unit = "V"
            elif any(keyword in metric.lower()
                     for keyword in ['frequency', 'freq', 'hz']):
                unit = "Hz"
            elif any(keyword in metric.lower() for keyword in ['pressure']):
                unit = "Pa"
            elif any(keyword in metric.lower() for keyword in ['power']):
                unit = "W"
            elif any(keyword in metric.lower() for keyword in ['bytes']):
                unit = "bytes"
            elif any(keyword in metric.lower()
                     for keyword in ['seconds', 'duration']):
                unit = "秒"
            elif any(keyword in metric.lower()
                     for keyword in ['total', 'count']):
                unit = "次"

            updated_config["metric_groups"][0]["metrics"].append({
                "id": metric,
                "name": friendly_name,
                "unit": unit
            })

        # 保存配置
        with open("updated_plc_points.json", "w", encoding="utf-8") as f:
            json.dump(updated_config, f, indent=2, ensure_ascii=False)

        print(f"✅ 已生成更新的配置檔案: updated_plc_points.json")
        print(f"包含 {len(selected_metrics)} 個實際可用的指標")

        print(f"\n使用方法:")
        print("1. 備份原配置: cp plc_points.json plc_points.json.backup")
        print("2. 使用新配置: cp updated_plc_points.json plc_points.json")
        print("3. 重啟儀表板: python working_dashboard.py")

        return updated_config

    return None


def main():
    """主函數"""
    print("=== ECU-1051 Modbus 指標分析工具 ===\n")

    # 分析所有指標
    all_metrics, metric_categories = analyze_prometheus_metrics()

    # 搜尋 ECU 相關指標
    potential_ecu_metrics = search_for_ecu_metrics(all_metrics)

    # 分析指標模式
    device_patterns, register_patterns = analyze_metric_patterns(all_metrics)

    # 獲取樣本數值
    client = MetricsOnlyPrometheusClient("http://sn.yesiang.com:9090/metrics")

    if potential_ecu_metrics:
        # 從最有希望的類別中取樣本
        sample_metrics = []
        for metrics_list in list(potential_ecu_metrics.values())[:3]:
            sample_metrics.extend(metrics_list[:3])

        if sample_metrics:
            get_sample_values(client, sample_metrics)

    # 建立指標映射
    expected_metrics = []
    plc_config = load_plc_points()
    if plc_config:
        for group in plc_config['metric_groups']:
            expected_metrics.extend([m['id'] for m in group['metrics']])

    possible_mappings = create_metric_mapping(potential_ecu_metrics,
                                              expected_metrics)

    # 生成更新的配置
    updated_config = generate_updated_config(all_metrics,
                                             potential_ecu_metrics)

    print(f"\n=== 分析總結 ===")
    print(f"• 總指標數: {len(all_metrics)}")
    print(
        f"• 可能的ECU指標: {sum(len(metrics) for metrics in potential_ecu_metrics.values())}"
    )
    print(f"• 期望的工業指標: {len(expected_metrics)}")
    print(f"• 可能的映射: {len(possible_mappings)}")

    if updated_config:
        print(f"• ✅ 已生成可用的配置檔案")
    else:
        print(f"• ❌ 無法生成映射配置")
        print(f"  建議：檢查 Modbus Exporter 是否正確配置")


if __name__ == "__main__":
    main()
