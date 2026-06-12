"""
Hardware Detection + OBS Auto-Configuration
"""
import os
import re
import json
import platform
import subprocess
from dataclasses import dataclass, field


@dataclass
class GPUInfo:
    name: str = ""
    brand: str = ""       # nvidia / amd / intel / unknown
    vram_mb: int = 0
    tier: str = ""        # high / medium / low / none


@dataclass
class HardwareProfile:
    gpu: GPUInfo = field(default_factory=GPUInfo)
    cpu_name: str = ""
    cpu_threads: int = 0
    ram_gb: float = 0.0
    display_w: int = 1920
    display_h: int = 1080


class HardwareDetector:

    _NV_HIGH = ("4090", "4080", "4070 TI", "3090", "3080", "3070 TI")
    _NV_MED  = ("4060", "3060", "3050", "2080", "2070", "2060",
                "1660", "TITAN")
    _NV_LOW  = ("1650", "1080", "1070", "1060", "1050", "GT ", "GTX 9")
    _AMD_HIGH = ("7900", "7800", "6900", "6800", "VEGA 64")
    _AMD_MED  = ("7600", "7500", "6700", "6600", "5700", "5600")
    _AMD_LOW  = ("580", "570", "550", "RX 5", "RX 4")

    # ═══════════════════════════════════════
    #  Detect
    # ═══════════════════════════════════════

    @staticmethod
    def detect_all(app=None):
        p = HardwareProfile()
        HardwareDetector._gpu(p)
        HardwareDetector._cpu(p)
        HardwareDetector._ram(p)
        HardwareDetector._display(p, app)
        return p

    @staticmethod
    def _gpu(p):
        try:
            r = subprocess.run(
                ["nvidia-smi",
                 "--query-gpu=name,memory.total",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
                encoding="utf-8", errors="replace")
            if r.returncode == 0 and r.stdout.strip():
                line = r.stdout.strip().split("\n")[0]
                parts = [x.strip() for x in line.split(",")]
                p.gpu.name = parts[0]
                p.gpu.brand = "nvidia"
                p.gpu.vram_mb = int(parts[1]) if len(parts) > 1 else 0
                p.gpu.tier = HardwareDetector._tier_nv(p.gpu.name)
                return
        except Exception:
            pass

        try:
            r = subprocess.run(
                ["wmic", "path", "win32_videocontroller",
                 "get", "name,adapterram"],
                capture_output=True, text=True, timeout=5,
                encoding="utf-8", errors="replace")
            if r.returncode == 0:
                lines = [l.strip() for l in r.stdout.split("\n")
                         if l.strip()
                         and "AdapterRAM" not in l
                         and "Name" not in l]
                for line in lines:
                    up = line.upper()
                    if "NVIDIA" in up:
                        p.gpu.brand = "nvidia"
                    elif "AMD" in up or "RADEON" in up:
                        p.gpu.brand = "amd"
                    elif "INTEL" in up:
                        p.gpu.brand = "intel"
                    p.gpu.name = re.split(r"\s{2,}", line)[0].strip()
                    nums = re.findall(r"\d+", line)
                    for n in nums:
                        v = int(n)
                        if v > 1_000_000:
                            p.gpu.vram_mb = v // (1024 * 1024)
                            break
                    break
        except Exception:
            pass

        if p.gpu.brand == "nvidia":
            p.gpu.tier = HardwareDetector._tier_nv(p.gpu.name)
        elif p.gpu.brand == "amd":
            p.gpu.tier = HardwareDetector._tier_amd(p.gpu.name)
        elif p.gpu.brand == "intel":
            p.gpu.tier = "medium" if "ARC" in p.gpu.name.upper() else "low"
        else:
            p.gpu.tier = "none"

    @staticmethod
    def _tier_nv(name):
        up = name.upper()
        for m in HardwareDetector._NV_HIGH:
            if m in up:
                return "high"
        for m in HardwareDetector._NV_MED:
            if m in up:
                return "medium"
        for m in HardwareDetector._NV_LOW:
            if m in up:
                return "low"
        return "medium"

    @staticmethod
    def _tier_amd(name):
        up = name.upper()
        for m in HardwareDetector._AMD_HIGH:
            if m in up:
                return "high"
        for m in HardwareDetector._AMD_MED:
            if m in up:
                return "medium"
        return "low"

    @staticmethod
    def _cpu(p):
        p.cpu_name = platform.processor() or "Unknown"
        p.cpu_threads = os.cpu_count() or 4

    @staticmethod
    def _ram(p):
        try:
            import psutil
            p.ram_gb = round(psutil.virtual_memory().total / (1024**3), 1)
            return
        except ImportError:
            pass
        try:
            r = subprocess.run(
                ["wmic", "os", "get", "TotalVisibleMemorySize"],
                capture_output=True, text=True, timeout=5,
                encoding="utf-8", errors="replace")
            for line in r.stdout.split("\n"):
                line = line.strip()
                if line.isdigit():
                    p.ram_gb = round(int(line) / (1024**2), 1)
                    return
        except Exception:
            pass
        p.ram_gb = 16.0

    @staticmethod
    def _display(p, app=None):
        try:
            if app is None:
                from PyQt6.QtWidgets import QApplication
                app = QApplication.instance()
            if app:
                screens = app.screens()
                if screens:
                    s = screens[0]
                    p.display_w = s.size().width()
                    p.display_h = s.size().height()
                    return
        except Exception:
            pass
        p.display_w, p.display_h = 1920, 1080

    # ═══════════════════════════════════════
    #  Recommend
    # ═══════════════════════════════════════

    @staticmethod
    def recommend(profile):
        g = profile.gpu
        w, h = profile.display_w, profile.display_h

        out_w, out_h = w, h
        if g.tier in ("low", "none") and h > 720:
            out_w, out_h = 1280, 720
        elif g.tier == "medium" and h > 1440:
            out_w, out_h = 2560, 1440

        rec = {
            "base_w": w, "base_h": h,
            "out_w": out_w, "out_h": out_h,
            "fps": 60,
            "format": "mkv",
            "scale_type": "Lanczos",
        }

        if g.brand == "nvidia" and g.tier in ("high", "medium"):
            rec["encoder"] = "jim_nvenc"
            rec["enc_type"] = "nvenc"
            if g.tier == "high":
                rec["preset"] = "p5"
                rec["profile"] = "high"
                rec["cq_level"] = 18
                rec["max_bitrate"] = 50000
                rec["bf"] = 2
            else:
                rec["preset"] = "p3"
                rec["profile"] = "high"
                rec["cq_level"] = 20
                rec["max_bitrate"] = 35000
                rec["bf"] = 2

        elif g.brand == "amd" and g.tier in ("high", "medium"):
            rec["encoder"] = "h264_texture_amf"
            rec["enc_type"] = "amd"
            if g.tier == "high":
                rec["preset"] = "Quality"
                rec["cq_level"] = 20
                rec["max_bitrate"] = 50000
            else:
                rec["preset"] = "Balanced"
                rec["cq_level"] = 22
                rec["max_bitrate"] = 35000

        elif g.brand == "intel" and g.tier in ("medium",):
            rec["encoder"] = "obs_qsv11"
            rec["enc_type"] = "qsv"
            rec["preset"] = "Best"
            rec["cq_level"] = 18
            rec["max_bitrate"] = 30000

        else:
            rec["encoder"] = "obs_x264"
            rec["enc_type"] = "x264"
            rec["profile"] = "high"
            if profile.cpu_threads >= 12:
                rec["preset"] = "fast"
                rec["bitrate"] = 20000
            elif profile.cpu_threads >= 8:
                rec["preset"] = "veryfast"
                rec["bitrate"] = 15000
            else:
                rec["preset"] = "ultrafast"
                rec["bitrate"] = 10000

        rec["audio_bitrate"] = 192
        return rec

    # ═══════════════════════════════════════
    #  Apply to OBS - uses set_profile_parameter
    # ═══════════════════════════════════════

    @staticmethod
    def apply_to_obs(client, rec):
        if not client:
            return False, "OBS 未连接"

        errors = []
        ok_count = 0

        def _set(cat, name, val):
            nonlocal ok_count
            try:
                client.set_profile_parameter(
                    category=cat, name=name, value=str(val))
                ok_count += 1
            except Exception as e:
                errors.append("{}.{}: {}".format(cat, name, e))

        # ── Video ──
        _set("Video", "BaseCX", rec["base_w"])
        _set("Video", "BaseCY", rec["base_h"])
        _set("Video", "OutputCX", rec["out_w"])
        _set("Video", "OutputCY", rec["out_h"])
        _set("Video", "FPSType", "0")
        _set("Video", "FPSNum", str(rec["fps"]))
        _set("Video", "ScaleType", rec.get("scale_type", "Lanczos"))

        # ── Recording output ──
        _set("Output", "RecFilePath", os.path.expanduser(
            "~/Videos/CS2 Highlights"))
        _set("Output", "RecFormatName", rec["format"])

        # Encoder
        encoder = rec["encoder"]
        _set("Output", "RecEncoder", encoder)
        _set("Output", "RecAudioEncoder", "ffmpeg_aac")
        _set("Output", "RecABitrate", str(rec["audio_bitrate"]))

        # Encoder-specific settings as JSON string
        enc_json = HardwareDetector._encoder_json(rec)
        if enc_json:
            _set("Output", "RecEncoderSettings", json.dumps(enc_json))

        if errors:
            msg = "成功 {}/{} 项\n失败:\n{}".format(
                ok_count, ok_count + len(errors),
                "\n".join(errors[:5]))
            return False, msg

        return True, "配置已应用! ({}/{} 项)\n建议重启 OBS 使设置完全生效。".format(
            ok_count, ok_count)

    @staticmethod
    def _encoder_json(rec):
        enc = rec["enc_type"]

        if enc == "nvenc":
            return {
                "preset": rec.get("preset", "p3"),
                "rate_control": "CQP",
                "cq-level": rec.get("cq_level", 20),
                "keyint": 120,
                "profile": rec.get("profile", "high"),
                "look-ahead": False,
                "psycho-visual-tuning": True,
                "gpu": 0,
                "max-bitrate": rec.get("max_bitrate", 50000),
                "bf": rec.get("bf", 2),
            }
        elif enc == "x264":
            return {
                "rate_control": "CBR",
                "bitrate": rec.get("bitrate", 15000),
                "preset": rec.get("preset", "veryfast"),
                "profile": rec.get("profile", "high"),
                "tune": "zerolatency",
            }
        elif enc == "amd":
            return {
                "RateControl": "CQP",
                "Bitrate": rec.get("max_bitrate", 35000),
                "QPI": rec.get("cq_level", 20),
                "QPP": rec.get("cq_level", 22),
                "QPB": rec.get("cq_level", 24),
                "KeyframePeriod": 120,
                "Preset": rec.get("preset", "Quality"),
            }
        elif enc == "qsv":
            return {
                "RateControlICQ": 1,
                "ICQQuality": rec.get("cq_level", 18),
                "TargetKbps": rec.get("max_bitrate", 30000),
                "KeyframePeriod": 120,
                "Preset": rec.get("preset", "Best"),
            }
        return None

    # ═══════════════════════════════════════
    #  Auto-detect Steam / CS2 / OBS paths
    # ═══════════════════════════════════════

    @staticmethod
    def detect_steam_id():
        """Auto-detect Steam ID from registry."""
        import winreg
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Valve\Steam")
            path, _ = winreg.QueryValueEx(key, "SteamPath")
            winreg.CloseKey(key)
            vdf = os.path.join(path, "config", "loginusers.vdf")
            if os.path.isfile(vdf):
                import codecs
                with codecs.open(vdf, "r", "utf-8", errors="ignore") as f:
                    content = f.read()
                # Find most recent user
                ids = re.findall(r'"(76561\d+)"', content)
                if ids:
                    return ids[0]
        except Exception:
            pass
        return ""

    @staticmethod
    def detect_steam_path():
        """Auto-detect Steam installation path."""
        import winreg
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Valve\Steam")
            path, _ = winreg.QueryValueEx(key, "SteamPath")
            winreg.CloseKey(key)
            return path.replace("/", "\\")
        except Exception:
            pass
        for p in (
            r"C:\Program Files (x86)\Steam",
            r"D:\Steam",
            r"C:\Program Files\Steam",
            r"D:\Program Files (x86)\Steam",
        ):
            if os.path.isdir(p):
                return p
        return ""

    @staticmethod
    def detect_cs2_path(steam_path=""):
        """Auto-detect CS2 installation path."""
        if not steam_path:
            steam_path = HardwareDetector.detect_steam_path()

        if steam_path:
            libraryfolders = os.path.join(
                steam_path, "steamapps", "libraryfolders.vdf")
            if os.path.isfile(libraryfolders):
                import codecs
                with codecs.open(libraryfolders, "r", "utf-8",
                                 errors="ignore") as f:
                    content = f.read()
                paths = re.findall(r'"path"\s+"([^"]+)"', content)
                for p in paths:
                    app = os.path.join(
                        p.replace("\\\\", "\\"),
                        "steamapps", "appmanifest_730.acf")
                    if os.path.isfile(app):
                        cs2 = os.path.join(
                            p.replace("\\\\", "\\"),
                            "steamapps", "common",
                            "Counter-Strike Global Offensive")
                        if os.path.isdir(cs2):
                            return cs2

            # Fallback: same drive as Steam
            cs2 = os.path.join(
                steam_path,
                "steamapps", "common",
                "Counter-Strike Global Offensive")
            if os.path.isdir(cs2):
                return cs2

        for p in (
            r"C:\Program Files (x86)\Steam\steamapps\common"
            r"\Counter-Strike Global Offensive",
            r"D:\SteamLibrary\steamapps\common"
            r"\Counter-Strike Global Offensive",
            r"E:\SteamLibrary\steamapps\common"
            r"\Counter-Strike Global Offensive",
            r"D:\Program Files (x86)\Steam\steamapps\common"
            r"\Counter-Strike Global Offensive",
        ):
            if os.path.isdir(p):
                return p

        return ""

    @staticmethod
    def detect_obs_port():
        """Try to detect OBS WebSocket port from config."""
        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, "AppData", "Roaming",
                         "obs-studio", "plugin_config",
                         "obs-websocket", "obs-websocket.json"),
            os.path.join(home, "AppData", "Roaming",
                         "obs-studio", "global.ini"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8",
                              errors="ignore") as f:
                        content = f.read()
                    ports = re.findall(
                        r'"ServerPort"\s*:\s*(\d+)', content)
                    if not ports:
                        ports = re.findall(
                            r'"port"\s*:\s*(\d+)', content)
                    if ports:
                        return int(ports[0])
                except Exception:
                    pass
        return 4455

    @staticmethod
    def detect_demo_folder():
        """Auto-detect common CS2 demo folders."""
        cs2 = HardwareDetector.detect_cs2_path()
        if cs2:
            demo_dir = os.path.join(cs2, "game", "csgo", "replays")
            if os.path.isdir(demo_dir):
                return demo_dir

        home = os.path.expanduser("~")
        for sub in (
            "Documents/CS2/replays",
            "Documents/CSGO/replays",
            "Videos/CS2",
        ):
            p = os.path.join(home, sub)
            if os.path.isdir(p):
                return p
        return ""

    @staticmethod
    def detect_ffmpeg():
        """Find FFmpeg on system."""
        import shutil
        p = shutil.which("ffmpeg")
        if p:
            return p
        if os.name == "nt":
            for path in (
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            ):
                if os.path.isfile(path):
                    return path
        return ""
