# ECU-1051 工業設備監控與AI智能分析系統

## 🏭 專案簡介

這是一個專為 ECU-1051 工業設備設計的智能監控系統，整合了 Modbus 通訊、Prometheus 數據收集、AI 異常檢測和實時儀表板展示功能。系統提供全方位的設備監控、預測性維護和智能決策支援。

### 核心特色

- 🔌 **多設備支援**: 支援 4 台 ECU-1051 設備同時監控
- 🤖 **AI 智能分析**: 異常檢測、趨勢預測、健康評分
- 📊 **實時儀表板**: 多種儀表板界面，支援即時數據視覺化
- 🛠️ **豐富工具集**: 設備診斷、數據分析、連線檢查工具
- 🔧 **高度可配置**: 靈活的設備和指標配置系統
- 🚀 **易於部署**: 完整的安裝和配置腳本

## 🏗️ 系統架構

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ECU-1051     │    │   ECU-1051     │    │   ECU-1051     │
│   設備 #1       │    │   設備 #2       │    │   設備 #3       │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │ Modbus TCP/IP
                                 ▼
                    ┌─────────────────────────┐
                    │    Modbus Exporter     │
                    │   (數據採集中介層)      │
                    └─────────┬───────────────┘
                              │ HTTP Metrics
                              ▼
                    ┌─────────────────────────┐
                    │     Prometheus         │
                    │   (時間序列資料庫)      │
                    └─────────┬───────────────┘
                              │ PromQL API
                              ▼
      ┌─────────────────────────────────────────────────────┐
      │                Python 監控系統                      │
      ├─────────────────┬───────────────┬───────────────────┤
      │   數據處理模組    │   AI 分析引擎   │   儀表板系統      │
      │  (DataProcessor) │ (AnomalyDetector)│ (Dash Apps)    │
      └─────────────────┴───────────────┴───────────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │      Web 儀表板        │
                    │  http://localhost:8050  │
                    └─────────────────────────┘
```

## 📁 檔案結構

```
ECU-1051-Monitor/
├── 📋 核心系統檔案
│   ├── main.py                     # 主程式入口
│   ├── config_loader.py            # 配置載入器
│   ├── data_processor.py           # 數據處理器
│   ├── anomaly_detector.py         # AI異常檢測器
│   └── prometheus_client.py        # Prometheus客戶端
│
├── 🎨 儀表板系統
│   ├── dashboard_app.py            # 主要儀表板
│   ├── ai_enhanced_dashboard.py    # AI增強版儀表板
│   ├── final_working_dashboard.py  # 最終優化版儀表板
│   ├── working_dashboard.py        # 實際工作版儀表板
│   ├── simple_dashboard_test.py    # 簡化測試版儀表板
│   ├── start_dashboard_only.py     # 單獨啟動儀表板工具
│   ├── dash_utils.py              # Dash版本相容工具
│   └── minimal_dash_test.py       # Dash測試工具
│
├── 🔧 數據客戶端
│   ├── metrics_only_client.py     # Metrics端點客戶端
│   ├── updated_prometheus_client.py # 更新版Prometheus客戶端
│   └── prometheus_debug.py        # Prometheus除錯工具
│
├── 🛠️ 診斷工具集
│   ├── check_device_connectivity.py      # 設備連線檢查
│   ├── industrial_data_diagnostics.py   # 工業數據診斷
│   ├── find_modbus_metrics.py           # Modbus指標發現
│   ├── find_relevant_metrics.py         # 相關指標搜尋
│   ├── fix_data_access.py              # 數據存取修正
│   ├── docker_prometheus_query.py       # Docker查詢工具
│   ├── correct_prometheus_query.py      # 正確查詢工具
│   ├── prometheus_raw_analysis.py       # 原始數據分析
│   └── quick_url_test.py               # 快速URL測試
│
├── ⚙️ 配置檔案
│   ├── devices.json               # 設備配置
│   ├── plc_points.json           # PLC點位配置  
│   ├── correct_plc_points.json   # 修正版點位配置
│   ├── discovered_metrics.json   # 發現的指標配置
│   ├── working_plc_points.json   # 實際工作配置
│   ├── updated_plc_points.json   # 更新版配置
│   ├── temp_plc_points.json      # 臨時測試配置
│   └── prometheus_config.json    # Prometheus配置
│
├── 🚀 安裝與部署
│   ├── setup.py                  # 自動安裝腳本
│   ├── requirements.txt          # Python套件需求
│   ├── test_modules.py           # 模組測試工具
│   ├── git_sync.sh              # Git同步腳本
│   ├── start_system.bat         # Windows啟動腳本
│   └── start_system.sh          # Linux/Mac啟動腳本
│
└── 📄 專案文件
    ├── .gitignore               # Git忽略規則
    └── README.md               # 本文件
