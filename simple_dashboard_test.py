#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
簡化版的儀表板測試程式
用於測試基本功能是否正常
"""

import sys
import datetime
import pandas as pd

# 測試 Dash 匯入
try:
    import dash
    from dash.dependencies import Output, Input
    import plotly.graph_objs as go

    # 使用相容性工具匯入組件
    try:
        from dash_utils import safe_dash_import, safe_run_server
        dcc, html, is_new_version = safe_dash_import()
    except ImportError:
        # 如果沒有 dash_utils，手動處理
        try:
            from dash import dcc, html
            print("✅ 使用新版 Dash 匯入方式")
            is_new_version = True
        except ImportError:
            import dash_core_components as dcc
            import dash_html_components as html
            print("⚠️ 使用舊版 Dash 匯入方式")
            is_new_version = False

        def safe_run_server(app, debug=True, host='0.0.0.0', port=8050):
            try:
                app.run(debug=debug, host=host, port=port)
            except AttributeError:
                app.run_server(debug=debug, host=host, port=port)

except ImportError as e:
    print(f"❌ Dash 匯入失敗: {e}")
    sys.exit(1)

# 測試自定義模組匯入
try:
    from config_loader import load_plc_points, load_devices
    from prometheus_client import PrometheusClient
    from data_processor import DataProcessor
    print("✅ 自定義模組匯入成功")
except ImportError as e:
    print(f"❌ 自定義模組匯入失敗: {e}")
    print("將使用模擬數據進行測試")

    # 建立模擬類別
    class PrometheusClient:

        def __init__(self, prometheus_url=""):
            self.prometheus_url = prometheus_url

        def get_latest_data_for_metrics(self, metrics):
            return {
                metric: 25.0 + (hash(metric) % 100) / 10.0
                for metric in metrics
            }

        def query_range(self, query, start, end, step):
            import time
            current_time = time.time()
            return [{
                'metric': {
                    '__name__': query.split('{')[0]
                },
                'values': [[current_time - i * 60,
                            str(25.0 + i * 0.1)] for i in range(10)]
            }]

    def load_plc_points():
        return {
            "metric_groups": [{
                "group_name":
                "測試組",
                "metrics": [{
                    "id": "test_temp_1",
                    "name": "測試溫度1",
                    "unit": "℃"
                }, {
                    "id": "test_temp_2",
                    "name": "測試溫度2",
                    "unit": "℃"
                }, {
                    "id": "test_current_1",
                    "name": "測試電流1",
                    "unit": "A"
                }]
            }]
        }

    def load_devices():
        return {
            "devices": [{
                "id": "test_device_1",
                "name": "測試設備1"
            }, {
                "id": "test_device_2",
                "name": "測試設備2"
            }]
        }


# 初始化
print("正在初始化組件...")
prometheus_client = PrometheusClient("http://sn.yesiang.com:9090")
plc_config = load_plc_points()
device_config = load_devices()

if not plc_config or not device_config:
    print("❌ 配置載入失敗")
    sys.exit(1)

print("✅ 組件初始化完成")

# 初始化 Dash 應用
app = dash.Dash(__name__)
app.title = "ECU 監控儀表板測試"

# 準備選項
device_options = [{
    'label': dev['name'],
    'value': dev['id']
} for dev in device_config['devices']]
metric_options = []
metric_info = {}

for group in plc_config['metric_groups']:
    for metric in group['metrics']:
        metric_options.append({'label': metric['name'], 'value': metric['id']})
        metric_info[metric['id']] = {
            'name': metric['name'],
            'unit': metric['unit']
        }

# 設定佈局
app.layout = html.Div([
    html.H1("ECU 監控儀表板測試", style={'textAlign': 'center'}),
    html.Div([
        html.Div([
            html.Label('選擇設備:'),
            dcc.Dropdown(
                id='device-selector',
                options=device_options,
                value=device_options[0]['value'] if device_options else None)
        ],
                 style={
                     'width': '48%',
                     'display': 'inline-block'
                 }),
        html.Div([
            html.Label('選擇指標:'),
            dcc.Dropdown(
                id='metric-selector',
                options=metric_options,
                value=[metric_options[0]['value']] if metric_options else [],
                multi=True)
        ],
                 style={
                     'width': '48%',
                     'float': 'right',
                     'display': 'inline-block'
                 })
    ],
             style={'padding': '20px'}),
    html.Hr(),
    html.Div(id='status-display',
             style={
                 'textAlign': 'center',
                 'fontSize': '18px',
                 'margin': '20px'
             }),
    dcc.Graph(id='data-graph'),

    # 自動更新
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0)
])


# 回調函數
@app.callback(
    [Output('status-display', 'children'),
     Output('data-graph', 'figure')], [
         Input('interval-component', 'n_intervals'),
         Input('device-selector', 'value'),
         Input('metric-selector', 'value')
     ])
def update_dashboard(n, selected_device, selected_metrics):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not selected_metrics:
        return (f"更新時間: {current_time} - 請選擇監測指標", {
            'data': [],
            'layout': {
                'title': '請選擇監測指標'
            }
        })

    # 獲取即時數據
    try:
        latest_data = prometheus_client.get_latest_data_for_metrics(
            selected_metrics)
        status_info = [f"更新時間: {current_time}"]

        for metric_id in selected_metrics:
            value = latest_data.get(metric_id, 0)
            name = metric_info.get(metric_id, {}).get('name', metric_id)
            unit = metric_info.get(metric_id, {}).get('unit', '')
            status_info.append(html.Br())
            status_info.append(f"{name}: {value:.2f} {unit}")

    except Exception as e:
        status_info = [f"更新時間: {current_time}", html.Br(), f"獲取數據時發生錯誤: {e}"]

    # 建立圖表
    try:
        import time
        current_timestamp = int(time.time())

        graphs = []
        for metric_id in selected_metrics:
            # 模擬歷史數據
            timestamps = [
                datetime.datetime.fromtimestamp(current_timestamp - i * 60)
                for i in range(20, 0, -1)
            ]
            values = [
                latest_data.get(metric_id, 25) + (i % 5 - 2) for i in range(20)
            ]

            graphs.append(
                go.Scatter(x=timestamps,
                           y=values,
                           mode='lines+markers',
                           name=metric_info.get(metric_id,
                                                {}).get('name', metric_id)))

        figure = {
            'data':
            graphs,
            'layout':
            go.Layout(title=f'設備 {selected_device} 監測數據',
                      xaxis={'title': '時間'},
                      yaxis={'title': '數值'},
                      hovermode='closest')
        }
    except Exception as e:
        figure = {'data': [], 'layout': {'title': f'圖表建立錯誤: {e}'}}

    return status_info, figure


if __name__ == '__main__':
    print("🎉 測試儀表板準備就緒！")
    print("儀表板網址: http://localhost:8050")
    print("按 Ctrl+C 停止伺服器")

    try:
        # 使用相容性函數啟動
        safe_run_server(app, debug=True, host='0.0.0.0', port=8050)
    except KeyboardInterrupt:
        print("\n伺服器已停止")
    except Exception as e:
        print(f"啟動伺服器時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
