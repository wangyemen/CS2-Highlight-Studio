"""
Settings persistence
"""
import json
import os
from pathlib import Path


class AppSettings:

    _DEFAULTS = {
        "steam_id": "",
        "tick_rate": 64,
        "auto_record_on_match_start": True,
        "auto_process_new_demo": True,
        "hotkeys_enabled": False,
        "hotkey_record": "F9",
        "hotkey_replay": "F10",
        "obs_host": "127.0.0.1",
        "obs_port": 4455,
        "obs_password": "",
        "obs_auto_connect": True,
        "gsi_port": 3010,
        "gsi_auto_start": True,
        "cs2_install_path": "",
        "demo_folder": "",
        "min_highlight_score": 3,
        "min_consecutive_kills": 2,
        "min_clutch_kills": 2,
        "before_buffer_seconds": 3,
        "after_buffer_seconds": 5,
        "output_dir": "",
        "output_quality": "high",
        "output_format": "mp4",
        "use_copy_mode": False,
        "ffmpeg_path": "",
    }

    def __init__(self):
        self._data_dir = Path(__file__).parent.parent / "config_data"
        self._data_dir.mkdir(exist_ok=True)
        self._file = self._data_dir / "settings.json"
        self._data = dict(self._DEFAULTS)
        self.load()

    def load(self):
        if self._file.exists():
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self._data.update(loaded)
            except Exception:
                pass

    def save(self):
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    def has(self, key):
        return key in self._data
