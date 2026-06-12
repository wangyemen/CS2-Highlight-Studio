"""
比赛监视器 - 自动发现新 Demo 文件并触发处理
监听 GSI 比赛结束信号，自动定位并处理最新 Demo
"""
import os
import time
import threading
from pathlib import Path
from typing import Optional, Callable


class MatchWatcher:
    """Demo 文件自动发现和监视"""

    def __init__(self, settings=None):
        self.settings = settings
        self._callbacks: list[Callable] = []
        self._watching = False
        self._thread: Optional[threading.Thread] = None
        self._last_demos: set = set()

    def add_callback(self, callback: Callable):
        self._callbacks.append(callback)

    def _notify(self, event: str, data):
        for cb in self._callbacks:
            try:
                cb(event, data)
            except Exception:
                pass

    def scan_all_folders(self) -> list[str]:
        """扫描所有配置的 Demo 文件夹"""
        all_demos = []

        # CS2 默认 demo 路径
        if self.settings:
            cs2_path = self.settings.get("cs2_install_path", "")
            if cs2_path:
                demo_dir = Path(cs2_path) / "replays"
                if demo_dir.exists():
                    all_demos.extend(
                        str(f) for f in demo_dir.glob("*.dem")
                    )

            # 用户自定义路径
            for folder in self.settings.get("demo_scan_folders", []):
                if os.path.exists(folder):
                    for f in Path(folder).rglob("*.dem"):
                        all_demos.append(str(f))

        return sorted(set(all_demos), key=lambda p: os.path.getmtime(p), reverse=True)

    def find_new_demos(self) -> list[str]:
        """找出新出现的 Demo 文件"""
        current = set(self.scan_all_folders())
        new_files = current - self._last_demos
        self._last_demos = current
        return sorted(new_files)

    def get_latest_demo(self) -> Optional[str]:
        """获取最新的 Demo 文件"""
        demos = self.scan_all_folders()
        return demos[0] if demos else None

    def watch_for_new_demos(self, interval: float = 10.0):
        """开始监视新的 Demo 文件"""
        self._watching = True
        self._last_demos = set(self.scan_all_folders())
        self._thread = threading.Thread(
            target=self._watch_loop,
            args=(interval,),
            daemon=True,
        )
        self._thread.start()

    def stop_watching(self):
        self._watching = False
        if self._thread:
            self._thread.join(timeout=3)

    def _watch_loop(self, interval: float):
        while self._watching:
            new_demos = self.find_new_demos()
            for demo in new_demos:
                self._notify("new_demo", demo)
            time.sleep(interval)

    def get_demo_display_name(self, filepath: str) -> str:
        """获取 Demo 的友好显示名称"""
        p = Path(filepath)
        name = p.stem

        # CS2 demo 文件名通常包含时间戳
        # 例: "cs2_demo_20240115_143022_12345678"
        parts = name.split("_")
        if len(parts) >= 3:
            date_part = parts[-2] if len(parts) > 2 else ""
            time_part = parts[-1] if len(parts) > 1 else ""
            return f"{p.parent.name}/{name}"

        return name
