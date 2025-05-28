#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os


def test_module_imports():
    """測試所有必要模組的匯入"""

    modules_to_test = [
        ('pandas', 'pd'),
        ('requests', None),
        ('numpy', 'np'),
        ('sklearn.ensemble', 'IsolationForest'),
        ('dash', None),
        ('dash_core_components', 'dcc'),
        ('dash_html_components', 'html'),
        ('plotly.graph_objs', 'go'),
        ('json', None),
        ('time', None),
        ('datetime', None),
        ('threading', None),
    ]

    print("Python 版本:", sys.version)
    print("Python 執行檔路徑:", sys.executable)
    print("當前工作目錄:", os.getcwd())
    print("\n--- 測試模組匯入 ---")

    success_count = 0
    failed_modules = []

    for module_info in modules_to_test:
        if len(module_info) == 2:
            module_name, alias = module_info
        else:
            module_name = module_info[0]
            alias = None

        try:
            if alias:
                if '.' in module_name:
                    # 處理類似 'sklearn.ensemble', 'IsolationForest' 的情況
                    exec(f"from {module_name} import {alias}")
                else:
                    # 處理類似 'pandas', 'pd' 的情況
                    exec(f"import {module_name} as {alias}")
            else:
                exec(f"import {module_name}")

            print(f"✅ {module_name} - 匯入成功")
            success_count += 1

        except ImportError as e:
            print(f"❌ {module_name} - 匯入失敗: {e}")
            failed_modules.append(module_name)
        except Exception as e:
            print(f"⚠️  {module_name} - 匯入時發生其他錯誤: {e}")
            failed_modules.append(module_name)

    print(f"\n--- 測試結果 ---")
    print(f"成功匯入: {success_count}/{len(modules_to_test)} 個模組")

    if failed_modules:
        print(f"失敗的模組: {', '.join(failed_modules)}")
        print("\n建議的安裝指令:")
        install_commands = {
            'pandas': 'pip install pandas',
            'requests': 'pip install requests',
            'numpy': 'pip install numpy',
            'sklearn.ensemble': 'pip install scikit-learn',
            'dash': 'pip install dash',
            'dash_core_components': 'pip install dash-core-components',
            'dash_html_components': 'pip install dash-html-components',
            'plotly.graph_objs': 'pip install plotly'
        }

        for module in failed_modules:
            if module in install_commands:
                print(f"  {install_commands[module]}")
    else:
        print("所有模組都已成功匯入！")

    return len(failed_modules) == 0


def test_custom_modules():
    """測試自定義模組的匯入"""

    custom_modules = [
        'config_loader', 'prometheus_client', 'data_processor',
        'anomaly_detector'
    ]

    print("\n--- 測試自定義模組 ---")

    success_count = 0
    failed_modules = []

    for module_name in custom_modules:
        try:
            exec(f"import {module_name}")
            print(f"✅ {module_name} - 匯入成功")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module_name} - 匯入失敗: {e}")
            failed_modules.append(module_name)
        except Exception as e:
            print(f"⚠️  {module_name} - 匯入時發生其他錯誤: {e}")
            failed_modules.append(module_name)

    print(f"\n自定義模組測試結果: {success_count}/{len(custom_modules)} 個模組成功匯入")

    if failed_modules:
        print(f"失敗的自定義模組: {', '.join(failed_modules)}")
        print("請確認這些檔案存在於當前目錄並且語法正確")

    return len(failed_modules) == 0


def test_file_existence():
    """測試必要檔案是否存在"""

    required_files = [
        'plc_points.json', 'devices.json', 'config_loader.py',
        'prometheus_client.py', 'data_processor.py', 'anomaly_detector.py',
        'dashboard_app.py'
    ]

    print("\n--- 測試檔案存在性 ---")

    missing_files = []

    for filename in required_files:
        if os.path.exists(filename):
            print(f"✅ {filename} - 檔案存在")
        else:
            print(f"❌ {filename} - 檔案不存在")
            missing_files.append(filename)

    if missing_files:
        print(f"\n缺少的檔案: {', '.join(missing_files)}")
        return False
    else:
        print("\n所有必要檔案都存在！")
        return True


def test_json_files():
    """測試 JSON 檔案的有效性"""

    json_files = ['plc_points.json', 'devices.json']

    print("\n--- 測試 JSON 檔案有效性 ---")

    all_valid = True

    for filename in json_files:
        if os.path.exists(filename):
            try:
                import json
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ {filename} - JSON 格式有效")
            except json.JSONDecodeError as e:
                print(f"❌ {filename} - JSON 格式錯誤: {e}")
                all_valid = False
            except Exception as e:
                print(f"❌ {filename} - 讀取檔案時發生錯誤: {e}")
                all_valid = False
        else:
            print(f"❌ {filename} - 檔案不存在")
            all_valid = False

    return all_valid


def main():
    """主函數"""
    print("=== 模組和環境測試工具 ===\n")

    # 測試標準模組匯入
    standard_modules_ok = test_module_imports()

    # 測試檔案存在性
    files_ok = test_file_existence()

    # 測試 JSON 檔案
    json_ok = test_json_files()

    # 測試自定義模組匯入
    custom_modules_ok = test_custom_modules()

    print("\n=== 總體測試結果 ===")

    if standard_modules_ok and files_ok and json_ok and custom_modules_ok:
        print("🎉 所有測試都通過！環境設定正確。")
        print("您可以嘗試執行 main.py 或直接執行 dashboard_app.py")
        return True
    else:
        print("❌ 部分測試失敗，請根據上述建議進行修正。")

        if not standard_modules_ok:
            print("• 需要安裝缺少的 Python 套件")
        if not files_ok:
            print("• 需要建立缺少的檔案")
        if not json_ok:
            print("• 需要修正 JSON 檔案格式")
        if not custom_modules_ok:
            print("• 需要檢查自定義模組的語法")

        return False


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
