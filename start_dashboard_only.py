#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
單獨啟動儀表板程式
避免 main.py 中的複雜邏輯干擾
"""

import sys
import os

def main():
    print("=== 啟動 ECU 監控儀表板 ===\n")
    
    # 檢查檔案是否存在
    if not os.path.exists("dashboard_app.py"):
        print("❌ dashboard_app.py 檔案不存在")
        return False
    
    print("方法 1: 嘗試執行簡化測試版本...")
    try:
        import simple_dashboard_test
        return True
    except Exception as e:
        print(f"方法 1 失敗: {e}")
    
    print("\n方法 2: 嘗試直接匯入 dashboard_app...")
    try:
        # 清除可能的快取模組
        if 'dashboard_app' in sys.modules:
            del sys.modules['dashboard_app']
        
        import dashboard_app
        print("✅ dashboard_app 匯入成功")
        
        # 呼叫 main 函數
        if hasattr(dashboard_app, 'main'):
            print("呼叫 dashboard_app.main()...")
            dashboard_app.main()
        else:
            print("❌ dashboard_app 沒有 main 函數")
            return False
            
        return True
        
    except Exception as e:
        print(f"方法 2 失敗: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n方法 3: 嘗試使用子程序...")
    try:
        import subprocess
        result = subprocess.run([sys.executable, "dashboard_app.py"], 
                              capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"方法 3 失敗: {e}")
    
    print("\n❌ 所有啟動方法都失敗了")
    return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n建議:")
            print("1. 執行 'python simple_dashboard_test.py' 進行基本測試")
            print("2. 檢查 dashboard_app.py 的語法是否正確")
            print("3. 確認所有依賴模組都已正確安裝")
    except KeyboardInterrupt:
        print("\n\n程式被使用者中斷")
    except Exception as e:
        print(f"\n啟動過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()