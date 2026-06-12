"""CS2 游戏目录 + SteamID 自动检测"""
import os
import re
import sys


def auto_detect_steam():
    if sys.platform == "win32":
        steam = _detect_steam_registry()
        if steam:
            return steam

    common = [
        r"C:\Program Files (x86)\Steam",
        r"C:\Program Files\Steam",
        r"D:\Steam", r"D:\SteamLibrary",
        r"E:\Steam", r"E:\SteamLibrary",
        r"F:\Steam", r"F:\SteamLibrary",
    ]
    for p in common:
        if os.path.isfile(os.path.join(p, "steam.exe")):
            return p

    for letter in "CDEFGHIJ":
        for name in ("Steam", "SteamLibrary"):
            path = "{}:\\{}".format(letter, name)
            if os.path.isfile(os.path.join(path, "steam.exe")):
                return path

    home = os.path.expanduser("~")
    for p in (os.path.join(home, ".steam", "steam"),
              os.path.join(home, ".local", "share", "Steam")):
        if os.path.isdir(p):
            return p
    return ""


def _detect_steam_registry():
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)
        path = path.replace("/", "\\")
        if os.path.isdir(path):
            return path
    except Exception:
        pass
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\WOW6432Node\Valve\Steam")
        path, _ = winreg.QueryValueEx(key, "InstallPath")
        winreg.CloseKey(key)
        if os.path.isdir(path):
            return path
    except Exception:
        pass
    return ""


def find_steam_libraries(steam_path):
    libraries = []
    if not steam_path or not os.path.isdir(steam_path):
        return libraries
    libraries.append(steam_path)
    vdf = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    if not os.path.isfile(vdf):
        return libraries
    try:
        with open(vdf, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        for m in re.finditer(r'"path"\s+"([^"]+)"', content):
            lib = m.group(1).replace("\\\\", "\\")
            if os.path.isdir(lib) and lib not in libraries:
                libraries.append(lib)
    except Exception:
        pass
    return libraries


def auto_detect_cs2():
    steam_path = auto_detect_steam()
    if not steam_path:
        return ("", "")
    libraries = find_steam_libraries(steam_path)
    for lib in libraries:
        common_dir = os.path.join(lib, "steamapps", "common")
        if not os.path.isdir(common_dir):
            continue
        for name in ("Counter-Strike Global Offensive", "Counter-Strike 2"):
            candidate = os.path.join(common_dir, name)
            if os.path.isdir(candidate):
                return (candidate, steam_path)
    return ("", steam_path)


def auto_detect_steam_id(steam_path=""):
    """从本地文件自动检测 SteamID"""
    if not steam_path:
        steam_path = auto_detect_steam()
    if not steam_path:
        return ""

    # 方法 1: loginusers.vdf
    users_file = os.path.join(steam_path, "config", "loginusers.vdf")
    if os.path.isfile(users_file):
        try:
            with open(users_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            steam_ids = re.findall(r'"(\d{17})"\s*\{', content)
            if steam_ids:
                return steam_ids[0]
        except Exception:
            pass

    # 方法 2: steam.inf
    cs2_paths = [
        os.path.join(steam_path, "steamapps", "common",
                     "Counter-Strike Global Offensive", "game", "csgo", "steam.inf"),
        os.path.join(steam_path, "steamapps", "common",
                     "Counter-Strike Global Offensive", "steam.inf"),
    ]
    for inf_path in cs2_paths:
        if os.path.isfile(inf_path):
            try:
                with open(inf_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                m = re.search(r"ClientSteamID=(\d+)", content)
                if m:
                    return m.group(1)
            except Exception:
                pass

    return ""


def get_csgo_cfg_path(cs2_path):
    if not cs2_path:
        return ""
    for sub in (os.path.join("game", "csgo", "cfg"),
                os.path.join("csgo", "cfg")):
        p = os.path.join(cs2_path, sub)
        if os.path.isdir(p):
            return p
    return os.path.join(cs2_path, "game", "csgo", "cfg")


def get_demo_path(cs2_path):
    if not cs2_path:
        return ""
    for sub in (os.path.join("game", "csgo", "replays"),
                os.path.join("csgo", "replays")):
        p = os.path.join(cs2_path, sub)
        if os.path.isdir(p):
            return p
    default = os.path.join(cs2_path, "game", "csgo", "replays")
    os.makedirs(default, exist_ok=True)
    return default
