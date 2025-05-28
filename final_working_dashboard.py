#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 在檔案開頭加入這行來忽略類型檢查
# type: ignore
"""
最終修正的儀表板
使用正確的 Prometheus 端點和找到的工業指標
"""

import sys
import datetime
import pandas as pd
import time

# Dash 匯入
try:
    import dash
    from dash.dependencies import Output, Input
    try:
        from dash import dcc, html
    except ImportError:
        import dash_core_components as dcc
        import dash_html_components as html
    import plotly.graph_objs as go
    print("✅ Dash 匯入成功")
except ImportError as e:
    print(f"❌ Dash 匯入失敗: {e}")
    sys.exit(1)

# 自定義模組匯入
try:
    from config_loader import load_plc_points, load_devices
    print("✅ 配置載入器匯入成功")
except ImportError as e:
    print(f"⚠️ 配置載入器匯入失敗: {e}")

# 使用修正的 Prometheus 客戶端
import requests


class FixedPrometheusClient:
    """修正的 Prometheus 客戶端，使用正確的端點"""

    def __init__(self, prometheus_url="http://sn.yesiang.com:9090"):
        self.prometheus_url = prometheus_url
        self.available = self._test_connection()
        print(f"初始化 Prometheus 客戶端: {prometheus_url}")
        if self.available:
            print("✅ 連接成功")
        else:
            print("❌ 連接失敗")

    def _test_connection(self):
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/status/config", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_latest_data_for_metrics(self, metric_ids):
        """獲取指標的最新數據"""
        if not self.available:
            return {metric_id: None for metric_id in metric_ids}

        latest_data = {}

        for metric_id in metric_ids:
            try:
                response = requests.get(f"{self.prometheus_url}/api/v1/query",
                                        params={'query': metric_id},
                                        timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        result = data.get('data', {}).get('result', [])
                        if result:
                            latest_data[metric_id] = float(
                                result[0]['value'][1])
                        else:
                            latest_data[metric_id] = None
                    else:
                        latest_data[metric_id] = None
                else:
                    latest_data[metric_id] = None

            except Exception as e:
                print(f"查詢 {metric_id} 時發生錯誤: {e}")
                latest_data[metric_id] = None

        return latest_data

    def query_range(self, query, start_time, end_time, step):
        """範圍查詢"""
        if not self.available:
            return []

        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query_range",
                params={
                    'query': query,
                    'start': start_time,
                    'end': end_time,
                    'step': step
                },
                timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data.get('data', {}).get('result', [])
            return []
        except:
            return []


print("正在初始化組件...")

# 初始化客戶端
prometheus_client = FixedPrometheusClient("http://sn.yesiang.com:9090")

# 使用從工具中發現的實際工業指標
discovered_metrics = {
    # 溫度指標
    "right_aux2a_temp_pv": {
        "name": "右側輔控2A溫度PV",
        "unit": "℃"
    },
    "right_heater2a_temp": {
        "name": "右側電熱室2A溫度",
        "unit": "℃"
    },
    "left_outlet_temp_middle_bottom": {
        "name": "左側出風中下溫度",
        "unit": "℃"
    },
    "right_inlet_temp_middle_middle": {
        "name": "右側入風中中溫度",
        "unit": "℃"
    },

    # 馬達指標
    "motor_freq_right_1b": {
        "name": "右側馬達1B頻率",
        "unit": "Hz"
    },
    "motor_freq_left_1b": {
        "name": "左側馬達1B頻率",
        "unit": "Hz"
    },
    "motor_current_right_2a": {
        "name": "右側馬達2A電流",
        "unit": "A"
    },
    "motor_current_left_1b": {
        "name": "左側馬達1B電流",
        "unit": "A"
    },

    # 壓力指標
    "damper_cda_pressure": {
        "name": "風門CDA壓力",
        "unit": "kPa"
    },
    "jr2_cda_pressure": {
        "name": "軸冷CDA壓力",
        "unit": "kPa"
    },
    "hepa_pressure_left": {
        "name": "HEPA壓差左",
        "unit": "Pa"
    },
    "hepa_pressure_right": {
        "name": "HEPA壓差右",
        "unit": "Pa"
    },

    # 控制指標
    "left_aux2b_ct": {
        "name": "左側輔控2B_CT",
        "unit": "A"
    },
    "right_aux1a_ct": {
        "name": "右側輔控1A_CT",
        "unit": "A"
    },
}

# 建立設備選項
device_options = [
    {
        'label': '1號機',
        'value': 'ecu1051_1'
    },
    {
        'label': '2號機',
        'value': 'ecu1051_2'
    },
    {
        'label': '3號機',
        'value': 'ecu1051_3'
    },
    {
        'label': '4號機',
        'value': 'ecu1051_4'
    },
]

# 建立指標選項
metric_options = []
for metric_id, info in discovered_metrics.items():
    metric_options.append({'label': info['name'], 'value': metric_id})

print("✅ 組件初始化完成")

# 初始化 Dash 應用
app = dash.Dash(__name__)
app.title = "ECU 監控儀表板 - 最終版本"

# 設定佈局
app.layout = html.Div([
    html.H1("ECU 監控儀表板", style={
        'textAlign': 'center',
        'color': '#2E86C1'
    }),
    html.Div([
        html.P("🟢 成功連接到 ECU-1051 數據源",
               style={
                   'textAlign': 'center',
                   'color': '#27AE60',
                   'fontWeight': 'bold'
               })
    ]),
    html.Div([
        html.Div([
            html.Label('選擇設備:', style={'fontWeight': 'bold'}),
            dcc.Dropdown(id='device-selector',
                         options=device_options,
                         value=device_options[0]['value'],
                         style={'marginTop': '5px'})
        ],
                 style={
                     'width': '48%',
                     'display': 'inline-block',
                     'padding': '10px'
                 }),
        html.Div(
            [
                html.Label('選擇指標 (可多選):', style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='metric-selector',
                    options=metric_options,
                    value=[
                        metric_options[0]['value'], metric_options[4]['value'],
                        metric_options[8]['value']
                    ],
                    multi=True,
                    style={'marginTop': '5px'})
            ],
            style={
                'width': '48%',
                'float': 'right',
                'display': 'inline-block',
                'padding': '10px'
            })
    ],
             style={'marginBottom': '20px'}),
    html.Hr(),

    # 狀態顯示區域
    html.Div([
        html.Div(id='status-display',
                 style={
                     'textAlign': 'center',
                     'fontSize': '16px',
                     'margin': '20px',
                     'padding': '15px',
                     'backgroundColor': '#F8F9FA',
                     'borderRadius': '5px',
                     'border': '1px solid #DEE2E6'
                 })
    ]),

    # 圖表區域
    html.Div([dcc.Graph(id='data-graph', style={'height': '500px'})],
             style={'margin': '20px'}),

    # 系統狀態
    html.Div([
        html.H4('系統狀態',
                style={
                    'textAlign': 'center',
                    'marginTop': '30px',
                    'color': '#34495E'
                }),
        html.Div(id='system-status',
                 style={
                     'textAlign': 'center',
                     'fontSize': '18px',
                     'fontWeight': 'bold',
                     'padding': '10px'
                 })
    ]),

    # 自動更新
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0)  # 5秒更新
])


