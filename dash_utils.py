#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dash 版本相容性工具
處理不同版本 Dash 的 API 差異
"""

import dash
import sys

def get_dash_version():
    """獲取 Dash 版本"""
    try:
        return dash.__version__
    except AttributeError:
        return "unknown"

def safe_dash_import():
    """安全匯入 Dash 組件，處理版本差異"""
    try:
        # 嘗試新版匯入方式
        from dash import dcc, html
        print(f"✅ 使用新版 Dash 匯入方式 (版本: {get_dash_version()})")
        return dcc, html, True
    except ImportError:
        try:
            # 回退到舊版匯入方式
            import dash_core_components as dcc
            import dash_html_components as html
            print(f"⚠️ 使用舊版 Dash 匯入方式 (版本: {get_dash_version()})")
            return dcc, html, False
        except ImportError as e:
            print(f"❌ Dash 組件匯入失敗: {e}")
            raise

def safe_run_server(app, debug=True, host='0.0.0.0', port=8050):
    """安全啟動 Dash 伺服器，處理版本差異"""
    dash_version = get_dash_version()
    print(f"正在使用 Dash 版本: {dash_version}")
    
    try:
        # 嘗試新版 API
        print("嘗試使用 app.run() 啟動伺服器...")
        app.run(debug=debug, host=host, port=port)
    except AttributeError:
        try:
            # 回退到舊版 API
            print("回退到 app.run_server() 啟動伺服器...")
            app.run_server(debug=debug, host=host, port=port)
        except Exception as e:
            print(f"❌ 兩種啟動方式都失敗: {e}")
            raise
    except Exception as e:
        print(f"❌ 啟動伺服器時發生錯誤: {e}")
        raise

def print_dash_info():
    """顯示 Dash 環境資訊"""
    print("=== Dash 環境資訊 ===")
    print(f"Dash 版本: {get_dash_version()}")
    print(f"Python 版本: {sys.version}")
    
    # 檢查相關套件版本
    packages = ['plotly', 'pandas', 'numpy']
    for package in packages:
        try:
            module = __import__(package)
            version = getattr(module, '__version__', 'unknown')
            print(f"{package} 版本: {version}")
        except ImportError:
            print(f"{package}: 未安裝")
    
    print("=====================")

if __name__ == "__main__":
    print_dash_info()
    
    # 測試匯入
    try:
        dcc, html, is_new_version = safe_dash_import()
        print("✅ Dash 組件匯入成功")
        
        # 建立簡單測試應用
        app = dash.Dash(__name__)
        app.layout = html.Div([
            html.H1("Dash 版本相容性測試"),
            html.P(f"當前使用的是 {'新版' if is_new_version else '舊版'} Dash API"),
            html.P(f"Dash 版本: {get_dash_version()}")
        ])
        
        print("測試應用建立成功，嘗試啟動...")
        safe_run_server(app, debug=True, host='0.0.0.0', port=8051)
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()