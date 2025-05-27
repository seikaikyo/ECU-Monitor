import struct
import json
import time
import logging
import concurrent.futures
from pathlib import Path
from pymodbus.client import ModbusTcpClient
from prometheus_client import start_http_server, Gauge, Counter

# 設定記錄
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("collector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ModbusCollector:
    def __init__(self, devices_file="devices.json", points_file="plc_points.json"):
        """初始化 Modbus 收集器"""
        self.metrics = {}  # 存儲所有指標
        self.connections = {}  # 存儲設備連接狀態

        # 載入設備和點位配置
        self.load_config(devices_file, points_file)

        # 創建指標
        self.create_metrics()

        # 設備連接和監控指標
        self.device_connection_status = Gauge(
            'device_connection_status', '設備連接狀態 (1=連接, 0=斷開)', ['device', 'ip'])
        self.device_read_total = Counter(
            'device_read_total', '設備讀取總次數', ['device', 'ip'])
        self.device_read_errors = Counter(
            'device_read_errors', '設備讀取錯誤次數', ['device', 'ip'])
        self.device_read_duration = Gauge(
            'device_read_duration', '設備讀取耗時(秒)', ['device', 'ip'])

    def load_config(self, devices_file, points_file):
        """載入設備和點位配置"""
        try:
            with open(devices_file, 'r', encoding='utf-8') as f:
                self.devices = json.load(f)['devices']
                logger.info(f"已載入 {len(self.devices)} 台設備配置")

            with open(points_file, 'r', encoding='utf-8') as f:
                self.point_groups = json.load(f)['metric_groups']
                total_points = sum(len(group['metrics'])
                                   for group in self.point_groups)
                logger.info(
                    f"已載入 {len(self.point_groups)} 組點位，共 {total_points} 個監控點")

            # 初始化設備連接狀態
            for device in self.devices:
                device['current_ip'] = device['primary_ip']  # 初始使用主要 IP
                device['last_fail_time'] = 0  # 上次連接失敗時間
                device['connection_state'] = 'disconnected'  # 初始狀態為未連接

        except Exception as e:
            logger.error(f"載入配置文件時發生錯誤: {e}")
            raise

    def create_metrics(self):
        """為所有監控點創建 Prometheus 指標"""
        for group in self.point_groups:
            for metric in group['metrics']:
                metric_id = metric['id']
                metric_name = metric['name']

                # 創建指標，添加設備標籤
                self.metrics[metric_id] = Gauge(
                    f"{metric_id}",
                    f"{metric_name} ({metric.get('unit', '')})",
                    ['device']
                )
                logger.debug(f"創建指標: {metric_id} - {metric_name}")

    def connect_device(self, device):
        """嘗試連接到設備，如主要 IP 失敗則嘗試備用 IP"""
        now = time.time()
        retry_interval = device.get('retry_interval', 60)  # 默認重試間隔為60秒

        # 如果處於重試冷卻期，繼續使用上次失敗的 IP
        if now - device['last_fail_time'] < retry_interval and device['connection_state'] == 'failed':
            return None

        # 確定要使用的 IP
        ip_to_use = device['current_ip']

        try:
            client = ModbusTcpClient(
                host=ip_to_use,
                port=device['port'],
                timeout=device.get('timeout', 3)
            )

            if client.connect():
                logger.info(f"已連接到設備 {device['name']} ({ip_to_use})")
                device['connection_state'] = 'connected'
                self.device_connection_status.labels(
                    device=device['id'], ip=ip_to_use).set(1)
                return client
            else:
                # 連接失敗，嘗試切換 IP
                self._handle_connection_failure(device, ip_to_use)
                return None

        except Exception as e:
            logger.error(f"連接設備 {device['name']} ({ip_to_use}) 時發生錯誤: {e}")
            self._handle_connection_failure(device, ip_to_use)
            return None

    def _handle_connection_failure(self, device, failed_ip):
        """處理連接失敗情況，切換 IP 並更新狀態"""
        logger.warning(f"連接設備 {device['name']} ({failed_ip}) 失敗")
        device['last_fail_time'] = time.time()
        device['connection_state'] = 'failed'
        self.device_connection_status.labels(
            device=device['id'], ip=failed_ip).set(0)

        # 切換到另一個 IP
        if failed_ip == device['primary_ip']:
            device['current_ip'] = device['backup_ip']
            logger.info(f"切換到備用 IP: {device['backup_ip']}")
        else:
            device['current_ip'] = device['primary_ip']
            logger.info(f"切換到主要 IP: {device['primary_ip']}")

    def read_modbus(self, client, device_id, start_address, count):
        """讀取 Modbus 資料"""
        try:
            # 將 40001 基址轉換為 0
            relative_address = start_address - 40001
            logger.debug(
                f"從設備 {device_id} 讀取 {count} 個寄存器，起始位址 {relative_address}")

            result = client.read_holding_registers(
                relative_address, count, slave=device_id)
            if not result.isError():
                return result.registers

            logger.error(f"從設備 {device_id}，地址 {start_address} 讀取錯誤: {result}")
            return None
        except Exception as e:
            logger.error(f"從設備 {device_id}，地址 {start_address} 讀取時發生異常: {e}")
            return None

    def process_data(self, device, group, registers):
        """處理讀取到的數據，更新 metrics"""
        if not registers:
            return

        for metric in group['metrics']:
            try:
                offset = metric['register_offset']
                data_type = metric.get('data_type', 'INT16')
                scale_factor = metric.get('scale_factor', 1.0)

                if data_type == 'INT16':
                    # 處理 INT16 數據
                    if offset < len(registers):
                        value = registers[offset] / scale_factor
                        self.metrics[metric['id']].labels(
                            device=device['id']).set(value)
                        logger.debug(f"更新指標 {metric['id']} = {value}")

                elif data_type == 'FLOAT32' and offset + 1 < len(registers):
                    # 處理 FLOAT32 數據（佔用兩個寄存器）
                    hi = registers[offset]
                    lo = registers[offset + 1]
                    raw_data = struct.pack('>HH', hi, lo)
                    value = struct.unpack('>f', raw_data)[0]
                    self.metrics[metric['id']].labels(
                        device=device['id']).set(value)
                    logger.debug(f"更新指標 {metric['id']} = {value}")

            except Exception as e:
                logger.error(f"處理指標 {metric['id']} 時發生錯誤: {e}")

    def collect_device_data(self, device):
        """收集單個設備的所有數據"""
        start_time = time.time()
        client = self.connect_device(device)

        if client:
            try:
                current_ip = device['current_ip']
                self.device_read_total.labels(
                    device=device['id'], ip=current_ip).inc()

                # 收集每組數據
                for group in self.point_groups:
                    registers = self.read_modbus(
                        client,
                        group['device_id'],
                        group['start_address'],
                        group['count']
                    )

                    if registers:
                        self.process_data(device, group, registers)
                    else:
                        self.device_read_errors.labels(
                            device=device['id'], ip=current_ip).inc()

            except Exception as e:
                logger.error(f"從設備 {device['name']} 收集數據時發生錯誤: {e}")
                self.device_read_errors.labels(
                    device=device['id'], ip=device['current_ip']).inc()
            finally:
                client.close()

        # 記錄讀取時間
        duration = time.time() - start_time
        self.device_read_duration.labels(
            device=device['id'], ip=device['current_ip']).set(duration)
        logger.debug(f"設備 {device['name']} 資料收集完成，耗時 {duration:.3f} 秒")

    def collect_all_data(self):
        """從所有設備收集數據"""
        # 使用線程池並行收集
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(self.devices), 10)) as executor:
            executor.map(self.collect_device_data, self.devices)

    def run(self, interval=5):
        """啟動收集程序"""
        while True:
            try:
                logger.info("開始收集數據...")
                self.collect_all_data()
                logger.info(f"數據收集完成，等待 {interval} 秒後再次收集")
            except Exception as e:
                logger.error(f"收集過程中發生錯誤: {e}")

            time.sleep(interval)


if __name__ == '__main__':
    # 確保配置文件存在
    config_path = Path("devices.json")
    points_path = Path("plc_points.json")

    if not config_path.exists() or not points_path.exists():
        logger.error(f"配置文件不存在: devices.json 或 plc_points.json")
        exit(1)

    # 啟動 Prometheus 服務
    start_http_server(8000)
    logger.info("Prometheus 指標服務已在 8000 埠啟動")

    # 啟動收集器
    collector = ModbusCollector()
    collector.run(interval=5)  # 每5秒收集一次
