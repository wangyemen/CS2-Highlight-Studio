"""
智能视频文件关联
从 OBS 录制目录、设置文件、时间戳自动匹配视频文件
"""
import os
import json
import re
from pathlib import Path
from typing import Optional


class VideoAssociator:

    VIDEO_EXTS = {".mp4", ".mkv", ".flv", ".ts", ".avi"}

    def __init__(self, settings=None):
        self.settings = settings

    def find_recording_from_obs(self, obs_controller=None) -> Optional[str]:
        """通过 OBS WebSocket 获取当前录制文件路径"""
        if obs_controller and obs_controller.state.connected:
            path = obs_controller.get_recording_path()
            if path and os.path.isfile(path):
                return path
        return None

    def find_recording_from_obs_settings(self) -> Optional[str]:
        """从 OBS 设置文件中读取录制输出路径"""
        if not self.settings:
            return None

        # 尝试从设置中获取
        obs_path = self.settings.get("obs_record_output_path", "")
        if obs_path and os.path.isdir(obs_path):
            return self._find_latest_video(obs_path)

        # 尝试 OBS 默认设置文件位置
        home = Path.home()
        obs_config_paths = [
            home / "AppData" / "Roaming" / "obs-studio" / "basic" / "profiles" / "Untitled",
            home / "AppData" / "Roaming" / "obs-studio" / "basic" / "profiles",
        ]

        for cfg_dir in obs_config_paths:
            if not cfg_dir.exists():
                continue
            for cfg_file in cfg_dir.rglob("basic.ini"):
                path = self._read_obs_output_path(cfg_file)
                if path and os.path.isdir(path):
                    return self._find_latest_video(path)

        return None

    def _read_obs_output_path(self, ini_path: Path) -> Optional[str]:
        """从 basic.ini 读取录制路径"""
        try:
            with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # 简单 INI 解析
            in_advanced = False
            for line in content.split("\n"):
                line = line.strip()
                if line.lower() == "[advanced]":
                    in_advanced = True
                elif line.startswith("["):
                    in_advanced = False
                elif in_advanced and "=" in line:
                    key, _, val = line.partition("=")
                    key = key.strip().lower()
                    val = val.strip().strip('"')
                    if "recording" in key and "path" in key.lower():
                        return val
                    if key == "recfilepath":
                        return val
        except Exception:
            pass
        return None

    def find_by_time_match(self, demo_path: str,
                           search_dirs: list = None,
                           tolerance_seconds: int = 7200) -> Optional[str]:
        """
        根据 Demo 文件的时间戳匹配最接近的视频文件

        Args:
            demo_path: Demo 文件路径
            search_dirs: 搜索目录列表
            tolerance_seconds: 最大允许时间差（秒），默认 2 小时
        """
        if not os.path.exists(demo_path):
            return None

        demo_mtime = os.path.getmtime(demo_path)

        if not search_dirs:
            search_dirs = self._get_default_search_dirs()

        best_match = None
        best_diff = float("inf")

        for search_dir in search_dirs:
            p = Path(search_dir)
            if not p.exists():
                continue
            try:
                for vf in p.rglob("*"):
                    if vf.suffix.lower() not in self.VIDEO_EXTS:
                        continue
                    try:
                        v_mtime = vf.stat().st_mtime
                    except OSError:
                        continue
                    diff = abs(v_mtime - demo_mtime)
                    if diff < best_diff:
                        best_diff = diff
                        best_match = str(vf)
            except PermissionError:
                continue

        if best_match and best_diff <= tolerance_seconds:
            return best_match
        return None

    def associate(self, demo_path: str,
                  obs_controller=None) -> Optional[str]:
        """
        综合策略: 按优先级尝试关联视频

        1. OBS 当前录制文件
        2. OBS 设置中的录制路径最新文件
        3. 时间戳匹配
        4. 返回 None
        """
        # 策略 1: OBS 正在录制
        result = self.find_recording_from_obs(obs_controller)
        if result:
            return result

        # 策略 2: OBS 设置文件
        result = self.find_recording_from_obs_settings()
        if result:
            return result

        # 策略 3: 时间戳匹配
        result = self.find_by_time_match(demo_path)
        if result:
            return result

        return None

    def _find_latest_video(self, folder: str) -> Optional[str]:
        """在文件夹中找到最新的视频文件"""
        p = Path(folder)
        if not p.exists():
            return None

        videos = []
        try:
            for f in p.iterdir():
                if f.suffix.lower() in self.VIDEO_EXTS and f.is_file():
                    videos.append(f)
        except PermissionError:
            return None

        if not videos:
            return None

        videos.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return str(videos[0])

    def _get_default_search_dirs(self) -> list:
        """获取默认的视频搜索目录"""
        dirs = []
        home = Path.home()

        # 设置中的输出目录
        if self.settings:
            output = self.settings.get("output_dir", "")
            if output:
                dirs.append(output)

        # Windows 常见目录
        for sub in ("Videos", "Videos/OBS", "Documents/OBS"):
            candidate = home / sub
            if candidate.exists():
                dirs.append(str(candidate))

        for letter in "CDEFGH":
            for sub in ("Videos", "OBS", "OBS\u5f55\u5236", "\u5f55\u50cf"):
                candidate = Path("{}:/{}".format(letter, sub))
                if candidate.exists():
                    dirs.append(str(candidate))

        return dirs
