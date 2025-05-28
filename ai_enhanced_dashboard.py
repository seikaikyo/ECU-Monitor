#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 在檔案開頭加入這行來忽略類型檢查
# type: ignore
"""
AI 增強版 ECU 監控儀表板
添加智慧分析、預測和建議功能
"""

import sys
import datetime
import pandas as pd
import time
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
import warnings

warnings.filterwarnings('ignore')

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

# AI 增強的 Prometheus 客戶端
import requests


class AIEnhancedPrometheusClient:
    """AI 增強的 Prometheus 客戶端"""

    def __init__(self, prometheus_url="http://sn.yesiang.com:9090"):
        self.prometheus_url = prometheus_url
        self.available = self._test_connection()
        self.historical_data = {}  # 儲存歷史數據用於 AI 分析
        print(f"初始化 AI 增強 Prometheus 客戶端: {prometheus_url}")
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
        """獲取指標的最新數據並儲存到歷史記錄"""
        if not self.available:
            return {metric_id: None for metric_id in metric_ids}

        latest_data = {}
        current_time = time.time()

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
                            value = float(result[0]['value'][1])
                            latest_data[metric_id] = value

                            # 儲存到歷史數據
                            if metric_id not in self.historical_data:
                                self.historical_data[metric_id] = []

                            self.historical_data[metric_id].append({
                                'timestamp':
                                current_time,
                                'value':
                                value
                            })

                            # 只保留最近 100 個數據點
                            if len(self.historical_data[metric_id]) > 100:
                                self.historical_data[
                                    metric_id] = self.historical_data[
                                        metric_id][-100:]
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