```

## 🚀 快速開始

### 環境需求

- **Python**: 3.8+ 
- **作業系統**: Windows / Linux / macOS
- **網路**: 可存取 ECU-1051 設備的內網環境
- **記憶體**: 建議 4GB+
- **硬碟**: 1GB 可用空間

### 自動化安裝

1. **克隆專案**
   ```bash
   git clone <repository-url>
   cd ECU-1051-Monitor
   ```

2. **執行自動安裝**
   ```bash
   python setup.py
   ```
   > 安裝腳本會自動檢查環境、安裝依賴套件並建立啟動腳本

3. **啟動系統**
   - **Windows**: 雙擊 `start_system.bat`
   - **Linux/Mac**: `./start_system.sh`
   - **手動啟動**: `python main.py`

### 手動安裝

如果自動安裝失敗，可以手動執行：

```bash
# 1. 安裝依賴套件
pip install -r requirements.txt

# 2. 測試模組安裝
python minimal_dash_test.py

# 3. 啟動系統
python main.py
```

## ⚙️ 系統配置

### 設備配置 (devices.json)

系統支援多台 ECU-1051 設備，每台設備配置主要和備用 IP 地址：

```json
{
    "devices": [
        {
            "id": "ecu1051_1",
            "name": "1號機",
            "primary_ip": "10.6.118.52",
            "backup_ip": "10.6.118.53",
            "port": 502,
            "timeout": 3,
            "retry_interval": 60
        }
    ]
}
```

### PLC 點位配置 (plc_points.json)

系統監控三大類別的工業數據：

#### 🌡️ 溫度控制器 (78個監測點)
- **主控溫度**: 左側/右側主控 PV/SV
- **輔控溫度**: 4組輔控溫度監測
- **電熱室溫度**: 8個電熱室超溫監測
- **進出風溫度**: 36個進出風溫度點
- **節能箱溫度**: 廢熱回收溫度監測

#### ⚡ 馬達和壓力 (25個監測點)
- **馬達頻率**: 左右側共8個馬達頻率
- **馬達電流**: 對應的電流監測
- **壓力監測**: CDA壓力、HEPA壓差
- **流量監測**: 軸冷CDA流量、進氣風量

#### 🔌 電表數據 (13個監測點)
- **電氣參數**: 電壓、電流、功率因數
- **功率數據**: 實功率、虛功率、視在功率
- **能耗統計**: 累積功率消耗

## 🎨 儀表板系統

系統提供多種儀表板界面，滿足不同的監控需求和環境適配：

### 1. 標準監控儀表板 (Port 8050)
```bash
python dashboard_app.py
```
- **基礎功能**: 實時數據展示、歷史趨勢圖
- **設備選擇**: 支援多設備切換
- **指標監控**: 可自由選擇監控指標
- **異常檢測**: 基礎異常狀態顯示

### 2. AI 增強版儀表板 (Port 8055)
```bash
python ai_enhanced_dashboard.py
```
- **🤖 AI 分析**: 智能異常檢測與趨勢預測
- **📊 健康評分**: 系統整體健康狀況評估
- **💡 智能建議**: AI 生成的維護建議
- **🔮 趨勢預測**: 未來數值變化預測
- **⚠️ 預警系統**: 多級警報機制

### 3. 最終優化版儀表板 (Port 8054)
```bash
python final_working_dashboard.py
```
- **✨ 最佳體驗**: 優化的使用者界面
- **🎯 精準監控**: 使用實際發現的工業指標
- **📈 進階圖表**: 更豐富的數據視覺化
- **🔧 穩定性**: 經過優化的連線處理

### 4. 實際工作版儀表板 (Port 8053)
```bash
python working_dashboard.py
```
- **🔌 直接連接**: 優化的 Prometheus /metrics 端點連接
- **📊 實時指標**: 動態發現並顯示實際可用指標
- **🛠️ 智能適配**: 自動適配不同的數據源格式
- **⚡ 效能優化**: 針對 metrics 端點優化的查詢方式

### 5. 簡化測試版儀表板 (Port 8050)
```bash
python simple_dashboard_test.py
```
- **🧪 測試專用**: 用於測試基本功能
- **💡 容錯處理**: 智能處理模組匯入失敗情況
- **🔄 模擬數據**: 在沒有實際數據時提供模擬數據
- **🛡️ 相容性**: 支援新舊版本 Dash 的相容性處理

### 6. 儀表板啟動工具
```bash
python start_dashboard_only.py
```
- **🚀 智能啟動**: 嘗試多種方式啟動儀表板
- **🔧 問題診斷**: 自動診斷啟動失敗原因
- **📝 建議提供**: 提供解決方案建議
- **🛠️ 備用方案**: 多重啟動策略確保成功率

## 🤖 AI 功能詳解

### 異常檢測系統

使用 **Isolation Forest** 演算法進行無監督異常檢測：

**主要特點:**
- **即時檢測**: 對當前數據進行即時異常判斷
- **歷史學習**: 基於歷史數據訓練檢測模型
- **多指標融合**: 同時考慮多個關鍵指標
- **動態調整**: 模型可根據新數據持續更新

**監控指標:**
```python
監控指標 = [
    'left_main_temp_pv',    # 左側主控溫度
    'left_aux1a_temp_pv',   # 左側輔控1A溫度  
    'left_aux1a_ct',        # 左側輔控1A電流
    'right_main_temp_pv',   # 右側主控溫度
    'right_aux1a_temp_pv',  # 右側輔控1A溫度
    'right_aux1a_ct'        # 右側輔控1A電流
]
```

### 趨勢預測系統

使用 **線性回歸** 進行短期趨勢預測：

**預測能力:**
- **趨勢判斷**: 識別上升、下降、穩定趨勢
- **數值預測**: 預測未來10個時間點的數值
- **置信度評估**: 提供預測結果的可信度
- **視覺化展示**: 預測曲線圖表顯示

### 健康評分系統

綜合評估系統整體健康狀況：

**評分標準:**
- **基礎分數**: 100分滿分
- **異常扣分**: 每個異常扣10-20分
- **溫度評估**: 高溫/低溫額外扣分
- **等級劃分**: 
  - 90-100分: 🟢 優秀
  - 70-89分: 🟡 良好  
  - <70分: 🔴 需要關注

### 智能建議系統

根據監控數據生成維護建議：

**建議類型:**
- **溫度異常**: 檢查冷卻/加熱系統
- **電流異常**: 檢查負載和電氣系統
- **趨勢預警**: 預防性維護提醒
- **一般維護**: 定期保養建議

## 🛠️ 診斷工具集

系統提供豐富的診斷工具，幫助快速定位問題：

### 設備連線診斷
```bash
python check_device_connectivity.py
```
- **連線測試**: 檢查所有設備的網路連線
- **端口檢測**: Modbus 502 端口可達性測試
- **服務發現**: 自動尋找 Modbus Exporter 服務
- **配置建議**: 生成 Prometheus 配置建議

### 工業數據診斷  
```bash
python industrial_data_diagnostics.py
```
- **指標對比**: 期望指標 vs 實際可用指標
- **數據來源追蹤**: 分析數據採集鏈路
- **問題定位**: 快速定位數據缺失原因
- **臨時方案**: 生成可用指標的臨時配置

### Prometheus 連線除錯
```bash
python prometheus_debug.py
```
- **連線測試**: 測試 Prometheus 伺服器狀態
- **API 檢查**: 驗證各個 API 端點可用性
- **指標查詢**: 測試具體指標的查詢功能
- **效能分析**: 查詢回應時間分析

### 指標發現工具
```bash
python find_modbus_metrics.py
python find_relevant_metrics.py
```
- **自動發現**: 掃描 Prometheus 中的所有可用指標
- **智能匹配**: 根據關鍵字匹配工業監控指標
- **配置生成**: 自動生成可用的配置檔案
- **映射建議**: 提供指標名稱映射建議

### 快速測試工具
```bash
python quick_url_test.py
python prometheus_raw_analysis.py
```
- **URL 測試**: 快速驗證端點可用性
- **原始分析**: 直接分析 /metrics 端點數據
- **格式檢查**: 驗證數據格式正確性
- **內容統計**: 指標數量和類型統計

## 🔧 故障排除指南

### 常見問題與解決方案

#### 1. 儀表板無法啟動

**問題現象**: 執行 `python dashboard_app.py` 出現錯誤

**解決步驟**:
```bash
# 1. 檢查 Python 版本
python --version  # 需要 3.8+

