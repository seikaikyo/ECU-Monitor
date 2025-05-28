#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
快速測試特定 URL 的工具
專門用於測試 sn.yesiang.com:9090/metrics
"""

import requests
import time

def test_url(url):
    """測試特定 URL"""
    print(f"=== 測試 URL: {url} ===")
    
    try:
        print("發送請求...")
        response = requests.get(url, timeout=10)
        
        print(f"HTTP 狀態碼: {response.status_code}")
        print(f"回應大小: {len(response.text)} 字元")
        
        if response.status_code == 200:
            print("✅ 連線成功！")
            
            # 分析內容類型
            content = response.text
            
            if "# HELP" in content or "# TYPE" in content:
                print("✅ 這看起來是 Prometheus metrics 格式")
                
                # 解析指標
                lines = content.split('\n')
                metrics = set()
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if ' ' in line:
                            metric_part = line.split(' ')[0]
                            if '{' in metric_part:
                                metric_name = metric_part.split('{')[0]
                            else:
                                metric_name = metric_part
                            metrics.append(metric_name)
                
                unique_metrics = sorted(list(set(metrics)))
                print(f"找到 {len(unique_metrics)} 個指標")
                
                # 顯示前20個指標
                print("\n前20個指標:")
                for i, metric in enumerate(unique_metrics[:20]):
                    print(f"  {i+1}. {metric}")
                
                if len(unique_metrics) > 20:
                    print(f"  ... 還有 {len(unique_metrics) - 20} 個指標")
                
                # 搜尋可能相關的指標
                print(f"\n搜尋可能相關的指標:")
                relevant_patterns = ['temp', 'current', 'motor', 'pressure', 'flow', 'freq']
                
                for pattern in relevant_patterns:
                    matches = [m for m in unique_metrics if pattern.lower() in m.lower()]
                    if matches:
                        print(f"  {pattern.upper()} 相關: {len(matches)} 個")
                        for match in matches[:3]:  # 只顯示前3個
                            print(f"    - {match}")
                        if len(matches) > 3:
                            print(f"    ... 還有 {len(matches) - 3} 個")
                
                return unique_metrics
            
            elif "{" in content and "}" in content:
                print("✅ 這看起來是 JSON 格式")
                try:
                    import json
                    data = response.json()
                    print(f"JSON 結構: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                except:
                    print("⚠️ JSON 解析失敗")
                return []
            
            else:
                print("⚠️ 未知的內容格式")
                print(f"內容開頭: {content[:200]}...")
                return []
        
        else:
            print(f"❌ HTTP 錯誤: {response.status_code}")
            print(f"錯誤內容: {response.text[:200]}...")
            return []
    
    except requests.exceptions.ConnectionError:
        print("❌ 連線錯誤 - 無法連接到伺服器")
        return []
    except requests.exceptions.Timeout:
        print("❌ 連線逾時")
        return []
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        return []

def test_prometheus_api_endpoints(base_url):
    """測試 Prometheus API 端點"""
    print(f"\n=== 測試 Prometheus API 端點 ===")
    
    # 移除 /metrics 如果存在
    if base_url.endswith('/metrics'):
        base_url = base_url[:-8]
    
    api_endpoints = [
        ("/api/v1/query?query=up", "基本查詢"),
        ("/api/v1/label/__name__/values", "指標列表"),
        ("/api/v1/status/config", "狀態配置"),
        ("", "根目錄")
    ]
    
    for endpoint, description in api_endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\n測試 {description}: {url}")
        
        try:
            response = requests.get(url, timeout=5)
            print(f"狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ {description} 可用")
                if endpoint == "/api/v1/label/__name__/values":
                    try:
                        data = response.json()
                        if data.get('status') == 'success':
                            metrics = data.get('data', [])
                            print(f"  找到 {len(metrics)} 個指標")
                    except:
                        pass
            else:
                print(f"❌ {description} 不可用")
        except Exception as e:
            print(f"❌ {description} 測試失敗: {e}")

def main():
    """主函數"""
    print("=== 快速 URL 測試工具 ===\n")
    
    # 測試您提到的 URL
    test_urls = [
        "http://sn.yesiang.com:9090/metrics",
        "http://sn.yesiang.com:9090",
    ]
    
    for url in test_urls:
        metrics = test_url(url)
        
        if metrics:
            print(f"\n✅ URL {url} 可用，找到 {len(metrics)} 個指標")
            
            # 測試 API 端點
            test_prometheus_api_endpoints(url)
            
            # 儲存結果供其他程式使用
            print(f"\n=== 配置建議 ===")
            if url.endswith('/metrics'):
                base_url = url[:-8]
                print(f"建議在 prometheus_client.py 中使用基礎 URL: {base_url}")
                print(f"程式會自動添加 /api/v1/query 等路径")
            else:
                print(f"建議在 prometheus_client.py 中使用 URL: {url}")
            
            # 檢查是否有我們需要的指標
            from config_loader import load_plc_points
            plc_config = load_plc_points()
            
            if plc_config:
                print(f"\n=== 檢查配置指標 ===")
                config_metrics = []
                for group in plc_config['metric_groups']:
                    for metric in group['metrics']:
                        config_metrics.append(metric['id'])
                
                found_metrics = []
                for config_metric in config_metrics:
                    if config_metric in metrics:
                        found_metrics.append(config_metric)
                
                if found_metrics:
                    print(f"✅ 找到 {len(found_metrics)} 個配置中的指標:")
                    for metric in found_metrics[:10]:  # 只顯示前10個
                        print(f"  - {metric}")
                    if len(found_metrics) > 10:
                        print(f"  ... 還有 {len(found_metrics) - 10} 個")
                else:
                    print("❌ 沒有找到配置中的指標")
                    print("可能的原因:")
                    print("1. 指標名稱不匹配")
                    print("2. 數據還沒有被收集")
                    print("3. 配置文件中的指標ID需要調整")
            
            break  # 找到可用的 URL 就停止
        else:
            print(f"\n❌ URL {url} 不可用或沒有數據")
    
    print(f"\n=== 測試完成 ===")

if __name__ == "__main__":
    main()