#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import datetime
import pandas as pd

# 嘗試匯入 Dash 相關模組
try:
    import dash
    from dash.dependencies import Output, Input
    # 使用新的匯入方式
    try:
        from dash import dcc, html
    except ImportError:
        # 如果新方式失敗，使用舊方式
        import dash_core_components as dcc
        import dash_html_components as html
    import plotly.graph_objs as go
    print("Dash 模組匯入成功")
except ImportError as e:
    print(f"匯入 Dash 模組時發生錯誤: {e}")
    print("請確認已正確安裝 Dash:")
    print("pip install dash plotly")
    sys.exit(1)

# 嘗試匯入自定義模組
try:
    from config_loader import load_plc_points, load_devices
    from prometheus_client import PrometheusClient
    from data_processor import DataProcessor
    from anomaly_detector import AnomalyDetector
    print("自定義模組匯入成功")
except ImportError as e:
    print(f"匯入自定義模組時發生錯誤: {e}")
    print("請確認所有必要的檔案都存在於當前目錄")
    sys.exit(1)

# 初始化全域變數
app = None
prometheus_client = None
plc_config = None
device_config = None
data_processor = None
anomaly_detector = None
metrics_for_anomaly = None


def initialize_components():
    """初始化所有組件"""
    global app, prometheus_client, plc_config, device_config, data_processor, anomaly_detector, metrics_for_anomaly

    try:
        # 初始化客戶端
        prometheus_client = PrometheusClient(
            prometheus_url="http://sn.yesiang.com:9090")
        plc_config = load_plc_points()
        device_config = load_devices()

        if not plc_config or not device_config:
            raise ValueError("無法載入配置檔案")

        data_processor = DataProcessor(plc_config)

        # 初始化異常檢測器
        metrics_for_anomaly = [
            'left_main_temp_pv', 'left_aux1a_temp_pv', 'left_aux1a_ct',
            'right_main_temp_pv', 'right_aux1a_temp_pv', 'right_aux1a_ct'
        ]
        anomaly_detector = AnomalyDetector(metrics_for_anomaly)

        print("組件初始化成功")
        return True

    except Exception as e:
        print(f"初始化組件時發生錯誤: {e}")
        return False


def train_anomaly_model():
    """訓練異常檢測模型"""
    global anomaly_detector, prometheus_client, data_processor, device_config, metrics_for_anomaly

    print("--- 正在載入歷史數據以訓練異常檢測模型 ---")

    try:
        end_time_train = int(datetime.datetime.now().timestamp())
        start_time_train = end_time_train - 24 * 3600  # 過去 24 小時
        training_data_list = []

        # 逐一查詢每個設備的每個監控指標的歷史數據
        for device in device_config['devices']:
            for metric_id in metrics_for_anomaly:
                try:
                    query_result = prometheus_client.query_range(
                        f'{metric_id}{{device_id="{device["id"]}"}}',
                        start_time_train, end_time_train, '5m')
                    if query_result:
                        df_temp = data_processor.process_range_data(
                            query_result, device_id=device['id'])
                        if not df_temp.empty:
                            training_data_list.append(df_temp)
                except Exception as e:
                    print(f"查詢 {device['id']} 的 {metric_id} 時發生錯誤: {e}")

        if training_data_list:
            historical_training_df = pd.concat(training_data_list,
                                               ignore_index=True)
            historical_training_df = historical_training_df.groupby(
                ['timestamp', 'device_id']).first().reset_index()
            print("歷史數據載入完成，正在訓練模型...")
            anomaly_detector.train_model(historical_training_df)
            print("異常檢測模型訓練完成。")
        else:
            print("未能載入足夠的歷史數據以訓練異常檢測模型。")

    except Exception as e:
        print(f"訓練異常檢測模型時發生錯誤: {e}")