# 2. 使用模組測試工具
python test_modules.py

# 3. 使用簡化測試版
python simple_dashboard_test.py

# 4. 使用啟動工具
python start_dashboard_only.py

# 5. 使用相容性工具
python dash_utils.py
```

#### 2. 設備連線失敗

**問題現象**: 顯示 "❌ 設備連線失敗"

**解決步驟**:
```bash
# 1. 檢查設備連線
python check_device_connectivity.py

# 2. 測試網路連通性
ping 10.6.118.52

# 3. 檢查 Modbus 端口
telnet 10.6.118.52 502

# 4. 修改設備配置
vim devices.json
```

#### 3. 數據無法取得

**問題現象**: 儀表板顯示 "無數據"

**解決步驟**:
```bash
# 1. 診斷數據來源
python industrial_data_diagnostics.py

# 2. 檢查 Prometheus 連線
python prometheus_debug.py

# 3. 測試 URL 連通性
python quick_url_test.py

# 4. 使用更新版客戶端
# 修改程式中的匯入：
# from updated_prometheus_client import PrometheusClient

# 5. 使用備用配置
cp working_plc_points.json plc_points.json
# 或
cp temp_plc_points.json plc_points.json

# 6. 使用實際工作版儀表板
python working_dashboard.py  # Port 8053
```

#### 4. AI 功能無法使用

**問題現象**: 異常檢測顯示 "模型未就緒"

**解決步驟**:
```bash
# 1. 檢查歷史數據
# 系統需要足夠的歷史數據來訓練模型

# 2. 降低數據要求
# 修改 anomaly_detector.py 中的 min_data_points

# 3. 手動訓練模型
python -c "
from anomaly_detector import AnomalyDetector
detector = AnomalyDetector(['temp_metric'])
# 手動提供訓練數據
"
```

#### 5. 指標名稱不匹配

**問題現象**: 配置中的指標在 Prometheus 中找不到

**解決步驟**:
```bash
# 1. 發現實際指標
python find_modbus_metrics.py

# 2. 修正數據存取
python fix_data_access.py

# 3. 使用映射工具
python correct_prometheus_query.py

# 4. 更新配置檔案
cp correct_plc_points.json plc_points.json
```

### 除錯技巧

#### 啟用詳細日誌
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 檢查數據流向
```bash
# 1. ECU設備 → Modbus Exporter
curl http://localhost:9602/metrics