# 回調函數
@app.callback([
    Output('status-display', 'children'),
    Output('data-graph', 'figure'),
    Output('system-status', 'children')
], [
    Input('interval-component', 'n_intervals'),
    Input('device-selector', 'value'),
    Input('metric-selector', 'value')
])
def update_dashboard(n, selected_device, selected_metrics):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not selected_metrics:
        return (html.Div([
            html.H5(f"資料更新時間: {current_time}", style={'color': '#2C3E50'}),
            html.P("請選擇要監測的指標", style={
                'color': '#E74C3C',
                'fontSize': '16px'
            })
        ]), {
            'data': [],
            'layout': {
                'title': '請選擇監測指標',
                'height': 500
            }
        }, html.Span("⚠️ 請選擇監測指標", style={'color': 'orange'}))

    # 獲取實際數據
    status_elements = [
        html.H5(f"資料更新時間: {current_time}",
                style={
                    'color': '#2C3E50',
                    'marginBottom': '15px'
                })
    ]

    try:
        latest_data = prometheus_client.get_latest_data_for_metrics(
            selected_metrics)

        data_rows = []
        valid_data_count = 0

        for metric_id in selected_metrics:
            value = latest_data.get(metric_id)
            name = discovered_metrics.get(metric_id, {}).get('name', metric_id)
            unit = discovered_metrics.get(metric_id, {}).get('unit', '')

            if value is not None:
                # 根據數值設定顏色
                if isinstance(value, (int, float)):
                    if value > 100:
                        color = '#E74C3C'  # 紅色 - 高值
                    elif value > 50:
                        color = '#F39C12'  # 橙色 - 中值
                    else:
                        color = '#27AE60'  # 綠色 - 正常值
                else:
                    color = '#34495E'  # 灰色 - 其他

                data_rows.append(
                    html.Div([
                        html.Span(f"{name}: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{value:.2f} {unit}",
                                  style={
                                      'color': color,
                                      'fontWeight': 'bold'
                                  })
                    ],
                             style={
                                 'margin': '5px 0',
                                 'fontSize': '14px'
                             }))
                valid_data_count += 1
            else:
                data_rows.append(
                    html.Div([
                        html.Span(f"{name}: ", style={'fontWeight': 'bold'}),
                        html.Span("無數據",
                                  style={
                                      'color': '#95A5A6',
                                      'fontStyle': 'italic'
                                  })
                    ],
                             style={
                                 'margin': '5px 0',
                                 'fontSize': '14px'
                             }))

        status_elements.extend(data_rows)

        if valid_data_count > 0:
            status_elements.append(
                html.
                P(f"✅ 成功獲取 {valid_data_count}/{len(selected_metrics)} 個指標的數據",
                  style={
                      'color': '#27AE60',
                      'marginTop': '15px',
                      'fontSize': '12px'
                  }))
        else:
            status_elements.append(
                html.P("❌ 未能獲取任何指標數據",
                       style={
                           'color': '#E74C3C',
                           'marginTop': '15px'
                       }))

    except Exception as e:
        valid_data_count = 0
        status_elements.append(
            html.P(f"❌ 獲取數據時發生錯誤: {e}",
                   style={
                       'color': '#E74C3C',
                       'marginTop': '15px'
                   }))
        latest_data = {}

    # 建立圖表
    graphs = []
    colors = [
        '#3498DB', '#E74C3C', '#2ECC71', '#F39C12', '#9B59B6', '#1ABC9C',
        '#34495E', '#E67E22'
    ]

    try:
        for i, metric_id in enumerate(selected_metrics):
            if metric_id in latest_data and latest_data[metric_id] is not None:
                # 獲取歷史數據
                try:
                    history_data = prometheus_client.query_range(
                        metric_id,
                        int(time.time()) - 3600,  # 過去1小時
                        int(time.time()),
                        '2m'  # 2分鐘間隔
                    )

                    if history_data and len(
                            history_data) > 0 and 'values' in history_data[0]:
                        timestamps = []
                        values = []

                        for ts, val in history_data[0]['values']:
                            timestamps.append(
                                datetime.datetime.fromtimestamp(float(ts)))
                            try:
                                values.append(float(val))
                            except (ValueError, TypeError):
                                values.append(0)

                        if timestamps and values:
                            graphs.append(
                                go.Scatter(x=timestamps,
                                           y=values,
                                           mode='lines+markers',
                                           name=discovered_metrics.get(
                                               metric_id,
                                               {}).get('name', metric_id),
                                           line=dict(color=colors[i %
                                                                  len(colors)],
                                                     width=2),
                                           marker=dict(size=4),
                                           hovertemplate=
                                           '%{y:.2f}<br>%{x}<extra></extra>'))
                except Exception as e:
                    print(f"獲取 {metric_id} 歷史數據失敗: {e}")

        figure = {
            'data':
            graphs,
            'layout':
            go.Layout(title={
                'text': f'設備 {selected_device} 即時監測數據',
                'x': 0.5,
                'font': {
                    'size': 18,
                    'color': '#2C3E50'
                }
            },
                      xaxis={
                          'title': '時間',
                          'showgrid': True
                      },
                      yaxis={
                          'title': '數值',
                          'showgrid': True
                      },
                      hovermode='x unified',
                      showlegend=True,
                      legend=dict(x=0, y=1, bgcolor='rgba(255,255,255,0.8)'),
                      plot_bgcolor='rgba(248,249,250,0.8)',
                      paper_bgcolor='rgba(255,255,255,1)',
                      height=500,
                      margin=dict(l=60, r=30, t=60, b=60))
        }
    except Exception as e:
        print(f"建立圖表時發生錯誤: {e}")
        figure = {
            'data': [],
            'layout': {
                'title': f'圖表建立錯誤: {e}',
                'height': 500
            }
        }

    # 系統狀態
    if valid_data_count > 0:
        system_status = html.Span("🟢 ECU-1051 系統運行正常",
                                  style={'color': '#27AE60'})
    else:
        system_status = html.Span("🔴 數據獲取異常", style={'color': '#E74C3C'})

    return status_elements, figure, system_status


def safe_run_app():
    """安全啟動應用"""
    try:
        app.run(debug=False, host='0.0.0.0', port=8054)
    except AttributeError:
        app.run_server(debug=False, host='0.0.0.0', port=8054)


if __name__ == '__main__':
    print("🎉 ECU 監控儀表板最終版本準備就緒！")
    print("儀表板網址: http://localhost:8054")
    print("使用發現的實際工業指標")
    print("數據源: http://sn.yesiang.com:9090")

    try:
        print("正在啟動伺服器...")
        safe_run_app()
    except KeyboardInterrupt:
        print("\n伺服器已停止")
    except Exception as e:
        print(f"啟動伺服器時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
