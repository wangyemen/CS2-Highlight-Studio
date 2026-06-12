"""
QThread 后台任务工作者
将耗时操作放在后台线程，避免 UI 卡顿
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
    """高光检测后台任务"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, parsed_match, settings=None):
        super().__init__()
        self.parsed_match = parsed_match
        self.settings = settings

    def run(self):
        try:
            from core.highlight_detector import HighlightDetector

            self.progress.emit("正在检测高光时刻...")

            detector = HighlightDetector(
                min_kills=self.settings.get(
                    "min_kills_for_highlight", 2
                ) if self.settings else 2,
                multi_kill_window=self.settings.get(
                    "multi_kill_window_seconds", 8.0
                ) if self.settings else 8.0,
                score_threshold=self.settings.get(
                    "highlight_score_threshold", 50
                ) if self.settings else 50,
                pre_buffer_seconds=self.settings.get(
                    "clip_pre_seconds", 5.0
                ) if self.settings else 5.0,
                post_buffer_seconds=self.settings.get(
                    "clip_post_seconds", 3.0
                ) if self.settings else 3.0,
            )

            highlights = detector.detect(self.parsed_match)
            self.progress.emit(
                "发现 {} 个高光片段".format(len(highlights))
            )
            self.finished.emit(highlights)

        except Exception as e:
            self.error.emit("高光检测失败: {}".format(str(e)))


class VideoProcessWorker(QThread):
    """视频处理后台任务"""
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(
        self, source_video, highlights, output_dir,
        match_name="highlight", quality="high", settings=None,
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
            from core.video_processor import VideoProcessor

            processor = VideoProcessor(settings=self.settings)

            result = processor.process_highlights(
                source_video=self.source_video,
                highlights=self.highlights,
                output_dir=self.output_dir,
                match_name=self.match_name,
                quality=self.quality,
                progress_callback=lambda cur, tot, msg:
                    self.progress.emit(cur, tot, msg),
            )

            self.finished.emit(result)

        except Exception as e:
            self.error.emit("视频处理失败: {}".format(str(e)))
