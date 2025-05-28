#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
設備連線檢查工具
檢查 PLC/Modbus 設備的網路連線狀況
"""

import socket
import time
import requests
from config_loader import load_devices

def ping_host(host, port, timeout=3):
    """檢查主機和端口的連通性"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except socket.gaierror:
        return False
    except Exception:
        return False

def check_modbus_connectivity():
    """檢查 Modbus 設備連線"""
    print("=== Modbus 設備連線檢查 ===\n")
    
    devices = load_devices()
    if not devices:
        print("❌ 無法載入設備配置")
        return []
    
    connectivity_results = []
    
    for device in devices['devices']:
        device_id = device['id']
        device_name = device['name']
        primary_ip = device['primary_ip']
        backup_ip = device.get('backup_ip')
        port = device.get('port', 502)
        
        print(f"🔍 檢查設備: {device_name} ({device_id})")
        
        # 檢查主要 IP
        primary_ok = ping_host(primary_ip, port)
        print(f"  主要 IP {primary_ip}:{port} - {'✅ 連通' if primary_ok else '❌ 無法連通'}")
        
        # 檢查備用 IP
        backup_ok = False
        if backup_ip:
            backup_ok = ping_host(backup_ip, port)
            print(f"  備用 IP {backup_ip}:{port} - {'✅ 連通' if backup_ok else '❌ 無法連通'}")
        
        connectivity_results.append({
            'device_id': device_id,
            'device_name': device_name,
            'primary_ip': primary_ip,
            'backup_ip': backup_ip,
            'port': port,
            'primary_connected': primary_ok,
            'backup_connected': backup_ok,
            'any_connected': primary_ok or backup_ok
        })
        
        print()
    
    return connectivity_results

def check_modbus_exporter_service():
    """檢查 Modbus Exporter 服務"""
    print("=== Modbus Exporter 服務檢查 ===\n")
    
    # 常見的 Modbus Exporter 端口
    common_ports = [9602, 9564, 8080, 8081, 9090]
    localhost_ips = ['127.0.0.1', 'localhost', '10.6.35.90']
    
    found_services = []
    
    for ip in localhost_ips:
        for port in common_ports:
            try:
                # 嘗試 HTTP 連接
                response = requests.get(f"http://{ip}:{port}/metrics", timeout=2)
                if response.status_code == 200:
                    content = response.text
                    if 'modbus' in content.lower() or any(keyword in content.lower() 
                                                        for keyword in ['temp_pv', 'motor_', 'current_']):
                        print(f"✅ 找到 Modbus Exporter: http://{ip}:{port}/metrics")
                        found_services.append(f"http://{ip}:{port}")
                        
                        # 分析指標
                        lines = content.split('\n')
                        modbus_metrics = [line.split(' ')[0] for line in lines 
                                        if line and not line.startswith('#') and ' ' in line]
                        
                        print(f"   找到 {len(modbus_metrics)} 個指標")
                        
                        # 顯示一些範例指標
                        sample_metrics = [m for m in modbus_metrics if any(keyword in m.lower() 
                                        for keyword in ['temp', 'motor', 'current'])][:5]
                        
                        if sample_metrics:
                            print("   範例指標:")
                            for metric in sample_metrics:
                                print(f"     • {metric}")
                        
                        return found_services
                
            except requests.exceptions.RequestException:
                continue
            except Exception:
                continue
    
    print("❌ 未找到 Modbus Exporter 服務")
    print("\n可能的位置:")
    print("• http://localhost:9602/metrics")
    print("• http://localhost:9564/metrics") 
    print("• http://10.6.35.90:9602/metrics")
    
    return found_services

