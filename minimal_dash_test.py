#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
最小化的 Dash 測試程式
用於確認 Dash 基本功能是否正常
"""

import sys

# 嘗試匯入 Dash
try:
    import dash
    print(f"✅ Dash 版本: {dash.__version__}")
except ImportError:
    print("❌ Dash 未安裝")
    sys.exit(1)

# 匯入組件
try:
    from dash import dcc, html
    print("✅ 使用新版 Dash 匯入")
except ImportError:
    try:
        import dash_core_components as dcc
        import dash_html_components as html
        print("✅ 使用舊版 Dash 匯入")
    except ImportError:
        print("❌ 無法匯入 Dash 組件")
        sys.exit(1)

# 建立應用
app = dash.Dash(__name__)

# 簡單佈局
app.layout = html.Div([
    html.H1("Dash 測試成功！"),
    html.P("如果您看到這個頁面，說明 Dash 安裝正確。"),
    html.Hr(),
    html.P("您可以關閉此視窗並繼續使用完整的儀表板。")
])

if __name__ == '__main__':
    print("🎉 最小化 Dash 測試")
    print("網址: http://localhost:8052")
    print("按 Ctrl+C 停止")
    
    try:
        # 嘗試不同的啟動方式
        try:
            app.run(debug=False, host='0.0.0.0', port=8052)
        except AttributeError:
            app.run_server(debug=False, host='0.0.0.0', port=8052)
    except KeyboardInterrupt:
        print("\n✅ 測試完成")
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        # 顯示詳細錯誤
        import traceback
        traceback.print_exc()