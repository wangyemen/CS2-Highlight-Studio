"""
Match History - with per-match folders and clip deletion
"""
import json
import os
import shutil
from pathlib import Path
from datetime import datetime


class MatchHistory:

    def __init__(self):
        self._data_dir = Path(__file__).parent.parent / "config_data"
        self._data_dir.mkdir(exist_ok=True)
        self._history_file = self._data_dir / "match_history.json"
        self.matches = []
        self.load()

    def load(self):
        if self._history_file.exists():
            try:
                with open(self._history_file, "r", encoding="utf-8") as f:
                    self.matches = json.load(f).get("matches", [])
            except Exception:
                self.matches = []

    def save(self):
        with open(self._history_file, "w", encoding="utf-8") as f:
            json.dump(
                {"matches": self.matches}, f,
                indent=2, ensure_ascii=False)

    # ═══════════════════════════════════════
    #  Add match record
    # ═══════════════════════════════════════

    def add_match(self, parsed_match, highlights, output_dir="",
                  clips=None):
        info = parsed_match.info

        highlights_info = []
        for hl in highlights:
            highlights_info.append({
                "id": hl.highlight_id,
                "type": hl.highlight_type,
                "player": hl.player,
                "score": hl.score,
                "description": hl.description,
                "start_seconds": round(hl.start_seconds, 2),
                "end_seconds": round(hl.end_seconds, 2),
                "kill_count": hl.kill_count,
                "headshot_count": hl.headshot_count,
            })

        # Auto-create per-match output folder
        match_folder = self._create_match_folder(info, output_dir)

        record = {
            "id": str(int(datetime.now().timestamp() * 1000)),
            "map_name": info.map_name,
            "score_ct": info.score_ct,
            "score_t": info.score_t,
            "team_a_name": info.team_a_name,
            "team_b_name": info.team_b_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_kills": parsed_match.total_kills,
            "tick_rate": info.tick_rate,
            "duration": round(info.duration_seconds, 1),
            "warmup_duration": round(info.warmup_duration, 1),
            "competitive_rounds": info.competitive_rounds,
            "players_a": parsed_match.player_stats_a,
            "players_b": parsed_match.player_stats_b,
            "highlights_count": len(highlights),
            "highlights_info": highlights_info,
            "output_dir": match_folder,
            "clips": clips or [],
        }

        self.matches.insert(0, record)
        if len(self.matches) > 200:
            self.matches = self.matches[:200]
        self.save()
        return record

    # ═══════════════════════════════════════
    #  Create per-match folder
    # ═══════════════════════════════════════

    def _create_match_folder(self, info, base_output_dir):
        """
        Create a dedicated folder for each match.
        Structure: {output_dir}/{date}_{map}/
        Example: F:/csHighlight/clips/20260612_dust2/
        """
        if not base_output_dir:
            return ""

        # Ensure base output dir exists
        base = Path(base_output_dir)
        base.mkdir(parents=True, exist_ok=True)

        # Build match folder name
        map_name = info.map_name.replace("de_", "").replace("cs_", "")
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        folder_name = "{}_{}".format(date_str, map_name)
        match_folder = base / folder_name
        match_folder.mkdir(parents=True, exist_ok=True)

        # Also create a clips subfolder
        clips_folder = match_folder / "clips"
        clips_folder.mkdir(exist_ok=True)

        return str(match_folder)

    # ═══════════════════════════════════════
    #  Update match
    # ═══════════════════════════════════════

    def update_match(self, match_id, output_dir=None, clips=None):
        for m in self.matches:
            if m["id"] == match_id:
                if output_dir is not None:
                    m["output_dir"] = output_dir
                if clips is not None:
                    m["clips"] = clips
                self.save()
                return True
        return False

    # ═══════════════════════════════════════
    #  Delete with clip cleanup
    # ═══════════════════════════════════════

    def delete_match(self, match_id, delete_clips=False):
        """
        Delete a match record.

        Args:
            match_id: record id
            delete_clips: if True, also delete clip files and folder
        Returns:
            tuple: (deleted_clips_count, deleted_files)
        """
        record = None
        for m in self.matches:
            if m["id"] == match_id:
                record = m
                break

        if not record:
            return 0, []

        deleted_files = []
        clips_count = 0

        if delete_clips:
            # Delete individual clip files
            clip_files = record.get("clips", [])
            for clip_path in clip_files:
                if clip_path and os.path.isfile(clip_path):
                    try:
                        os.remove(clip_path)
                        deleted_files.append(clip_path)
                        clips_count += 1
                    except OSError:
                        pass

            # Try to delete the match folder if empty
            output_dir = record.get("output_dir", "")
            if output_dir and os.path.isdir(output_dir):
                clips_sub = os.path.join(output_dir, "clips")
                # Remove clips subfolder
                if os.path.isdir(clips_sub):
                    try:
                        shutil.rmtree(clips_sub)
                    except OSError:
                        pass
                # Try to remove main match folder (only if empty)
                try:
                    os.rmdir(output_dir)
                except OSError:
                    pass  # Not empty, leave it

        # Remove from list
        self.matches = [m for m in self.matches if m["id"] != match_id]
        self.save()

        return clips_count, deleted_files

    # ═══════════════════════════════════════
    #  Query
    # ═══════════════════════════════════════

    def get_match_by_id(self, match_id):
        for m in self.matches:
            if m["id"] == match_id:
                return m
        return None

    def get_recent(self, count=50):
        return self.matches[:count]

    def clear(self, delete_clips=False):
        """Clear all history"""
        if delete_clips:
            for m in self.matches:
                for clip in m.get("clips", []):
                    if clip and os.path.isfile(clip):
                        try:
                            os.remove(clip)
                        except OSError:
                            pass
                output_dir = m.get("output_dir", "")
                if output_dir and os.path.isdir(output_dir):
                    try:
                        shutil.rmtree(output_dir)
                    except OSError:
                        pass
        self.matches = []
        self.save()