def create_app_layout():
    """建立應用程式佈局"""
    global device_config, plc_config

    # 構建設備選項
    device_options = [{
        'label': dev['name'],
        'value': dev['id']
    } for dev in device_config['devices']]

    # 獲取所有獨特的 metric_id 及其名稱和單位
    all_metric_options = []
    for group in plc_config['metric_groups']:
        for metric in group['metrics']:
            all_metric_options.append({
                'label': metric['name'],
                'value': metric['id']
            })

    return html.Div(children=[
        html.H1(children='工業設備智慧決策儀表板', style={'textAlign': 'center'}),
        html.Div([
            html.Div([
                html.Label('選擇設備:'),
                dcc.Dropdown(id='device-selector',
                             options=device_options,
                             value=device_options[0]['value']
                             if device_options else None,
                             clearable=False)
            ],
                     style={
                         'width': '49%',
                         'display': 'inline-block'
                     }),
            html.Div([
                html.Label('選擇監測指標 (多選):'),
                dcc.Dropdown(id='metric-selector',
                             options=all_metric_options,
                             value=[all_metric_options[0]['value']]
                             if all_metric_options else [],
                             multi=True)
            ],
                     style={
                         'width': '49%',
                         'float': 'right',
                         'display': 'inline-block'
                     })
        ],
                 style={'padding': '10px'}),
        html.Hr(),
        html.Div(id='live-update-text',
                 style={
                     'textAlign': 'center',
                     'fontSize': '20px',
                     'margin': '10px'
                 }),
        html.Div([
            dcc.Graph(id='live-update-graph'),
        ],
                 style={
                     'width': '98%',
                     'margin': 'auto'
                 }),
        html.Div([
            html.H3('異常檢測狀態',
                    style={
                        'textAlign': 'center',
                        'marginTop': '20px'
                    }),
            html.Div(id='anomaly-status',
                     style={
                         'textAlign': 'center',
                         'fontSize': '24px',
                         'fontWeight': 'bold'
                     }),
            html.Div(id='anomaly-details',
                     style={
                         'textAlign': 'center',
                         'fontSize': '18px',
                         'marginTop': '10px'
                     }),
        ]),

        # 隱藏的計時間隔，用於觸發更新
        dcc.Interval(
            id='interval-component',
            interval=5 * 1000,  # 每 5 秒更新一次
            n_intervals=0)
    ])


