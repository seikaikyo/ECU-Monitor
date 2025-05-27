# update_plc_config.py - PLC 配置更新工具
import json
from pathlib import Path


def create_enhanced_plc_config():
    """創建增強版 PLC 配置"""

    config = {
        "system_info": {
            "name": "智慧烘箱監控系統",
            "version": "1.0.0",
            "description": "整合 PLC 數據讀取、AI 異常檢測和 Web 界面的完整監控解決方案",
            "created_date": "2024-01-01",
            "last_updated": "2024-12-19"
        },
        "connection_settings": {
            "default_host": "192.168.1.100",
            "default_port": 502,
            "timeout": 10,
            "retry_attempts": 3,
            "retry_delay": 2
        },
        "metric_groups": [
            {
                "group_name":
                "溫度控制器",
                "group_id":
                "temperature_controllers",
                "device_id":
                1,
                "start_address":
                40001,
                "count":
                78,
                "description":
                "主要溫度控制相關參數",
                "priority":
                "high",
                "metrics": [{
                    "id": "left_main_temp_pv",
                    "name": "左側主控_PV",
                    "register_offset": 0,
                    "data_type": "INT16",
                    "scale_factor": 10.0,
                    "unit": "℃",
                    "description": "左側主控制器當前溫度值",
                    "normal_range": [150, 200],
                    "critical_range": [100, 250],
                    "alert_enabled": True
                }, {
                    "id": "left_main_temp_sv",
                    "name": "左側主控_SV",
                    "register_offset": 1,
                    "data_type": "INT16",
                    "scale_factor": 10.0,
                    "unit": "℃",
                    "description": "左側主控制器設定溫度值",
                    "normal_range": [150, 200],
                    "critical_range": [100, 250],
                    "alert_enabled": True
                }, {
                    "id": "right_main_temp_pv",
                    "name": "右側主控_PV",
                    "register_offset": 14,
                    "data_type": "INT16",
                    "scale_factor": 10.0,
                    "unit": "℃",
                    "description": "右側主控制器當前溫度值",
                    "normal_range": [150, 200],
                    "critical_range": [100, 250],
                    "alert_enabled": True
                }, {
                    "id": "right_main_temp_sv",
                    "name": "右側主控_SV",
                    "register_offset": 15,
                    "data_type": "INT16",
                    "scale_factor": 10.0,
                    "unit": "℃",
                    "description": "右側主控制器設定溫度值",
                    "normal_range": [150, 200],
                    "critical_range": [100, 250],
                    "alert_enabled": True
                }
                            # 繼續添加其他溫度相關指標...
                            ]
            },
            {
                "group_name":
                "馬達和壓力",
                "group_id":
                "motors_and_pressure",
                "device_id":
                2,
                "start_address":
                40001,
                "count":
                25,
                "description":
                "馬達頻率、電流和系統壓力參數",
                "priority":
                "medium",
                "metrics": [{
                    "id": "motor_freq_left_1a",
                    "name": "左側馬達頻率-1A",
                    "register_offset": 0,
                    "data_type": "INT16",
                    "scale_factor": 100.0,
                    "unit": "Hz",
                    "description": "左側1A馬達運行頻率",
                    "normal_range": [45, 55],
                    "critical_range": [30, 70],
                    "alert_enabled": True
                }, {
                    "id": "motor_current_left_1a",
                    "name": "左側馬達電流-1A",
                    "register_offset": 9,
                    "data_type": "INT16",
                    "scale_factor": 10.0,
                    "unit": "A",
                    "description": "左側1A馬達電流",
                    "normal_range": [10, 40],
                    "critical_range": [5, 60],
                    "alert_enabled": True
                }]
            },
            {
                "group_name":
                "電表數據",
                "group_id":
                "power_meter",
                "device_id":
                3,
                "start_address":
                40001,
                "count":
                26,
                "description":
                "電力系統相關參數",
                "priority":
                "high",
                "metrics": [{
                    "id": "voltage_avg",
                    "name": "電壓(平均值)",
                    "register_offset": 0,
                    "data_type": "FLOAT32",
                    "scale_factor": 1.0,
                    "unit": "V",
                    "description": "系統平均電壓",
                    "normal_range": [380, 420],
                    "critical_range": [350, 450],
                    "alert_enabled": True
                }, {
                    "id": "active_power",
                    "name": "瞬時實功率(P)",
                    "register_offset": 14,
                    "data_type": "FLOAT32",
                    "scale_factor": 1.0,
                    "unit": "kW",
                    "description": "瞬時實功率",
                    "normal_range": [1.5, 3.5],
                    "critical_range": [0.5, 5.0],
                    "alert_enabled": True
                }]
            }
        ],
        "ai_settings": {
            "model_type": "IsolationForest",
            "contamination": 0.1,
            "training_interval_hours": 24,
            "min_training_samples": 50,
            "feature_engineering": {
                "rolling_windows": [5, 10, 30],
                "statistical_features": ["mean", "std", "diff", "zscore"],
                "time_features": ["hour", "day_of_week", "minute"]
            },
            "anomaly_thresholds": {
                "warning": -0.2,
                "critical": -0.5
            }
        },
        "alert_settings": {
            "email_enabled": False,
            "sms_enabled": False,
            "web_notifications": True,
            "alert_cooldown_minutes": 5,
            "max_alerts_per_hour": 10
        }
    }

    # 保存配置
    with open('plc_points_enhanced.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print("✅ 增強版 PLC 配置文件已創建: plc_points_enhanced.json")
    return config


def update_original_config():
    """更新原始配置文件，添加額外屬性"""

    # 讀取原始配置
    try:
        with open('plc_points.json', 'r', encoding='utf-8') as f:
            original_config = json.load(f)
    except FileNotFoundError:
        print("❌ 原始配置文件 plc_points.json 不存在")
        return False

    # 添加增強屬性
    for group in original_config.get("metric_groups", []):
        # 添加群組屬性
        group.setdefault("group_id",
                         group["group_name"].lower().replace(" ", "_"))
        group.setdefault("description", f"{group['group_name']} 相關參數")
        group.setdefault("priority", "medium")

        # 為每個指標添加屬性
        for metric in group.get("metrics", []):
            metric.setdefault("description", f"{metric['name']} 監控數據")
            metric.setdefault("alert_enabled", True)

            # 根據指標類型設定正常範圍
            if "temp" in metric["id"].lower():
                metric.setdefault("normal_range", [150, 200])
                metric.setdefault("critical_range", [100, 250])
            elif "current" in metric["id"].lower():
                metric.setdefault("normal_range", [10, 40])
                metric.setdefault("critical_range", [5, 60])
            elif "freq" in metric["id"].lower():
                metric.setdefault("normal_range", [45, 55])
                metric.setdefault("critical_range", [30, 70])
            elif "power" in metric["id"].lower():
                metric.setdefault("normal_range", [1.5, 3.5])
                metric.setdefault("critical_range", [0.5, 5.0])
            elif "voltage" in metric["id"].lower():
                metric.setdefault("normal_range", [380, 420])
                metric.setdefault("critical_range", [350, 450])
            else:
                metric.setdefault("normal_range", [0, 100])
                metric.setdefault("critical_range", [0, 200])

    # 保存更新後的配置
    with open('plc_points_updated.json', 'w', encoding='utf-8') as f:
        json.dump(original_config, f, ensure_ascii=False, indent=2)

    print("✅ 原始配置已更新: plc_points_updated.json")
    return True


if __name__ == "__main__":
    print("🔧 PLC 配置更新工具")
    print("=" * 30)

    # 創建增強版配置
    create_enhanced_plc_config()

    # 更新原始配置
    update_original_config()

    print("\n✅ 配置更新完成！")

# ---