# 2. Modbus Exporter → Prometheus  
curl http://sn.yesiang.com:9090/api/v1/query?query=up

# 3. Prometheus → Python應用
python -c "
from metrics_only_client import MetricsOnlyPrometheusClient
client = MetricsOnlyPrometheusClient()
print(client.get_available_metrics()[:10])
"
```

#### 效能調優

**記憶體使用優化**:
```python
# 限制歷史數據快取
MAX_CACHE_SIZE = 100

# 降低查詢頻率
QUERY_INTERVAL = 10  # 10秒查詢一次
```

**網路連線優化**:
```python
# 增加連線逾時
TIMEOUT = 30

# 設定重試機制
MAX_RETRIES = 3
```

## 📊 使用方法和操作指南

### 基本操作流程

#### 1. 系統啟動
```bash
# 方法一: 使用啟動腳本 (推薦)
./start_system.sh  # Linux/Mac
# 或
start_system.bat   # Windows

# 方法二: 直接啟動主程式
python main.py

# 方法三: 只啟動儀表板
python dashboard_app.py
```

#### 2. 存取儀表板
啟動後，在瀏覽器中開啟以下網址：

- **標準版**: http://localhost:8050
- **AI增強版**: http://localhost:8055  
- **最終版**: http://localhost:8054

#### 3. 基本操作

**選擇監控設備**:
- 在頂部下拉選單選擇要監控的設備
- 支援 1-4 號機切換

**選擇監測指標**:
- 在指標選擇器中勾選要監控的參數
- 支援多指標同時監控
- 不同類型指標會以不同顏色顯示

**查看即時數據**:
- 數據每 5-8 秒自動更新
- 數值異常時會變紅色顯示
- 包含單位和友好名稱

**歷史趨勢分析**:
- 圖表顯示過去 1 小時的數據變化
- 可通過滑鼠懸停查看具體數值
- 支援縮放和平移操作

### 進階功能使用

#### AI 分析功能 (AI 增強版儀表板)

**異常檢測**:
- 系統會自動標記異常數據點
- 異常指標以紅色顯示並標註 ⚠️
- 異常分數越低表示越異常

**趨勢預測**:
- 查看下方的預測圖表
- 虛線表示未來趨勢預測
- 不同指標以不同顏色區分

**健康評分**:
- 底部顯示系統整體健康狀況
- 綠色表示健康，紅色表示需要關注
- 評分基於多個指標綜合計算

**智能建議**:
- 左側面板顯示 AI 生成的建議
- 根據異常和趨勢提供維護建議
- 建議按優先級排序

#### 數據匯出

**CSV 匯出** (需自行實作):
```python
# 在 data_processor.py 中新增
def export_to_csv(self, data, filename):
    data.to_csv(filename, index=False)
```

**JSON 匯出**:
```python
# 匯出配置
import json
with open('current_config.json', 'w') as f:
    json.dump(config_data, f, indent=2)
```

#### 客製化設定

**新增監控指標**:
1. 編輯 `plc_points.json`
2. 新增指標定義
3. 重新啟動系統

**修改更新頻率**:
```python
# 在儀表板檔案中修改
dcc.Interval(
    id='interval-component',
    interval=5000,  # 5秒 (可調整)
    n_intervals=0
)
```

**調整異常檢測敏感度**:
```python
# 在 anomaly_detector.py 中修改
self.model = IsolationForest(
    contamination=0.01,  # 降低此值提高敏感度
    random_state=42
)
```

### 維護操作

#### 日常維護檢查
```bash
# 1. 檢查系統狀態
python prometheus_debug.py

# 2. 檢查設備連線
python check_device_connectivity.py

# 3. 檢查數據品質
python industrial_data_diagnostics.py
```

#### 定期維護任務
```bash
# 每週執行
# 1. 更新指標發現
python find_modbus_metrics.py

# 2. 重新訓練 AI 模型
# 系統會自動重新訓練，或手動重啟

# 3. 檢查日誌檔案大小
du -sh *.log

# 每月執行  
# 1. 備份配置檔案
cp *.json backup/

# 2. 清理暫存檔案
rm -f temp_*.json working_*.json
```

## 📷 截圖和展示

### 主要介面截圖

**標準監控儀表板**:
- 設備選擇和指標監控介面
- 即時數據展示面板
- 歷史趨勢圖表
- 系統狀態指示器

**AI 增強版儀表板**:
- AI 分析結果面板
- 異常檢測視覺化
- 趨勢預測圖表  
- 智能建議列表
- 系統健康評分

**診斷工具介面**:
- 設備連線狀態圖
- 指標發現結果
- 數據品質分析
- 問題排除建議

### 功能演示影片

**基本操作演示**:
1. 系統啟動流程
2. 設備選擇和指標配置
3. 即時數據監控
4. 歷史數據查看

**AI 功能演示**:
1. 異常檢測觸發
2. 趨勢預測展示
3. 健康評分變化
4. 智能建議生成

**故障排除演示**:
1. 連線問題診斷
2. 數據問題定位
3. 配置檔案修復
4. 系統恢復過程

## 🔧 API 文件

### 核心類別 API

#### PrometheusClient
```python
class PrometheusClient:
    def __init__(self, prometheus_url: str)
    def query_instant(self, query: str) -> dict
    def query_range(self, query: str, start_time: int, 
                   end_time: int, step: str) -> list
    def get_latest_data_for_metrics(self, metric_ids: list) -> dict