def setup_callbacks():
    """設定回調函數"""
    global app, prometheus_client, plc_config, anomaly_detector, metrics_for_anomaly

    # 建立指標 ID 到名稱和單位的映射
    metric_id_to_name_map = {}
    metric_id_to_unit_map = {}
    for group in plc_config['metric_groups']:
        for metric in group['metrics']:
            metric_id_to_name_map[metric['id']] = metric['name']
            metric_id_to_unit_map[metric['id']] = metric['unit']

    @app.callback([
        Output('live-update-text', 'children'),
        Output('live-update-graph', 'figure'),
        Output('anomaly-status', 'children'),
        Output('anomaly-details', 'children')
    ], [
        Input('interval-component', 'n_intervals'),
        Input('device-selector', 'value'),
        Input('metric-selector', 'value')
    ])
    def update_metrics(n, selected_device_id, selected_metric_ids):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not selected_metric_ids:
            return (html.Div([f"資料更新時間: {current_time}",
                              html.P("請選擇監測指標")]), {
                                  'data': [],
                                  'layout': {
                                      'title': '請選擇監測指標'
                                  }
                              }, "請選擇監測指標", "")

        # 1. 獲取即時數據
        try:
            latest_data = prometheus_client.get_latest_data_for_metrics(
                selected_metric_ids)
            display_text = [f"資料更新時間: {current_time}"]
            current_values_dict = {}

            if latest_data:
                for metric_id in selected_metric_ids:
                    value = latest_data.get(metric_id)
                    if value is not None:
                        metric_name = metric_id_to_name_map.get(
                            metric_id, metric_id)
                        metric_unit = metric_id_to_unit_map.get(metric_id, "")
                        display_text.append(
                            html.P(
                                f"{metric_name}: {value:.2f} {metric_unit}"))
                        current_values_dict[metric_id] = value
                    else:
                        display_text.append(html.P(f"{metric_id}: 無數據"))
            else:
                display_text.append(html.P("未能從 Prometheus 獲取即時數據。"))
        except Exception as e:
            display_text = [
                f"資料更新時間: {current_time}",
                html.P(f"獲取數據時發生錯誤: {e}")
            ]
            current_values_dict = {}

        # 2. 獲取歷史趨勢數據
        graphs = []
        try:
            end_time = int(datetime.datetime.now().timestamp())
            start_time = end_time - 60 * 60  # 過去 1 小時的數據
            step = '1m'  # 每 1 分鐘一個數據點

            for metric_id in selected_metric_ids:
                query = f'{metric_id}{{device_id="{selected_device_id}"}}'
                history_data_prom = prometheus_client.query_range(
                    query, start_time, end_time, step)

                if history_data_prom:
                    timestamps = []
                    values = []
                    for entry in history_data_prom:
                        for ts, val in entry['values']:
                            timestamps.append(
                                datetime.datetime.fromtimestamp(float(ts)))
                            values.append(float(val))

                    if timestamps and values:
                        graphs.append(
                            go.Scatter(
                                x=timestamps,
                                y=values,
                                mode='lines+markers',
                                name=
                                f'{metric_id_to_name_map.get(metric_id, metric_id)} ({metric_id_to_unit_map.get(metric_id, "")})'
                            ))
        except Exception as e:
            print(f"獲取歷史數據時發生錯誤: {e}")

        figure = {
            'data':
            graphs,
            'layout':
            go.Layout(title=f'設備 {selected_device_id} 監測趨勢圖',
                      xaxis={'title': '時間'},
                      yaxis={'title': '值'},
                      legend={
                          'x': 0,
                          'y': 1
                      },
                      hovermode='closest')
        }

        # 3. 執行異常檢測
        anomaly_status = "正常"
        anomaly_detail_text = ""

        try:
            if anomaly_detector.model and current_values_dict:
                current_df = pd.DataFrame([current_values_dict])

                # 確保 DataFrame 包含所有訓練時使用的指標
                for m_id in metrics_for_anomaly:
                    if m_id not in current_df.columns:
                        current_df[m_id] = 0.0

                current_df = current_df[metrics_for_anomaly]
                detection_result = anomaly_detector.detect(current_df)

                if detection_result['is_anomaly']:
                    anomaly_status = html.Span("⛔ 檢測到異常！",
                                               style={'color': 'red'})
                    anomaly_detail_text = f"異常分數: {detection_result['anomaly_score']:.2f} (分數越低越異常)"
                else:
                    anomaly_status = html.Span("✅ 運行正常",
                                               style={'color': 'green'})
                    anomaly_detail_text = f"異常分數: {detection_result['anomaly_score']:.2f}"
            else:
                anomaly_status = "異常檢測模型未就緒或無數據"
        except Exception as e:
            anomaly_status = f"異常檢測時發生錯誤: {e}"

        return html.Div(
            display_text), figure, anomaly_status, anomaly_detail_text


def main():
    """主函數"""
    global app

    print("啟動儀表板應用程式...")

    # 初始化組件
    if not initialize_components():
        print("組件初始化失敗，退出程式")
        return

    # 初始化 Dash 應用 - 必須在這裡初始化
    app = dash.Dash(__name__)
    app.title = "AI智慧決策儀表板"
    print("Dash 應用初始化完成")

    # 訓練異常檢測模型
    train_anomaly_model()

    # 設定佈局
    try:
        app.layout = create_app_layout()
        print("應用佈局設定完成")
    except Exception as e:
        print(f"設定應用佈局時發生錯誤: {e}")
        return

    # 設定回調函數
    try:
        setup_callbacks()
        print("回調函數設定完成")
    except Exception as e:
        print(f"設定回調函數時發生錯誤: {e}")
        return

    # 啟動應用
    print("儀表板已準備就緒，正在啟動伺服器...")
    print("儀表板網址: http://localhost:8050")
    try:
        app.run(debug=True, host='0.0.0.0', port=8050)
    except Exception as e:
        print(f"啟動伺服器時發生錯誤: {e}")
        raise


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n收到中斷信號，正在關閉儀表板...")
    except Exception as e:
        print(f"啟動儀表板時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("儀表板已關閉")
