"""
Video Processor - FFmpeg with hardware encoding
"""
import os
import subprocess
import shutil

_CREATION_FLAGS = 0
if hasattr(subprocess, "CREATE_NO_WINDOW"):
    _CREATION_FLAGS = subprocess.CREATE_NO_WINDOW

import tempfile
from pathlib import Path


class VideoProcessor:

    def __init__(self, ffmpeg_path=None,
                 settings=None):
        if ffmpeg_path:
            self.ffmpeg_path = ffmpeg_path
        elif settings:
            self.ffmpeg_path = settings.get(
                "ffmpeg_path", "ffmpeg")
        else:
            self.ffmpeg_path = "ffmpeg"
        if not self.ffmpeg_path:
            self.ffmpeg_path = "ffmpeg"
        self._validate_ffmpeg()

        self._encoder = self._detect_encoder()
        self._max_threads = max(
            2, (os.cpu_count() or 4) - 2)

        print("[Video] Encoder: {} ({})".format(
            self._encoder["name"],
            self._encoder["type"]))
        print("[Video] Threads: {}".format(
            self._max_threads))

    # ═══════════════════════════════════════
    #  Encoder detection
    # ═══════════════════════════════════════

    def _detect_encoder(self):
        try:
            r = subprocess.run(
                [self.ffmpeg_path, "-encoders"],
                capture_output=True, timeout=5,
                encoding="utf-8", errors="replace",
                creationflags=_CREATION_FLAGS)
            encoders = r.stdout
        except Exception:
            encoders = ""

        if "h264_nvenc" in encoders:
            return {
                "type": "nvenc",
                "name": "NVIDIA NVENC",
                "vcodec": "h264_nvenc"}
        if "h264_amf" in encoders:
            return {
                "type": "amf",
                "name": "AMD AMF",
                "vcodec": "h264_amf"}
        if "h264_qsv" in encoders:
            return {
                "type": "qsv",
                "name": "Intel QSV",
                "vcodec": "h264_qsv"}
        return {
            "type": "cpu",
            "name": "CPU (libx264)",
            "vcodec": "libx264"}

    def get_encoder_name(self):
        return self._encoder["name"]

    # ═══════════════════════════════════════
    #  Encode args builder
    # ═══════════════════════════════════════

    def _build_encode_args(self, quality):
        """Build FFmpeg encoding arguments
        based on encoder + quality mode."""
        enc = self._encoder["type"]

        if quality == "copy":
            return ["-c:v", "copy", "-c:a", "copy"]

        threads = str(self._max_threads)

        if enc == "nvenc":
            cfg = {
                "quality": {
                    "qp": "18", "preset": "p7",
                    "br": "256k"},
                "balanced": {
                    "qp": "22", "preset": "p4",
                    "br": "192k"},
                "speed": {
                    "qp": "26", "preset": "p1",
                    "br": "128k"},
            }
            p = cfg.get(quality, cfg["balanced"])
            return [
                "-c:v", "h264_nvenc",
                "-rc", "constqp",
                "-qp", p["qp"],
                "-preset", p["preset"],
                "-c:a", "aac", "-b:a", p["br"],
                "-threads", threads]

        if enc == "amf":
            cfg = {
                "quality": {"q": "quality"},
                "balanced": {"q": "balanced"},
                "speed": {"q": "speed"},
            }
            p = cfg.get(quality, cfg["balanced"])
            return [
                "-c:v", "h264_amf",
                "-quality", p["q"],
                "-c:a", "aac", "-b:a", "192k",
                "-threads", threads]

        if enc == "qsv":
            cfg = {
                "quality": {
                    "q": "1", "p": "veryslow"},
                "balanced": {
                    "q": "3", "p": "medium"},
                "speed": {
                    "q": "5", "p": "fast"},
            }
            p = cfg.get(quality, cfg["balanced"])
            return [
                "-c:v", "h264_qsv",
                "-global_quality", p["q"],
                "-preset", p["p"],
                "-c:a", "aac", "-b:a", "192k",
                "-threads", threads]

        # CPU fallback
        cfg = {
            "quality": {
                "crf": "18", "preset": "slow",
                "br": "256k"},
            "balanced": {
                "crf": "20", "preset": "medium",
                "br": "192k"},
            "speed": {
                "crf": "23", "preset": "ultrafast",
                "br": "128k"},
        }
        p = cfg.get(quality, cfg["balanced"])
        return [
            "-c:v", "libx264",
            "-crf", p["crf"],
            "-preset", p["preset"],
            "-c:a", "aac", "-b:a", p["br"],
            "-threads", threads]

    # ═══════════════════════════════════════
    #  FFmpeg validate
    # ═══════════════════════════════════════

    def _validate_ffmpeg(self):
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True, timeout=5,
                encoding="utf-8", errors="replace",
                creationflags=_CREATION_FLAGS)
            if result.returncode != 0:
                raise RuntimeError("FFmpeg failed")
        except FileNotFoundError:
            raise FileNotFoundError(
                "FFmpeg not found: {}\n"
                "Install FFmpeg or set path "
                "in Settings.".format(
                    self.ffmpeg_path))

    # ═══════════════════════════════════════
    #  Clip
    # ═══════════════════════════════════════

    def clip_highlight(
            self, source_video, highlight,
            output_path, quality="balanced"):
        os.makedirs(
            os.path.dirname(output_path) or ".",
            exist_ok=True)

        start = max(0, highlight.start_seconds)
        duration = highlight.end_seconds - start

        encode_args = self._build_encode_args(
            quality)

        cmd = [
            self.ffmpeg_path,
            "-ss", str(start),
            "-i", source_video,
            "-t", str(duration),
        ] + encode_args + [
            "-movflags", "+faststart",
            "-y", output_path,
        ]

        self._run_ffmpeg(cmd)
        return output_path

    # ═══════════════════════════════════════
    #  Merge
    # ═══════════════════════════════════════

    def merge_clips(self, clip_paths, output_path,
                    quality="balanced"):
        if not clip_paths:
            raise ValueError("No clips to merge")
        if len(clip_paths) == 1:
            out_dir = os.path.dirname(output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            shutil.copy2(
                clip_paths[0], output_path)
            return output_path

        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        list_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt",
            delete=False, encoding="utf-8")
        try:
            for clip in clip_paths:
                safe = (clip.replace("\\", "/")
                        .replace("'", "'\\''"))
                list_file.write(
                    "file '{}'\n".format(safe))
            list_file.close()

            encode_args = self._build_encode_args(
                quality)
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", list_file.name,
            ] + encode_args + [
                "-movflags", "+faststart",
                "-y", output_path,
            ]

            self._run_ffmpeg(cmd)
        finally:
            os.unlink(list_file.name)

        return output_path

    # ═══════════════════════════════════════
    #  Process all highlights
    # ═══════════════════════════════════════

    def process_highlights(
            self, source_video, highlights,
            output_dir, match_name="highlight",
            quality="balanced",
            progress_callback=None):
        os.makedirs(output_dir, exist_ok=True)
        clips_dir = os.path.join(
            output_dir, "clips")
        os.makedirs(clips_dir, exist_ok=True)

        clip_paths = []
        total = len(highlights)

        for i, hl in enumerate(highlights):
            if progress_callback:
                progress_callback(
                    i, total,
                    "Clip {}/{}: {} ({})".format(
                        i + 1, total,
                        hl.display_type,
                        hl.player))

            clip_name = (
                "{}_{:02d}_{}_{}.mp4".format(
                    match_name,
                    hl.highlight_id,
                    hl.highlight_type,
                    hl.player))
            clip_path = os.path.join(
                clips_dir, clip_name)

            try:
                self.clip_highlight(
                    source_video, hl,
                    clip_path,
                    quality=quality)
                clip_paths.append(clip_path)
            except Exception as e:
                print("Clip failed {}: {}".format(
                    clip_name, e))

        if progress_callback:
            progress_callback(
                total, total, "Merging...")

        merged_name = (
            "{}_highlight.mp4".format(
                match_name))
        merged_path = os.path.join(
            output_dir, merged_name)

        if clip_paths:
            self.merge_clips(
                clip_paths, merged_path,
                quality=quality)
        else:
            merged_path = None

        if progress_callback:
            progress_callback(
                total, total, "Done")

        return {
            "clips": clip_paths,
            "merged": merged_path}

    # ═══════════════════════════════════════
    #  Utils
    # ═══════════════════════════════════════

    @staticmethod
    def find_obs_recording(obs_path=None):
        search = []
        if obs_path:
            search.append(Path(obs_path))
        home = Path.home()
        for sub in ("Videos", "Videos/OBS"):
            c = home / sub
            if c.exists():
                search.append(c)
        for letter in "CDEFGH":
            for sub in ("Videos", "OBS"):
                c = Path(
                    "{}:/{}".format(letter, sub))
                if c.exists():
                    search.append(c)
        for base in search:
            for ext in ("*.mp4", "*.mkv",
                        "*.flv", "*.ts"):
                files = sorted(
                    base.glob(ext),
                    key=lambda f:
                        f.stat().st_mtime,
                    reverse=True)
                if files:
                    return str(files[0])
        return None

    def get_video_duration(self, video_path):
        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-f", "null", "-"]
        r = subprocess.run(
            cmd, capture_output=True,
            encoding="utf-8", errors="replace",
            creationflags=_CREATION_FLAGS)
        for line in r.stderr.split("\n"):
            if "Duration" in line:
                parts = (line.split("Duration:")[1]
                         .split(",")[0].strip())
                h, m, s = parts.split(":")
                return (float(h) * 3600
                        + float(m) * 60
                        + float(s))
        return 0.0

    def _run_ffmpeg(self, cmd):
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=600,
            encoding="utf-8",
            errors="replace",
            creationflags=_CREATION_FLAGS)
        if result.returncode != 0:
            error_msg = (
                result.stderr[-500:]
                if result.stderr
                else "Unknown")
            raise RuntimeError(
                "FFmpeg failed:\n{}".format(
                    error_msg))