class ECUAIAnalyzer:
    """ECU AI 分析器"""

    def __init__(self):
        self.anomaly_detector = IsolationForest(contamination=0.1,
                                                random_state=42)
        self.trend_predictors = {}
        self.is_trained = False
        print("🤖 AI 分析器初始化完成")

    def analyze_data(self, historical_data, current_data):
        """執行 AI 分析，包括異常檢測、趨勢預測和智慧建議"""
        analysis_results = {
            'anomalies': [],
            'predictions': {},
            'recommendations': [],
            'health_score': 100,
            'alerts': []
        }

        if not historical_data or not current_data:
            return analysis_results

        # 1. 異常檢測
        anomalies = self._detect_anomalies(historical_data, current_data)
        analysis_results['anomalies'] = anomalies

        # 2. 趨勢預測
        predictions = self._predict_trends(historical_data)
        analysis_results['predictions'] = predictions

        # 3. 健康評分
        health_score = self._calculate_health_score(current_data, anomalies)
        analysis_results['health_score'] = health_score

        # 4. 智慧建議
        recommendations = self._generate_recommendations(
            current_data, anomalies, predictions)
        analysis_results['recommendations'] = recommendations

        # 5. 警報生成
        alerts = self._generate_alerts(current_data, anomalies, health_score)
        analysis_results['alerts'] = alerts

        return analysis_results

    def _detect_anomalies(self, historical_data, current_data):
        """異常檢測"""
        anomalies = []

        try:
            # 準備訓練數據
            training_data = []
            for metric_id, history in historical_data.items():
                if len(history) >= 10:  # 至少需要 10 個數據點
                    values = [
                        point['value'] for point in history
                        if point['value'] is not None
                    ]
                    if values:
                        training_data.extend(values)

            if len(training_data) >= 20:
                # 訓練異常檢測模型
                X = np.array(training_data).reshape(-1, 1)
                self.anomaly_detector.fit(X)
                self.is_trained = True

                # 檢測當前數據
                for metric_id, value in current_data.items():
                    if value is not None:
                        prediction = self.anomaly_detector.predict([[value]])
                        if prediction[0] == -1:  # 異常
                            anomaly_score = self.anomaly_detector.decision_function(
                                [[value]])[0]
                            anomalies.append({
                                'metric':
                                metric_id,
                                'value':
                                value,
                                'score':
                                abs(anomaly_score),
                                'severity':
                                'high'
                                if abs(anomaly_score) > 0.5 else 'medium'
                            })
        except Exception as e:
            print(f"異常檢測錯誤: {e}")

        return anomalies

    def _predict_trends(self, historical_data):
        """趨勢預測"""
        predictions = {}

        for metric_id, history in historical_data.items():
            if len(history) >= 10:
                try:
                    timestamps = [point['timestamp'] for point in history]
                    values = [
                        point['value'] for point in history
                        if point['value'] is not None
                    ]

                    if len(values) >= 5:
                        # 準備線性回歸數據
                        X = np.array(range(len(values))).reshape(-1, 1)
                        y = np.array(values)

                        # 訓練模型
                        model = LinearRegression()
                        model.fit(X, y)

                        # 預測未來 10 個時間點
                        future_X = np.array(
                            range(len(values),
                                  len(values) + 10)).reshape(-1, 1)
                        future_predictions = model.predict(future_X)

                        # 計算趨勢
                        trend = 'stable'
                        if model.coef_[0] > 0.1:
                            trend = 'increasing'
                        elif model.coef_[0] < -0.1:
                            trend = 'decreasing'

                        predictions[metric_id] = {
                            'trend':
                            trend,
                            'slope':
                            float(model.coef_[0]),
                            'future_values':
                            future_predictions.tolist(),
                            'confidence':
                            min(0.95, max(0.5, 1 - abs(model.coef_[0]) * 0.1))
                        }
                except Exception as e:
                    print(f"預測 {metric_id} 趨勢時發生錯誤: {e}")

        return predictions

    def _calculate_health_score(self, current_data, anomalies):
        """計算系統健康評分"""
        base_score = 100

        # 根據異常數量扣分
        anomaly_penalty = len(anomalies) * 10
        base_score -= anomaly_penalty

        # 根據異常嚴重程度額外扣分
        for anomaly in anomalies:
            if anomaly['severity'] == 'high':
                base_score -= 15
            elif anomaly['severity'] == 'medium':
                base_score -= 5

        # 根據溫度範圍評估
        temp_metrics = [k for k in current_data.keys() if 'temp' in k.lower()]
        for metric in temp_metrics:
            value = current_data.get(metric)
            if value is not None:
                if value > 80:  # 高溫警告
                    base_score -= 20
                elif value > 70:  # 溫度偏高
                    base_score -= 10
                elif value < 10:  # 溫度異常低
                    base_score -= 15

        return max(0, base_score)

    def _generate_recommendations(self, current_data, anomalies, predictions):
        """生成智慧建議"""
        recommendations = []

        # 基於異常的建議
        for anomaly in anomalies:
            metric = anomaly['metric']
            value = anomaly['value']

            if 'temp' in metric.lower():
                if value > 70:
                    recommendations.append({
                        'type': 'temperature_high',
                        'message': f'{metric} 溫度過高 ({value:.1f}℃)，建議檢查冷卻系統',
                        'priority': 'high'
                    })
                elif value < 10:
                    recommendations.append({
                        'type': 'temperature_low',
                        'message': f'{metric} 溫度異常低 ({value:.1f}℃)，建議檢查加熱系統',
                        'priority': 'medium'
                    })

            elif 'current' in metric.lower():
                if value > 15:
                    recommendations.append({
                        'type': 'current_high',
                        'message': f'{metric} 電流過高 ({value:.1f}A)，建議檢查負載',
                        'priority': 'high'
                    })

        # 基於趨勢的建議
        for metric, prediction in predictions.items():
            if prediction['trend'] == 'increasing' and 'temp' in metric.lower(
            ):
                recommendations.append({
                    'type': 'trend_warning',
                    'message': f'{metric} 呈上升趋势，建议预防性维护',
                    'priority': 'medium'
                })
            elif prediction[
                    'trend'] == 'decreasing' and 'current' in metric.lower():
                recommendations.append({
                    'type': 'performance_decline',
                    'message': f'{metric} 呈下降趋势，可能需要检查设备效率',
                    'priority': 'low'
                })

        # 一般性維護建議
        if not anomalies:
            recommendations.append({
                'type': 'maintenance',
                'message': '系統運行正常，建議定期檢查和保養',
                'priority': 'low'
            })

        return recommendations[:5]  # 限制建議數量

    def _generate_alerts(self, current_data, anomalies, health_score):
        """生成警報"""
        alerts = []

        if health_score < 60:
            alerts.append({
                'level': 'critical',
                'message': f'系統健康評分過低 ({health_score}/100)，需要立即檢查'
            })
        elif health_score < 80:
            alerts.append({
                'level': 'warning',
                'message': f'系統健康評分偏低 ({health_score}/100)，建議檢查'
            })

        for anomaly in anomalies:
            if anomaly['severity'] == 'high':
                alerts.append({
                    'level': 'critical',
                    'message': f'{anomaly["metric"]} 檢測到嚴重異常'
                })

        return alerts


