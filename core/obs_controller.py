"""
OBS WebSocket 控制器
连接 OBS Studio，监控录制状态，发送时间戳标记
"""
import json
import asyncio
import threading
import time
from typing import Optional, Callable
from dataclasses import dataclass

try:
    import obsws_python as obs
    HAS_OBSWS = True
except ImportError:
    HAS_OBSWS = False


@dataclass
class OBSState:
    connected: bool = False
    recording: bool = False
    streaming: bool = False
    recording_path: str = ""
    current_scene: str = ""
    record_time: float = 0.0


class OBSController:
    """OBS Studio 控制器"""

    def __init__(self, settings=None):
        self.settings = settings
        self.state = OBSState()
        self._client = None
        self._status_callback: Optional[Callable] = None
        self._lock = threading.Lock()

    def set_status_callback(self, callback: Callable):
        self._status_callback = callback

    def _notify(self):
        if self._status_callback:
            try:
                self._status_callback(self.state)
            except Exception:
                pass

    def connect(self, host: str = None, port: int = None, password: str = None):
        """连接到 OBS WebSocket"""
        if not HAS_OBSWS:
            self.state.connected = False
            self._notify()
            return False

        host = host or (self.settings.get("obs_host") if self.settings else "127.0.0.1")
        port = port or (self.settings.get("obs_port") if self.settings else 4455)
        password = password or (self.settings.get("obs_password") if self.settings else "")

        try:
            self._client = obs.ReqClient(
                host=host, port=port, password=password
            )
            # 测试连接
            self._client.get_version()
            self.state.connected = True
            self._update_state()
            self._start_polling()
            self._notify()
            return True
        except Exception as e:
            print(f"OBS 连接失败: {e}")
            self.state.connected = False
            self._notify()
            return False

    def disconnect(self):
        """断开 OBS 连接"""
        self._stop_polling()
        if self._client:
            try:
                self._client.disconnect()
            except Exception:
                pass
        self._client = None
        self.state.connected = False
        self.state.recording = False
        self.state.streaming = False
        self._notify()

    def _start_polling(self):
        self._polling = True
        self._poll_thread = threading.Thread(
            target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def _stop_polling(self):
        self._polling = False

    def _poll_loop(self):
        self._polling = True
        while self._polling:
            try:
                self._update_state()
                self._notify()
            except Exception:
                pass
            time.sleep(2)


    def _update_state(self):
        """更新 OBS 状态"""
        if not self._client:
            return
        try:
            rec = self._client.get_record_status()
            self.state.recording = rec.output_active
            self.state.recording_path = getattr(rec, "output_path", "")

            stream = self._client.get_stream_status()
            self.state.streaming = stream.output_active

            scene = self._client.get_current_program_scene()
            self.state.current_scene = scene.scene_name
        except Exception as e:
            print(f"OBS 状态更新失败: {e}")

    def is_recording(self) -> bool:
        """检查是否正在录制"""
        self._update_state()
        return self.state.recording

    def get_recording_path(self) -> str:
        """获取当前录制文件路径"""
        self._update_state()
        return self.state.recording_path

    def start_recording(self):
        """开始录制 (safe)"""
        if not self._client:
            return False
        try:
            rec = self._client.get_record_status()
            if rec.output_active:
                self.state.recording = True
                return True
        except Exception:
            pass
        try:
            self._client.start_record()
            self._update_state()
            self._notify()
            return True
        except Exception as e:
            print("OBS start_record failed: {}".format(e))
            return False

    def stop_recording(self):
        """停止录制 (safe)"""
        if not self._client:
            return False
        try:
            rec = self._client.get_record_status()
            if not rec.output_active:
                self.state.recording = False
                return True
        except Exception:
            pass
        try:
            self._client.stop_record()
            self._update_state()
            self._notify()
            return True
        except Exception as e:
            print("OBS stop_record failed: {}".format(e))
            return False

    def toggle_recording(self):
        if self.state.recording:
            return self.stop_recording()
        return self.start_recording()

    def save_replay_buffer(self):
        if not self._client:
            return False
        try:
            self._client.save_replay_buffer()
            return True
        except Exception as e:
            print("OBS save_replay failed: {}".format(e))
            return False

    def mark_highlight(self, timestamp: float):
        """
        向 OBS 发送高光时间戳标记
        用于 OBS 插件标记关键时间点
        """
        if self._client:
            try:
                self._client.call("TriggerHotkeyByName",
                    {"hotkeyName": f"cs2_highlight_{timestamp}"})
            except Exception:
                pass

    def get_status_text(self) -> str:
        """获取状态摘要文本"""
        if not self.state.connected:
            return "未连接"
        parts = []
        if self.state.recording:
            parts.append("录制中")
        if self.state.streaming:
            parts.append("推流中")
        if not parts:
            parts.append("已连接(空闲)")
        return " | ".join(parts)


class OBSStatusPoller:
    """定时轮询 OBS 状态的后台线程"""

    def __init__(self, controller: OBSController, interval: float = 2.0):
        self.controller = controller
        self.interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def _poll_loop(self):
        while self._running:
            try:
                self.controller._update_state()
                self.controller._notify()
            except Exception:
                pass
            import time
            time.sleep(self.interval)
