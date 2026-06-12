"""
全局快捷键管理器
"""
import threading
from typing import Callable, Optional


class HotkeyManager:
    """
    跨平台全局快捷键管理
    依赖 keyboard 库 (pip install keyboard)
    Windows 需要管理员权限才能注册全局热键
    """

    def __init__(self, settings=None):
        self.settings = settings
        self._callbacks = {}
        self._active = False
        self._keyboard_available = False
        self._installed = self._check_keyboard()

    def _check_keyboard(self) -> bool:
        try:
            import keyboard
            self._keyboard_available = True
            return True
        except ImportError:
            return False

    @property
    def is_available(self):
        return self._keyboard_available

    def register(self, hotkey_str: str, callback: Callable, name: str = ""):
        """
        注册一个全局快捷键

        Args:
            hotkey_str: 快捷键字符串, 如 "ctrl+shift+r"
            callback: 触发时调用的函数
            name: 快捷键名称标识
        """
        if not self._keyboard_available:
            return False

        if not hotkey_str or not hotkey_str.strip():
            return False

        try:
            import keyboard
            keyboard.add_hotkey(
                hotkey_str,
                callback,
                suppress=False,
                trigger_on_release=False,
            )
            self._callbacks[name or hotkey_str] = hotkey_str
            return True
        except Exception as e:
            print("快捷键注册失败 '{}': {}".format(hotkey_str, e))
            return False

    def unregister(self, name: str):
        if not self._keyboard_available:
            return
        try:
            import keyboard
            hotkey_str = self._callbacks.pop(name, None)
            if hotkey_str:
                keyboard.remove_hotkey(hotkey_str)
        except Exception:
            pass

    def unregister_all(self):
        if not self._keyboard_available:
            return
        try:
            import keyboard
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        self._callbacks.clear()

    def load_from_settings(self, record_callback=None,
                           replay_callback=None):
        """从设置加载并注册所有快捷键"""
        if not self.settings:
            return
        if not self.settings.get("hotkeys_enabled", False):
            return

        self.unregister_all()

        hotkey_record = self.settings.get("hotkey_toggle_record", "")
        hotkey_replay = self.settings.get("hotkey_save_replay", "")

        if hotkey_record and record_callback:
            self.register(hotkey_record, record_callback, "toggle_record")

        if hotkey_replay and replay_callback:
            self.register(hotkey_replay, replay_callback, "save_replay")

    def format_hotkey(self, hotkey_str: str) -> str:
        """将快捷键字符串转为显示格式"""
        if not hotkey_str:
            return "无"
        parts = hotkey_str.split("+")
        display_map = {
            "ctrl": "Ctrl", "control": "Ctrl",
            "shift": "Shift",
            "alt": "Alt",
            "win": "Win", "super": "Win",
        }
        return "+".join(display_map.get(p.lower(), p.upper()) for p in parts)

    @staticmethod
    def is_available_check() -> bool:
        try:
            import keyboard
            return True
        except ImportError:
            return False