def check_prometheus_scrape_config():
    """檢查 Prometheus 抓取配置"""
    print("\n=== Prometheus 抓取配置檢查 ===\n")
    
    try:
        response = requests.get("http://sn.yesiang.com:9090/api/v1/status/config", timeout=5)
        if response.status_code == 200:
            config_data = response.json()
            if config_data['status'] == 'success':
                config_yaml = config_data['data']['yaml']
                
                print("✅ 成功獲取 Prometheus 配置")
                
                # 檢查是否有工業數據相關的 job
                industrial_keywords = ['modbus', 'plc', 'industrial', 'device', 'sensor']
                
                has_industrial_job = any(keyword in config_yaml.lower() for keyword in industrial_keywords)
                
                if has_industrial_job:
                    print("✅ 配置中包含工業數據相關的 job")
                else:
                    print("❌ 配置中未找到工業數據相關的 job")
                
                # 解析 scrape_configs
                if 'scrape_configs:' in config_yaml:
                    print("\n📋 抓取配置概要:")
                    lines = config_yaml.split('\n')
                    in_scrape_configs = False
                    current_job = None
                    
                    for line in lines:
                        line = line.strip()
                        if line.startswith('scrape_configs:'):
                            in_scrape_configs = True
                            continue
                        
                        if in_scrape_configs:
                            if line.startswith('- job_name:'):
                                current_job = line.split(':')[1].strip().strip('"\'')
                                targets_info = "未知"
                                print(f"  • Job: {current_job}")
                            elif line.startswith('static_configs:') or line.startswith('targets:'):
                                continue
                            elif '- targets:' in line or 'targets:' in line:
                                continue
                            elif line.startswith('- ') and ':' in line and current_job:
                                target = line.replace('- ', '').strip().strip('"\'')
                                if target and '.' in target:  # 看起來像 IP:port
                                    print(f"    目標: {target}")
                
                return True
            else:
                print(f"❌ API 錯誤: {config_data}")
        else:
            print(f"❌ HTTP 錯誤: {response.status_code}")
    except Exception as e:
        print(f"❌ 檢查配置時發生錯誤: {e}")
    
    return False

def generate_setup_recommendations(connectivity_results, found_services):
    """生成設置建議"""
    print("\n=== 設置建議 ===\n")
    
    connected_devices = [r for r in connectivity_results if r['any_connected']]
    disconnected_devices = [r for r in connectivity_results if not r['any_connected']]
    
    if not connected_devices:
        print("❌ 所有設備都無法連通")
        print("\n立即行動項目:")
        print("1. 檢查網路連線")
        print("2. 確認設備電源狀態")
        print("3. 檢查防火牆設置")
        print("4. 確認 IP 地址配置")
        return
    
    if not found_services:
        print("❌ 未找到 Modbus Exporter 服務")
        print("\n需要安裝和配置 Modbus Exporter:")
        print("1. 下載 Modbus Exporter")
        print("2. 創建配置檔案 modbus.yml")
        print("3. 啟動服務: ./modbus_exporter --config.file=modbus.yml")
        print("4. 在 Prometheus 中添加抓取配置")
        
        # 生成範例配置
        print("\n📄 範例 modbus.yml 配置:")
        print("```yaml")
        print("modules:")
        print("  default:")
        print("    protocol: tcp")
        print("    timeout: 1s")
        print("    retries: 3")
        print("    registers:")
        
        for device in connected_devices[:1]:  # 只顯示第一個設備的範例
            print(f"      # {device['device_name']}")
            print(f"      - name: left_main_temp_pv")
            print(f"        address: 40001")
            print(f"        type: holding")
            print(f"        format: int16")
            print(f"        scale: 0.1")
        
        print("```")
        
        print("\n📄 範例 Prometheus 配置:")
        print("```yaml")
        print("scrape_configs:")
        print("  - job_name: 'modbus-exporter'")
        print("    static_configs:")
        print("      - targets:")
        
        for device in connected_devices:
            ip = device['primary_ip'] if device['primary_connected'] else device['backup_ip']
            print(f"        - '{ip}:502'")
        
        print("    metrics_path: /probe")
        print("    params:")
        print("      module: [default]")
        print("    relabel_configs:")
        print("      - source_labels: [__address__]")
        print("        target_label: __param_target")
        print("      - source_labels: [__param_target]")
        print("        target_label: instance")
        print("      - target_label: __address__")
        print("        replacement: localhost:9602")
        print("```")
    
    else:
        print("✅ 找到 Modbus Exporter 服務")
        print("檢查 Prometheus 是否正確配置以抓取這些服務")

def main():
    """主函數"""
    print("=== 設備連線診斷工具 ===\n")
    
    # 檢查設備連線
    connectivity_results = check_modbus_connectivity()
    
    # 檢查 Modbus Exporter
    found_services = check_modbus_exporter_service()
    
    # 檢查 Prometheus 配置
    prometheus_config_ok = check_prometheus_scrape_config()
    
    # 生成建議
    generate_setup_recommendations(connectivity_results, found_services)
    
    print(f"\n=== 診斷總結 ===")
    connected_count = sum(1 for r in connectivity_results if r['any_connected'])
    print(f"設備連線: {connected_count}/{len(connectivity_results)} 台設備可連通")
    print(f"Modbus Exporter: {'✅ 已找到' if found_services else '❌ 未找到'}")
    print(f"Prometheus 配置: {'✅ 可訪問' if prometheus_config_ok else '❌ 無法訪問'}")

if __name__ == "__main__":
    main()