```

#### DataProcessor  
```python
class DataProcessor:
    def __init__(self, plc_points_config: dict)
    def process_latest_data(self, latest_data_dict: dict, 
                          device_id: str) -> pd.DataFrame
    def process_range_data(self, range_data_list: list, 
                         device_id: str) -> pd.DataFrame
```

#### AnomalyDetector
```python
class AnomalyDetector:
    def __init__(self, metrics_to_monitor: list, model_path: str = None)
    def train_model(self, historical_data_df: pd.DataFrame)
    def detect(self, current_data_df: pd.DataFrame) -> dict
```

### 配置檔案格式

#### devices.json
```json
{
    "devices": [
        {
            "id": "ecu1051_1",
            "name": "1號機", 
            "primary_ip": "10.6.118.52",
            "backup_ip": "10.6.118.53",
            "port": 502,
            "timeout": 3,
            "retry_interval": 60
        }
    ]
}
```

#### plc_points.json
```json
{
    "metric_groups": [
        {
            "group_name": "溫度控制器",
            "device_id": 1,
            "start_address": 40001,
            "count": 78,
            "metrics": [
                {
                    "id": "left_main_temp_pv",
                    "name": "左側主控_PV",
                    "register_offset": 0,
                    "data_type": "INT16", 
                    "scale_factor": 10.0,
                    "unit": "℃"
                }
            ]
        }
    ]
}
```

### REST API 端點

如需擴展 REST API 功能，可參考以下設計：

```python
# Flask API 擴展 (需另外實作)
@app.route('/api/devices', methods=['GET'])
def get_devices():
    return jsonify(devices)

@app.route('/api/metrics/<device_id>', methods=['GET']) 
def get_device_metrics(device_id):
    return jsonify(metrics)

@app.route('/api/anomaly/<device_id>', methods=['GET'])
def get_anomaly_status(device_id):
    return jsonify(anomaly_status)
```

## 🚀 部署和配置

### 生產環境部署

#### Docker 部署
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8050 8054 8055

CMD ["python", "main.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  ecu-monitor:
    build: .
    ports:
      - "8050:8050"
      - "8054:8054" 
      - "8055:8055"
    environment:
      - PROMETHEUS_URL=http://prometheus:9090
    networks:
      - monitoring
    
networks:
  monitoring:
    external: true
```

#### Systemd 服務部署

建立系統服務檔案：

```ini
# /etc/systemd/system/ecu-monitor.service
[Unit]
Description=ECU-1051 Monitoring System
After=network.target

[Service]
Type=simple
User=monitor
WorkingDirectory=/opt/ecu-monitor
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/ecu-monitor

[Install]
WantedBy=multi-user.target
```

啟用服務：
```bash
sudo systemctl daemon-reload
sudo systemctl enable ecu-monitor
sudo systemctl start ecu-monitor
sudo systemctl status ecu-monitor
```

#### Nginx 反向代理

```nginx
# /etc/nginx/sites-available/ecu-monitor
server {
    listen 80;
    server_name ecu-monitor.local;

    location / {
        proxy_pass http://127.0.0.1:8050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ai {
        proxy_pass http://127.0.0.1:8055;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /final {
        proxy_pass http://127.0.0.1:8054;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 效能優化配置

#### Python 優化設定

```python
# config/performance.py
import multiprocessing

# 設定處理器核心數
CPU_COUNT = multiprocessing.cpu_count()

# 資料庫連線池
DB_POOL_SIZE = 10
DB_POOL_TIMEOUT = 30

# 快取設定  
CACHE_SIZE = 1000
CACHE_TTL = 300  # 5分鐘

# 查詢優化
BATCH_SIZE = 100
QUERY_TIMEOUT = 10
```

#### 記憶體管理

```python
# 在主程式中加入記憶體監控
import psutil
import gc

def monitor_memory():
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB")
    
    # 定期清理
    if memory_info.rss > 500 * 1024 * 1024:  # 500MB
        gc.collect()
```

### 監控和日誌

#### 日誌配置

```python
# config/logging.py
import logging
from logging.handlers import RotatingFileHandler

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/ecu_monitor.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

#### 健康檢查端點

```python
# health_check.py
from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route('/health')
def health_check():
    status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {}
    }
    
    # 檢查 Prometheus
    try:
        response = requests.get('http://sn.yesiang.com:9090/api/v1/status/config', timeout=5)
        status['services']['prometheus'] = 'up' if response.status_code == 200 else 'down'
    except:
        status['services']['prometheus'] = 'down'
    
    # 檢查設備連線
    try:
        from check_device_connectivity import check_modbus_connectivity
        results = check_modbus_connectivity()
        connected = sum(1 for r in results if r['any_connected'])
        status['services']['devices'] = f"{connected}/{len(results)} connected"
    except:
        status['services']['devices'] = 'unknown'
    
    return jsonify(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8060)
```

## 🔒 安全性配置

### 網路安全

