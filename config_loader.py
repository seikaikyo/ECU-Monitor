import json


def load_plc_points(file_path='plc_points.json'):
    """
    載入 PLC 點位配置。
    Args:
        file_path (str): plc_points.json 檔案的路徑。
    Returns:
        dict: PLC 點位配置資料。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"錯誤：無法解析 JSON 檔案 {file_path}")
        return None


def load_devices(file_path='devices.json'):
    """
    載入設備配置。
    Args:
        file_path (str): devices.json 檔案的路徑。
    Returns:
        dict: 設備配置資料。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"錯誤：無法解析 JSON 檔案 {file_path}")
        return None


if __name__ == "__main__":
    plc_config = load_plc_points()
    device_config = load_devices()

    if plc_config:
        print("--- PLC 點位配置載入成功 ---")
        # print(json.dumps(plc_config, indent=2, ensure_ascii=False)) # 測試用，顯示完整配置
    if device_config:
        print("--- 設備配置載入成功 ---")
        # print(json.dumps(device_config, indent=2, ensure_ascii=False)) # 測試用，顯示完整配置