# 初始化組件
print("正在初始化 AI 增強組件...")
prometheus_client = AIEnhancedPrometheusClient("http://sn.yesiang.com:9090")
ai_analyzer = ECUAIAnalyzer()

# 實際工業指標（從您的系統中發現的）
discovered_metrics = {
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
    "motor_freq_right_1b": {
        "name": "右側馬達1B頻率",
        "unit": "Hz"
    },
    "motor_current_right_2a": {
        "name": "右側馬達2A電流",
        "unit": "A"
    },
    "damper_cda_pressure": {
        "name": "風門CDA壓力",
        "unit": "kPa"
    },
    "hepa_pressure_left": {
        "name": "HEPA壓差左",
        "unit": "Pa"
    },
}

# 建立設備和指標選項
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

metric_options = []
for metric_id, info in discovered_metrics.items():
    metric_options.append({'label': info['name'], 'value': metric_id})

print("✅ AI 增強組件初始化完成")

# 初始化 Dash 應用
app = dash.Dash(__name__)
app.title = "ECU AI 智慧監控儀表板"

# AI 增強的佈局
app.layout = html.Div([
    html.H1("🤖 ECU AI 智慧監控儀表板",
            style={
                'textAlign': 'center',
                'color': '#2E86C1'
            }),
    html.Div([
        html.P("🚀 AI 驅動的智慧分析與預測",
               style={
                   'textAlign': 'center',
                   'color': '#8E44AD',
                   'fontWeight': 'bold',
                   'fontSize': '16px'
               })
    ]),

    # 控制面板
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
                dcc.Dropdown(id='metric-selector',
                             options=metric_options,
                             value=[
                                 metric_options[0]['value'],
                                 metric_options[1]['value']
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

    # AI 分析結果面板
    html.Div([
        html.Div([
            html.H4("🤖 AI 分析結果",
                    style={
                        'color': '#8E44AD',
                        'textAlign': 'center'
                    }),
            html.Div(id='ai-analysis',
                     style={
                         'padding': '15px',
                         'backgroundColor': '#F8F9FA',
                         'borderRadius': '5px'
                     })
        ],
                 style={
                     'width': '48%',
                     'display': 'inline-block',
                     'padding': '10px'
                 }),
        html.Div(
            [
                html.H4("📊 即時數據",
                        style={
                            'color': '#2E86C1',
                            'textAlign': 'center'
                        }),
                html.Div(id='status-display',
                         style={
                             'padding': '15px',
                             'backgroundColor': '#F8F9FA',
                             'borderRadius': '5px'
                         })
            ],
            style={
                'width': '48%',
                'float': 'right',
                'display': 'inline-block',
                'padding': '10px'
            })
    ],
             style={'marginBottom': '20px'}),

    # 圖表區域
    html.Div([dcc.Graph(id='data-graph', style={'height': '400px'})],
             style={'margin': '20px'}),

    # 預測圖表
    html.Div([dcc.Graph(id='prediction-graph', style={'height': '300px'})],
             style={'margin': '20px'}),

    # 系統健康狀態
    html.Div([
        html.H4('🏥 系統健康狀態', style={
            'textAlign': 'center',
            'color': '#27AE60'
        }),
        html.Div(id='health-status',
                 style={
                     'textAlign': 'center',
                     'fontSize': '24px',
                     'fontWeight': 'bold',
                     'padding': '20px'
                 })
    ]),

    # 自動更新
    dcc.Interval(id='interval-component', interval=8000,
                 n_intervals=0)  # 8秒更新，給 AI 分析更多時間
])


# AI 增強的回調函數
@app.callback([
    Output('status-display', 'children'),
    Output('data-graph', 'figure'),
    Output('ai-analysis', 'children'),
    Output('prediction-graph', 'figure'),
    Output('health-status', 'children')
], [
    Input('interval-component', 'n_intervals'),
    Input('device-selector', 'value'),
    Input('metric-selector', 'value')
])
def update_ai_dashboard(n, selected_device, selected_metrics):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not selected_metrics:
        return (html.P("請選擇監測指標"), {
            'data': [],
            'layout': {
                'title': '請選擇監測指標'
            }
        }, html.P("等待數據選擇..."), {
            'data': [],
            'layout': {
                'title': '預測分析'
            }
        }, html.Span("⚠️ 請選擇監測指標", style={'color': 'orange'}))

    # 獲取數據
    try:
        latest_data = prometheus_client.get_latest_data_for_metrics(
            selected_metrics)

        # 執行 AI 分析
        ai_results = ai_analyzer.analyze_data(
            prometheus_client.historical_data, latest_data)

        # 準備狀態顯示
        status_elements = [
            html.H6(f"更新時間: {current_time}", style={'color': '#2C3E50'})
        ]
        valid_data_count = 0

        for metric_id in selected_metrics:
            value = latest_data.get(metric_id)
            name = discovered_metrics.get(metric_id, {}).get('name', metric_id)
            unit = discovered_metrics.get(metric_id, {}).get('unit', '')

            if value is not None:
                # 檢查是否為異常值
                is_anomaly = any(a['metric'] == metric_id
                                 for a in ai_results['anomalies'])
                color = '#E74C3C' if is_anomaly else '#27AE60'

                status_elements.append(
                    html.Div([
                        html.Span(f"{name}: ", style={'fontWeight': 'bold'}),
                        html.Span(f"{value:.2f} {unit}",
                                  style={
                                      'color': color,
                                      'fontWeight': 'bold'
                                  }),
                        html.Span(" ⚠️", style={'color': '#E74C3C'})
                        if is_anomaly else None
                    ],
                             style={
                                 'margin': '3px 0',
                                 'fontSize': '13px'
                             }))
                valid_data_count += 1

        # AI 分析結果顯示
        ai_elements = []

        # 異常檢測結果
        if ai_results['anomalies']:
            ai_elements.append(html.H6("🚨 檢測到異常:", style={'color': '#E74C3C'}))
            for anomaly in ai_results['anomalies']:
                ai_elements.append(
                    html.
                    P(f"• {anomaly['metric']}: {anomaly['value']:.2f} ({anomaly['severity']})",
                      style={
                          'fontSize': '12px',
                          'margin': '2px 0'
                      }))
        else:
            ai_elements.append(
                html.P("✅ 未檢測到異常",
                       style={
                           'color': '#27AE60',
                           'fontSize': '12px'
                       }))

        # 智慧建議
        if ai_results['recommendations']:
            ai_elements.append(
                html.H6("💡 AI 建議:",
                        style={
                            'color': '#8E44AD',
                            'marginTop': '10px'
                        }))
            for rec in ai_results['recommendations'][:3]:
                priority_color = {
                    'high': '#E74C3C',
                    'medium': '#F39C12',
                    'low': '#3498DB'
                }.get(rec['priority'], '#34495E')
                ai_elements.append(
                    html.P(f"• {rec['message']}",
                           style={
                               'fontSize': '11px',
                               'margin': '2px 0',
                               'color': priority_color
                           }))

        # 趨勢預測圖表
        prediction_graphs = []
        for metric_id, prediction in ai_results['predictions'].items():
            if metric_id in selected_metrics:
                future_times = [
                    datetime.datetime.now() + datetime.timedelta(minutes=i * 2)
                    for i in range(10)
                ]
                prediction_graphs.append(
                    go.Scatter(
                        x=future_times,
                        y=prediction['future_values'],
                        mode='lines',
                        name=
                        f"{discovered_metrics.get(metric_id, {}).get('name', metric_id)} 預測",
                        line=dict(dash='dash', width=2)))

        prediction_figure = {
            'data':
            prediction_graphs,
            'layout':
            go.Layout(title='🔮 AI 趨勢預測',
                      xaxis={'title': '時間'},
                      yaxis={'title': '預測值'},
                      height=300)
        }

        # 主要數據圖表（與之前相同，但加上異常標記）
        graphs = []
        colors = ['#3498DB', '#E74C3C', '#2ECC71', '#F39C12']

        for i, metric_id in enumerate(selected_metrics):
            if metric_id in latest_data and latest_data[metric_id] is not None:
                try:
                    history_data = prometheus_client.query_range(
                        metric_id,
                        int(time.time()) - 3600, int(time.time()), '2m')

                    if history_data and len(
                            history_data) > 0 and 'values' in history_data[0]:
                        timestamps = []
                        values = []

                        for ts, val in history_data[0]['values']:
                            timestamps.append(
                                datetime.datetime.fromtimestamp(float(ts)))
                            values.append(float(val))

                        if timestamps and values:
                            # 標記異常點
                            is_anomaly = any(a['metric'] == metric_id
                                             for a in ai_results['anomalies'])
                            line_color = '#E74C3C' if is_anomaly else colors[
                                i % len(colors)]

                            graphs.append(
                                go.Scatter(
                                    x=timestamps,
                                    y=values,
                                    mode='lines+markers',
                                    name=discovered_metrics.get(
                                        metric_id, {}).get('name', metric_id),
                                    line=dict(color=line_color,
                                              width=3 if is_anomaly else 2),
                                    marker=dict(size=6 if is_anomaly else 4)))
                except Exception as e:
                    print(f"獲取歷史數據失敗: {e}")

        figure = {
            'data':
            graphs,
            'layout':
            go.Layout(title='📈 即時監測數據 (AI 增強)',
                      xaxis={'title': '時間'},
                      yaxis={'title': '數值'},
                      hovermode='x unified',
                      height=400)
        }

        # 健康狀態
        health_score = ai_results['health_score']
        if health_score >= 90:
            health_status = html.Span(f"🟢 優秀 ({health_score}/100)",
                                      style={'color': '#27AE60'})
        elif health_score >= 70:
            health_status = html.Span(f"🟡 良好 ({health_score}/100)",
                                      style={'color': '#F39C12'})
        else:
            health_status = html.Span(f"🔴 需要關注 ({health_score}/100)",
                                      style={'color': '#E74C3C'})

        return status_elements, figure, ai_elements, prediction_figure, health_status

    except Exception as e:
        print(f"更新儀表板時發生錯誤: {e}")
        return (html.P("數據獲取錯誤"), {
            'data': [],
            'layout': {
                'title': '數據錯誤'
            }
        }, html.P("AI 分析暫停"), {
            'data': [],
            'layout': {
                'title': '預測分析'
            }
        }, html.Span("❌ 系統錯誤", style={'color': 'red'}))


def safe_run_app():
    """安全啟動應用"""
    try:
        app.run(debug=False, host='0.0.0.0', port=8055)
    except AttributeError:
        app.run_server(debug=False, host='0.0.0.0', port=8055)


if __name__ == '__main__':
    print("🤖 ECU AI 智慧監控儀表板準備就緒！")
    print("儀表板網址: http://localhost:8055")
    print("🧠 AI 功能包括:")
    print("  • 異常檢測 (Isolation Forest)")
    print("  • 趨勢預測 (線性回歸)")
    print("  • 智慧建議生成")
    print("  • 系統健康評分")
    print("  • 預測性維護提醒")

    try:
        print("正在啟動 AI 增強伺服器...")
        safe_run_app()
    except KeyboardInterrupt:
        print("\n🤖 AI 儀表板已停止")
    except Exception as e:
        print(f"啟動 AI 儀表板時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