#### 防火牆規則
```bash
# Ubuntu/Debian
sudo ufw allow 8050/tcp  # 主儀表板
sudo ufw allow 8054/tcp  # 最終版儀表板  
sudo ufw allow 8055/tcp  # AI增強版儀表板
sudo ufw allow from 10.6.118.0/24 to any port 502  # Modbus設備

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8050/tcp
sudo firewall-cmd --permanent --add-port=8054/tcp
sudo firewall-cmd --permanent --add-port=8055/tcp
sudo firewall-cmd --reload
```

#### SSL/TLS 配置

```python
# 在 Dash 應用中啟用 HTTPS
if __name__ == '__main__':
    app.run_server(
        debug=False, 
        host='0.0.0.0', 
        port=8050,
        ssl_context='adhoc'  # 或使用證書檔案
    )
```

### 存取控制

#### 基本認證

```python
# auth.py
import dash_auth

# 使用者認證
VALID_USERNAME_PASSWORD_PAIRS = {
    'admin': 'password123',
    'operator': 'operator123'
}

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)
```

#### 角色權限控制

```python
# rbac.py
from functools import wraps
from flask import session, request, abort

def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# 使用範例
@require_role('admin')
def admin_only_function():
    pass
```

### 資料保護

#### 敏感資料加密

```python
# encryption.py
from cryptography.fernet import Fernet

class DataEncryption:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt_config(self, config_data):
        return self.cipher.encrypt(json.dumps(config_data).encode())
    
    def decrypt_config(self, encrypted_data):
        return json.loads(self.cipher.decrypt(encrypted_data).decode())
```

#### 備份策略

```bash
#!/bin/bash
# backup.sh - 自動備份腳本

BACKUP_DIR="/backup/ecu-monitor"
DATE=$(date +%Y%m%d_%H%M%S)

# 建立備份目錄
mkdir -p $BACKUP_DIR

# 備份配置檔案
tar -czf $BACKUP_DIR/config_$DATE.tar.gz *.json

# 備份日誌檔案  
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# 清理舊備份 (保留30天)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

## 📈 效能監控

### 系統指標監控

#### 資源使用監控

```python
# performance_monitor.py
import psutil
import time
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        
    def get_system_metrics(self):
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters(),
            'uptime': time.time() - self.start_time
        }
    
    def get_process_metrics(self):
        process = psutil.Process()
        return {
            'cpu_percent': process.cpu_percent(),
            'memory_info': process.memory_info(),
            'num_threads': process.num_threads(),
            'open_files': len(process.open_files())
        }
```

#### 應用程式效能監控

```python
# app_monitor.py
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        if execution_time > 1.0:  # 超過1秒的操作記錄警告
            logging.warning(f"{func.__name__} took {execution_time:.2f} seconds")
        
        return result
    return wrapper

# 使用範例
@monitor_performance
def expensive_operation():
    time.sleep(2)
```

### 資料庫效能

#### 查詢優化

```python
# query_optimizer.py
import time
from collections import defaultdict

class QueryOptimizer:
    def __init__(self):
        self.query_stats = defaultdict(list)
    
    def track_query(self, query, execution_time):
        self.query_stats[query].append(execution_time)
    
    def get_slow_queries(self, threshold=1.0):
        slow_queries = {}
        for query, times in self.query_stats.items():
            avg_time = sum(times) / len(times)
            if avg_time > threshold:
                slow_queries[query] = {
                    'avg_time': avg_time,
                    'max_time': max(times),
                    'count': len(times)
                }
        return slow_queries
```

#### 連線池管理

```python
# connection_pool.py
import threading
from queue import Queue

class ConnectionPool:
    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self.pool = Queue(maxsize=max_connections)
        self.active_connections = 0
        self.lock = threading.Lock()
    
    def get_connection(self):
        with self.lock:
            if not self.pool.empty():
                return self.pool.get()
            elif self.active_connections < self.max_connections:
                conn = self.create_connection()
                self.active_connections += 1
                return conn
            else:
                # 等待可用連線
                return self.pool.get(timeout=30)
    
    def return_connection(self, conn):
        self.pool.put(conn)
    
    def create_connection(self):
        # 建立實際連線的邏輯
        pass
```

## 🧪 測試和品質保證

### 單元測試

#### 測試框架設定

```python
# tests/test_data_processor.py
import unittest
import pandas as pd
from data_processor import DataProcessor

class TestDataProcessor(unittest.TestCase):
    def setUp(self):
        self.plc_config = {
            "metric_groups": [{
                "group_name": "test",
                "metrics": [{
                    "id": "test_metric",
                    "name": "Test Metric",
                    "unit": "°C",
                    "data_type": "INT16",
                    "scale_factor": 10.0
                }]
            }]
        }
        self.processor = DataProcessor(self.plc_config)
    
    def test_process_latest_data(self):
        test_data = {"test_metric": 25.5}
        result = self.processor.process_latest_data(test_data, "test_device")
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.iloc[0]["test_metric"], 25.5)
        self.assertEqual(result.iloc[0]["device_id"], "test_device")

if __name__ == '__main__':
    unittest.main()
```

#### 異常檢測測試

```python
# tests/test_anomaly_detector.py
import unittest
import numpy as np
import pandas as pd
from anomaly_detector import AnomalyDetector

