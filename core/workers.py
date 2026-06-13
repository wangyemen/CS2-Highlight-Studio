"""
QThread background workers
"""
from PyQt6.QtCore import QThread, pyqtSignal


class DemoParseWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, filepath, steam_id=""):
        super().__init__()
        self._filepath = filepath
        self._steam_id = steam_id

    def run(self):
        try:
            self.progress.emit("解析 Demo...")
            from core.demo_parser import DemoParserEngine
            engine = DemoParserEngine()
            result = engine.parse_demo(
                self._filepath, steam_id=self._steam_id)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class HighlightDetectWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, parsed_match, settings=None):
        super().__init__()
        self.parsed_match = parsed_match
        self.settings = settings

    def run(self):
        try:
            from core.highlight_detector import (
                HighlightDetector)

            self.progress.emit(
                "正在检测高光时刻...")

            detector = HighlightDetector(
                min_kills=self.settings.get(
                    "min_consecutive_kills", 1
                ) if self.settings else 1,
                multi_kill_window=self.settings.get(
                    "multi_kill_window_seconds", 8.0
                ) if self.settings else 8.0,
                score_threshold=self.settings.get(
                    "min_highlight_score", 3
                ) if self.settings else 3,
                pre_buffer_seconds=self.settings.get(
                    "before_buffer_seconds", 3
                ) if self.settings else 3,
                post_buffer_seconds=self.settings.get(
                    "after_buffer_seconds", 5
                ) if self.settings else 5,
                include_single_kills=True,
            )

            highlights = detector.detect(
                self.parsed_match)
            self.progress.emit(
                "发现 {} 个片段".format(
                    len(highlights)))
            self.finished.emit(highlights)

        except Exception as e:
            self.error.emit(
                "高光检测失败: {}".format(str(e)))


class VideoProcessWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(
        self, source_video, highlights, output_dir,
        match_name="highlight", quality="high",
        settings=None,
    ):
        super().__init__()
        self.source_video = source_video
        self.highlights = highlights
        self.output_dir = output_dir
        self.match_name = match_name
        self.quality = quality
        self.settings = settings

    def run(self):
        try:
            from core.video_processor import (
                VideoProcessor)

            processor = VideoProcessor(
                settings=self.settings)

            result = processor.process_highlights(
                source_video=self.source_video,
                highlights=self.highlights,
                output_dir=self.output_dir,
                match_name=self.match_name,
                quality=self.quality,
                progress_callback=(
                    lambda cur, tot, msg:
                    self.progress.emit(
                        cur, tot, msg)),
            )

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(
                "视频处理失败: {}".format(str(e)))
