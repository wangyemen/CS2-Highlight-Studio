"""
Video Processor - FFmpeg based
"""
import os
import subprocess

# Hide console window on Windows
_CREATION_FLAGS = 0
if hasattr(subprocess, "CREATE_NO_WINDOW"):
    _CREATION_FLAGS = subprocess.CREATE_NO_WINDOW

import tempfile
from pathlib import Path


class VideoProcessor:

    QUALITY_PRESETS = {
        "low": {"crf": 28, "preset": "ultrafast", "audio_bitrate": "128k"},
        "medium": {"crf": 23, "preset": "fast", "audio_bitrate": "192k"},
        "high": {"crf": 18, "preset": "medium", "audio_bitrate": "256k"},
    }

    def __init__(self, ffmpeg_path=None, settings=None):
        if ffmpeg_path:
            self.ffmpeg_path = ffmpeg_path
        elif settings:
            self.ffmpeg_path = settings.get("ffmpeg_path", "ffmpeg")
        else:
            self.ffmpeg_path = "ffmpeg"
        if not self.ffmpeg_path:
            self.ffmpeg_path = "ffmpeg"
        self._validate_ffmpeg()

    @staticmethod
    def find_ffmpeg():
        import shutil
        path = shutil.which("ffmpeg")
        if path:
            return path
        import sys
        if sys.platform == "win32":
            import os
            for p in (
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                r"D:\ffmpeg\bin\ffmpeg.exe",
            ):
                if os.path.isfile(p):
                    return p
        return "ffmpeg"

    def _validate_ffmpeg(self):
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True, timeout=5,
                encoding="utf-8", errors="replace",
                creationflags=_CREATION_FLAGS,
            )
            if result.returncode != 0:
                raise RuntimeError("FFmpeg failed")
        except FileNotFoundError:
            raise FileNotFoundError(
                "FFmpeg not found: {}\n"
                "Install FFmpeg or set path in Settings.".format(
                    self.ffmpeg_path))

    def clip_highlight(self, source_video, highlight, output_path,
                       quality="high", use_copy=False):
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        start = max(0, highlight.start_seconds)
        duration = highlight.end_seconds - start

        if use_copy:
            cmd = [
                self.ffmpeg_path, "-ss", str(start),
                "-i", source_video, "-t", str(duration),
                "-c", "copy", "-avoid_negative_ts", "make_zero",
                "-y", output_path,
            ]
        else:
            p = self.QUALITY_PRESETS.get(quality, self.QUALITY_PRESETS["high"])
            cmd = [
                self.ffmpeg_path, "-ss", str(start),
                "-i", source_video, "-t", str(duration),
                "-c:v", "libx264", "-crf", str(p["crf"]),
                "-preset", p["preset"],
                "-c:a", "aac", "-b:a", p["audio_bitrate"],
                "-movflags", "+faststart", "-y", output_path,
            ]

        self._run_ffmpeg(cmd)
        return output_path

    def merge_clips(self, clip_paths, output_path, quality="high"):
        if not clip_paths:
            raise ValueError("No clips to merge")
        if len(clip_paths) == 1:
            import shutil
            out_dir = os.path.dirname(output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            shutil.copy2(clip_paths[0], output_path)
            return output_path

        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        list_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8")
        try:
            for clip in clip_paths:
                safe = clip.replace("\\", "/").replace("'", "'\\''")
                list_file.write("file '{}'\n".format(safe))
            list_file.close()

            p = self.QUALITY_PRESETS.get(quality, self.QUALITY_PRESETS["high"])
            cmd = [
                self.ffmpeg_path, "-f", "concat", "-safe", "0",
                "-i", list_file.name,
                "-c:v", "libx264", "-crf", str(p["crf"]),
                "-preset", p["preset"],
                "-c:a", "aac", "-b:a", p["audio_bitrate"],
                "-movflags", "+faststart", "-y", output_path,
            ]
            self._run_ffmpeg(cmd)
        finally:
            os.unlink(list_file.name)

        return output_path

    def process_highlights(self, source_video, highlights, output_dir,
                           match_name="highlight", quality="high",
                           progress_callback=None):
        os.makedirs(output_dir, exist_ok=True)
        clips_dir = os.path.join(output_dir, "clips")
        os.makedirs(clips_dir, exist_ok=True)

        clip_paths = []
        total = len(highlights)

        for i, hl in enumerate(highlights):
            if progress_callback:
                progress_callback(i, total,
                    "Clip {}/{}: {} ({})".format(
                        i + 1, total, hl.display_type, hl.player))

            clip_name = "{}_{:02d}_{}_{}.mp4".format(
                match_name, hl.highlight_id,
                hl.highlight_type, hl.player)
            clip_path = os.path.join(clips_dir, clip_name)

            try:
                self.clip_highlight(
                    source_video, hl, clip_path, quality=quality)
                clip_paths.append(clip_path)
            except Exception as e:
                print("Clip failed {}: {}".format(clip_name, e))

        if progress_callback:
            progress_callback(total, total, "Merging...")

        merged_name = "{}_highlight.mp4".format(match_name)
        merged_path = os.path.join(output_dir, merged_name)

        if clip_paths:
            self.merge_clips(clip_paths, merged_path, quality=quality)
        else:
            merged_path = None

        if progress_callback:
            progress_callback(total, total, "Done")

        return {"clips": clip_paths, "merged": merged_path}

    @staticmethod
    def find_obs_recording(obs_path=None):
        from pathlib import Path
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
                c = Path("{}:/{}".format(letter, sub))
                if c.exists():
                    search.append(c)

        for base in search:
            for ext in ("*.mp4", "*.mkv", "*.flv", "*.ts"):
                files = sorted(
                    base.glob(ext),
                    key=lambda f: f.stat().st_mtime, reverse=True)
                if files:
                    return str(files[0])
        return None

    def get_video_duration(self, video_path):
        cmd = [self.ffmpeg_path, "-i", video_path, "-f", "null", "-"]
        r = subprocess.run(cmd, capture_output=True,
            encoding="utf-8", errors="replace")
        for line in r.stderr.split("\n"):
            if "Duration" in line:
                parts = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = parts.split(":")
                return float(h) * 3600 + float(m) * 60 + float(s)
        return 0.0

    def _run_ffmpeg(self, cmd):
        """
        Run FFmpeg with UTF-8 encoding to avoid GBK errors on Windows.
        """
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=600,
            encoding="utf-8",
            errors="replace",
            creationflags=_CREATION_FLAGS,
        )
        if result.returncode != 0:
            error_msg = result.stderr[-500:] if result.stderr else "Unknown"
            raise RuntimeError(
                "FFmpeg failed:\n{}".format(error_msg))