class TestAnomalyDetector(unittest.TestCase):
    def setUp(self):
        self.metrics = ['metric1', 'metric2']
        self.detector = AnomalyDetector(self.metrics)
    
    def test_train_model(self):
        # 建立測試數據
        data = pd.DataFrame({
            'metric1': np.random.normal(50, 5, 100),
            'metric2': np.random.normal(30, 3, 100),
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='1H'),
            'device_id': ['test'] * 100
        })
        
        self.detector.train_model(data)
        self.assertIsNotNone(self.detector.model)
    
    def test_detect_anomaly(self):
        # 先訓練模型
        self.test_train_model()
        
        # 測試正常數據
        normal_data = pd.DataFrame({
            'metric1': [52.0],
            'metric2': [31.0]
        })
        result = self.detector.detect(normal_data)
        self.assertFalse(result['is_anomaly'])
        
        # 測試異常數據
        anomaly_data = pd.DataFrame({
            'metric1': [100.0],  # 明顯異常值
            'metric2': [5.0]     # 明顯異常值
        })
        result = self.detector.detect(anomaly_data)
        self.assertTrue(result['is_anomaly'])

if __name__ == '__main__':
    unittest.main()
```

### 整合測試

#### 端到端測試

```python
# tests/test_integration.py
import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

class TestDashboardIntegration(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()
        self.dashboard_url = "http://localhost:8050"
    
    def tearDown(self):
        self.driver.quit()
    
    def test_dashboard_loads(self):
        self.driver.get(self.dashboard_url)
        time.sleep(2)
        
        # 檢查標題
        title = self.driver.find_element(By.TAG_NAME, "h1")
        self.assertIn("工業設備智慧決策儀表板", title.text)
    
    def test_device_selection(self):
        self.driver.get(self.dashboard_url)
        time.sleep(2)
        
        # 測試設備選擇
        device_dropdown = self.driver.find_element(By.ID, "device-selector")
        device_dropdown.click()
        
        options = device_dropdown.find_elements(By.TAG_NAME, "option")
        self.assertGreater(len(options), 0)
    
    def test_data_updates(self):
        self.driver.get(self.dashboard_url)
        time.sleep(5)  # 等待初始數據載入
        
        # 獲取初始數據
        initial_time = self.driver.find_element(By.ID, "live-update-text").text
        
        # 等待數據更新
        time.sleep(10)
        
        # 檢查數據是否更新
        updated_time = self.driver.find_element(By.ID, "live-update-text").text
        self.assertNotEqual(initial_time, updated_time)

if __name__ == '__main__':
    unittest.main()
```

### 效能測試

#### 負載測試

```python
# tests/test_performance.py
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor

def load_test_dashboard(url, num_requests=100, num_threads=10):
    """對儀表板進行負載測試"""
    
    def make_request():
        try:
            response = requests.get(url, timeout=10)
            return response.status_code, response.elapsed.total_seconds()
        except Exception as e:
            return 500, 10.0
    
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_request = {executor.submit(make_request): i for i in range(num_requests)}
        
        for future in future_to_request:
            status_code, response_time = future.result()
            results.append((status_code, response_time))
    
    end_time = time.time()
    
    # 分析結果
    successful_requests = sum(1 for status, _ in results if status == 200)
    avg_response_time = sum(time for _, time in results) / len(results)
    max_response_time = max(time for _, time in results)
    
    print(f"負載測試結果:")
    print(f"總請求數: {num_requests}")
    print(f"成功請求數: {successful_requests}")
    print(f"成功率: {successful_requests/num_requests*100:.1f}%")
    print(f"平均回應時間: {avg_response_time:.2f}秒")
    print(f"最大回應時間: {max_response_time:.2f}秒")
    print(f"總執行時間: {end_time-start_time:.2f}秒")

if __name__ == '__main__':
    load_test_dashboard("http://localhost:8050")
```

### 自動化測試

#### CI/CD 流水線

```yaml
# .github/workflows/test.yml
name: ECU Monitor Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov selenium
    
    - name: Run unit tests
      run: |
        pytest tests/test_*.py -v --cov=.
    
    - name: Run integration tests
      run: |
        # 啟動服務
        python main.py &
        sleep 10
        
        # 執行整合測試
        pytest tests/test_integration.py -v
        
        # 關閉服務
        pkill -f "python main.py"
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## 📚 相關資源和參考

### 官方文檔

- **Dash Framework**: https://dash.plotly.com/
- **Plotly Graphing**: https://plotly.com/python/
- **Pandas**: https://pandas.pydata.org/docs/
- **Scikit-learn**: https://scikit-learn.org/stable/
- **Prometheus**: https://prometheus.io/docs/

### 工業通訊協定

- **Modbus Protocol**: https://modbus.org/
- **Modbus TCP**: https://www.modbus.org/docs/Modbus_Messaging_Implementation_Guide_V1_0b.pdf
- **Modbus Exporter**: https://github.com/RichiH/modbus_exporter

### 機器學習資源

- **Isolation Forest**: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html
- **Anomaly Detection**: https://scikit-learn.org/stable/modules/outlier_detection.html
- **Time Series Analysis**: https://pandas.pydata.org/docs/user_guide/timeseries.html

### 開發工具

- **Python Best Practices**: https://docs.python-guide.org/
- **Flask Development**: https://flask.palletsprojects.com/
- **Docker**: https://docs.docker.com/
- **Git**: https://git-scm.com/doc

## 🤝 貢獻指南

### 開發環境設定

```bash
# 1. Fork 並 clone 儲存庫
git clone https://github.com/yourusername/ECU-1051-Monitor.git
cd ECU-1051-Monitor

# 2. 建立開發環境
python -m venv venv_dev
source venv_dev/bin/activate  # Linux/Mac
# 或 venv_dev\Scripts\activate  # Windows

# 3. 安裝開發依賴
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy

# 4. 安裝pre-commit hooks
pre-commit install
```

### 程式碼規範

#### Python 程式碼風格

```python
# 使用 Black 進行程式碼格式化
black *.py

# 使用 Flake8 進行 linting
flake8 *.py --max-line-length=88

# 使用 mypy 進行類型檢查
mypy *.py
```

#### 提交規範

```bash
feat: 新增功能
fix: 修復錯誤
docs: 文檔更新
style: 程式碼格式修改
refactor: 程式碼重構
test: 測試相關
chore: 建置過程或輔助工具的變動
```

### 提交流程

1. **建立功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **開發和測試**
   ```bash
   # 執行測試
   pytest tests/
   
   # 檢查程式碼品質
   black --check *.py
   flake8 *.py
   ```

3. **提交變更**
   ```bash
   git add .
   git commit -m "feat: 新增XX功能"
   git push origin feature/your-feature-name
   ```

4. **建立 Pull Request**
   - 在 GitHub 上建立 PR
   - 描述變更內容
   - 等待 code review

### 問題回報

請使用 GitHub Issues 回報問題，並包含：

- **環境資訊**: 作業系統、Python 版本
- **錯誤描述**: 詳細的錯誤訊息
- **重現步驟**: 如何重現問題
- **期望結果**: 期望的行為
- **螢幕截圖**: 如果適用

## 📝 版本更新記錄

### v2.1.0 (2024-12-XX)
- ✨ 新增 AI 增強版儀表板
- 🤖 整合異常檢測和趨勢預測
- 📊 新增系統健康評分功能
- 🛠️ 改善診斷工具集
- 🔧 優化效能和穩定性

### v2.0.0 (2024-11-XX)
- 🚀 完全重寫的儀表板系統
- 📱 響應式設計支援
- 🔌 支援多設備同時監控
- 📈 進階數據視覺化
- 🛡️ 新增安全性功能

### v1.5.0 (2024-10-XX)
- 🔍 新增豐富的診斷工具
- 📊 改善數據處理效能
- 🐛 修復多項已知問題
- 📖 完善文檔和使用指南

### v1.0.0 (2024-09-XX)
- 🎉 首次發布
- 🏭 基礎工業設備監控功能
- 📊 Prometheus 數據整合
- 🌐 Web 儀表板界面

## 📄 授權條款

本專案採用 MIT 授權條款，詳見 [LICENSE](LICENSE) 檔案。

### MIT License

```
Copyright (c) 2024 ECU-1051 Monitoring System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 📞 技術支援

### 聯絡方式

- **GitHub Issues**: 在專案頁面提交問題
- **Email**: support@ecu-monitor.com (如果適用)
- **文檔**: 參考本 README 和程式碼註解

### 常見問題 FAQ

**Q: 系統支援哪些作業系統？**
A: 支援 Windows、Linux 和 macOS，推薦 Ubuntu 18.04+ 或 Windows 10+。

**Q: 最低硬體需求是什麼？**
A: CPU: 2核心, RAM: 4GB, 硬碟: 1GB，網路連線到設備。

**Q: 可以監控多少台設備？**
A: 目前設計支援 4 台 ECU-1051 設備，可以根據需要擴展。

**Q: 數據多久更新一次？**
A: 預設每 5-8 秒更新一次，可在配置中調整。

**Q: 支援歷史數據查詢嗎？**
A: 支援，可查詢 Prometheus 中儲存的歷史數據。

**Q: AI 功能需要額外配置嗎？**
A: 不需要，系統會自動訓練模型，但需要足夠的歷史數據。

### 技術社群

- **Stack Overflow**: 使用 `ecu-1051-monitor` 標籤
- **Reddit**: r/IndustrialAutomation
- **Discord**: 工業自動化技術討論群

---

## 🏁 結語

ECU-1051 工業設備監控與AI智能分析系統是一個功能完整、易於使用的工業監控解決方案。透過整合現代 Web 技術、機器學習算法和工業通訊協定，為工業設備提供了全方位的智能監控能力。

系統的設計理念是**簡單易用**但**功能強大**，既適合技術人員進行深度分析，也適合操作人員進行日常監控。豐富的診斷工具和詳細的文檔確保了系統的可維護性和可擴展性。

我們期望這個系統能夠幫助提升工業設備的運行效率，降低維護成本，並為預測性維護提供有力支援。

**立即開始使用，體驗智能工業監控的強大功能！** 🚀

---

*最後更新：2024年12月*  
*版本：v2.1.0*  
*維護者：ECU Monitor Development Team*