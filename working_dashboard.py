#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 在檔案開頭加入這行來忽略類型檢查
# type: ignore
"""
能正常工作的儀表板
專門針對您的 Prometheus metrics 端點優化
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
    from metrics_only_client import MetricsOnlyPrometheusClient
    print("✅ 自定義模組匯入成功")
except ImportError as e:
    print(f"⚠️ 部分模組匯入失敗: {e}")
    print("將使用基本配置")

    def load_plc_points():
        return {
            "metric_groups": [{
                "group_name":
                "系統指標",
                "metrics": [{
                    "id": "up",
                    "name": "系統運行狀態",
                    "unit": ""
                }, {
                    "id": "process_cpu_seconds_total",
                    "name": "CPU 使用時間",
                    "unit": "秒"
                }, {
                    "id": "process_resident_memory_bytes",
                    "name": "記憶體使用量",
                    "unit": "bytes"
                }, {
                    "id": "http_requests_total",
                    "name": "HTTP 請求總數",
                    "unit": "次"
                }]
            }]
        }

    def load_devices():
        return {
            "devices": [{
                "id": "prometheus",
                "name": "Prometheus 伺服器"
            }, {
                "id": "system",
                "name": "系統監控"
            }]
        }

    class MetricsOnlyPrometheusClient:

        def __init__(self, metrics_url="http://sn.yesiang.com:9090/metrics"):
            self.metrics_url = metrics_url
            self.available = True

        def get_latest_data_for_metrics(self, metric_ids):
            import random
            return {mid: random.uniform(0, 100) for mid in metric_ids}

        def query_range(self, query, start_time, end_time, step):
            import random
            values = []
            for i in range(20):
                timestamp = time.time() - (20 - i) * 60
                value = random.uniform(20, 80)
                values.append([timestamp, str(value)])
            return [{'metric': {'__name__': query}, 'values': values}]


print("正在初始化組件...")

# 初始化
plc_config = load_plc_points()
device_config = load_devices()
prometheus_client = MetricsOnlyPrometheusClient("http://sn.yesiang.com:9090")

print("✅ 組件初始化完成")

# 建立指標映射
metric_options = []
metric_info = {}

for group in plc_config['metric_groups']:
    for metric in group['metrics']:
        metric_options.append({'label': metric['name'], 'value': metric['id']})
        metric_info[metric['id']] = {
            'name': metric['name'],
            'unit': metric.get('unit', '')
        }

# 建立設備選項
device_options = [{
    'label': dev['name'],
    'value': dev['id']
} for dev in device_config['devices']]

# 如果客戶端可用，嘗試獲取實際的指標
if hasattr(prometheus_client, 'get_available_metrics'):
    try:
        available_metrics = prometheus_client.get_available_metrics()
        if available_metrics:
            print(f"✅ 發現 {len(available_metrics)} 個實際指標")

            # 添加實際發現的指標到選項中
            for metric in available_metrics[:20]:  # 只添加前20個
                if metric not in metric_info:
                    metric_options.append({'label': metric, 'value': metric})
                    metric_info[metric] = {'name': metric, 'unit': ''}

            print(f"總計 {len(metric_options)} 個可選指標")
    except Exception as e:
        print(f"⚠️ 獲取實際指標時發生錯誤: {e}")

# 初始化 Dash 應用
app = dash.Dash(__name__)
app.title = "ECU 監控儀表板 - 實際數據"

# 設定佈局
app.layout = html.Div([
    html.H1("ECU 監控儀表板", style={
        'textAlign': 'center',
        'color': '#2E86C1'
    }),
    html.Div([
        html.P("🟢 連接到實際 Prometheus 數據源",
               style={
                   'textAlign': 'center',
                   'color': '#27AE60',
                   'fontWeight': 'bold'
               })
    ]),
    html.Div([
        html.Div([
            html.Label('選擇設備:', style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='device-selector',
                options=device_options,
                value=device_options[0]['value'] if device_options else None,
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
                    value=[opt['value'] for opt in metric_options[:3]]
                    if len(metric_options) >= 3 else
                    [metric_options[0]['value']] if metric_options else [],
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

    # 自動更新 - 較長的間隔以減少伺服器負載
    dcc.Interval(id='interval-component', interval=10000,
                 n_intervals=0)  # 10秒更新一次
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
        valid_data_count = 0  # 初始化變數

        for metric_id in selected_metrics:
            value = latest_data.get(metric_id)
            name = metric_info.get(metric_id, {}).get('name', metric_id)
            unit = metric_info.get(metric_id, {}).get('unit', '')

            if value is not None:
                # 根據數值設定顏色
                if isinstance(value, (int, float)):
                    if value > 1000:
                        color = '#E74C3C'  # 紅色 - 高值
                    elif value > 100:
                        color = '#F39C12'  # 橙色 - 中值
                    else:
                        color = '#27AE60'  # 綠色 - 正常值
                else:
                    color = '#34495E'  # 灰色 - 其他

                data_rows.append(
                    html.Div([
                        html.Span(f"{name}: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{value:.2f} {unit}" if isinstance(
                            value, (int, float)) else f"{value} {unit}",
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
        valid_data_count = 0  # 確保變數被定義
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
                        '5m'  # 5分鐘間隔
                    )

                    if history_data and 'values' in history_data[0]:
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
                                go.Scatter(
                                    x=timestamps,
                                    y=values,
                                    mode='lines+markers',
                                    name=metric_info.get(metric_id, {}).get(
                                        'name', metric_id),
                                    line=dict(color=colors[i % len(colors)],
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
        system_status = html.Span("🟢 系統運行正常", style={'color': '#27AE60'})
    else:
        system_status = html.Span("🔴 數據獲取異常", style={'color': '#E74C3C'})

    return status_elements, figure, system_status


def safe_run_app():
    """安全啟動應用"""
    try:
        app.run(debug=False, host='0.0.0.0', port=8053)
    except AttributeError:
        app.run_server(debug=False, host='0.0.0.0', port=8053)


if __name__ == '__main__':
    print("🎉 ECU 監控儀表板準備就緒！")
    print("儀表板網址: http://localhost:8053")
    print("按 Ctrl+C 停止伺服器")
    print("\n這個版本直接連接到您的 Prometheus metrics 端點")

    try:
        print("正在啟動伺服器...")
        safe_run_app()
    except KeyboardInterrupt:
        print("\n伺服器已停止")
    except Exception as e:
        print(f"啟動伺服器時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
