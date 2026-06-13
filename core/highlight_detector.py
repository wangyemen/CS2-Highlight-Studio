"""
Highlight detection engine
"""
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
import numpy as np


@dataclass
class Highlight:
    """Single highlight clip"""
    highlight_id: int
    highlight_type: str
    player: str
    start_tick: int
    end_tick: int
    start_seconds: float
    end_seconds: float
    score: float
    kill_count: int
    headshot_count: int = 0
    has_noscope: bool = False
    has_wallbang: bool = False
    has_through_smoke: bool = False
    round_num: int = 0
    description: str = ""
    kill_ticks: list = field(default_factory=list)

    @property
    def duration_seconds(self):
        return self.end_seconds - self.start_seconds

    @property
    def display_type(self):
        type_names = {
            "ace": "王牌 ACE",
            "4k": "四杀 4K",
            "3k": "三杀 3K",
            "2k": "双杀 2K",
            "clutch": "残局",
            "highlight": "精彩",
            "kill": "普通击杀",
        }
        return type_names.get(
            self.highlight_type, self.highlight_type)


class HighlightDetector:

    def __init__(
        self,
        min_kills: int = 1,
        multi_kill_window: float = 8.0,
        score_threshold: float = 3.0,
        pre_buffer_seconds: float = 3.0,
        post_buffer_seconds: float = 5.0,
        include_single_kills: bool = True,
    ):
        self.min_kills = min_kills
        self.multi_kill_window = multi_kill_window
        self.score_threshold = score_threshold
        self.pre_buffer = pre_buffer_seconds
        self.post_buffer = post_buffer_seconds
        self.include_single_kills = include_single_kills

    def detect(self, parsed_match) -> list[Highlight]:
        if (parsed_match.kills_df is None
                or parsed_match.kills_df.empty):
            return []

        kills_df = parsed_match.kills_df
        tick_rate = parsed_match.info.tick_rate

        highlights = []
        highlight_id = 0

        # Track covered kills
        covered = set()

        # 1. Multi-kill clusters per attacker
        attacker_col = self._find_col(
            kills_df.columns,
            ("attacker_name", "attacker",
             "killer_name", "killer"))
        if not attacker_col:
            return []

        for attacker in kills_df[attacker_col].unique():
            attacker_kills = kills_df[
                kills_df[attacker_col] == attacker
            ].sort_values("tick")

            if len(attacker_kills) < 2:
                continue

            clusters = self._find_kill_clusters(
                attacker_kills, tick_rate)

            for cluster in clusters:
                if len(cluster) < self.min_kills:
                    continue

                highlight_id += 1
                hl = self._create_highlight(
                    highlight_id, cluster,
                    attacker, tick_rate)
                highlights.append(hl)
                for k in cluster:
                    covered.add(
                        (attacker, k.get("tick", 0)))

        # 2. Clutch detection
        clutch_highlights = self._detect_clutches(
            kills_df, tick_rate)
        for hl in clutch_highlights:
            highlight_id += 1
            hl.highlight_id = highlight_id
            highlights.append(hl)
            for t in hl.kill_ticks:
                covered.add(
                    (hl.player, t))

        # 3. Single kills → type "kill"
        if self.include_single_kills:
            for _, row in kills_df.iterrows():
                attacker = self._safe_str(
                    row.get(attacker_col))
                tick = row.get("tick", 0)
                if not attacker:
                    continue
                if (attacker, tick) in covered:
                    continue
                highlight_id += 1
                hl = self._create_kill_highlight(
                    highlight_id, row,
                    attacker, tick_rate)
                highlights.append(hl)

        # 4. Merge overlapping
        highlights = self._merge_overlapping(
            highlights)

        # 5. Filter: single kills always pass,
        #    others need score >= threshold
        highlights = [
            h for h in highlights
            if (h.highlight_type == "kill"
                or h.score >= self.score_threshold)]

        # 6. Sort by score desc
        highlights.sort(
            key=lambda h: h.score, reverse=True)

        return highlights

    # ── Helpers ──

    @staticmethod
    def _find_col(columns, candidates):
        for name in candidates:
            if name in columns:
                return name
        return None

    @staticmethod
    def _safe_str(val):
        if val is None:
            return ""
        s = str(val).strip()
        if not s or s in ("nan", "None", "<NULL>"):
            return ""
        return s

    def _find_kill_clusters(
        self, kills_df, tick_rate
    ):
        if kills_df.empty:
            return []

        window_ticks = int(
            self.multi_kill_window * tick_rate)
        clusters = []
        current = []

        for _, row in kills_df.iterrows():
            kd = row.to_dict()
            if not current:
                current.append(kd)
                continue
            last_tick = current[-1]["tick"]
            gap = kd["tick"] - last_tick
            if gap <= window_ticks:
                current.append(kd)
            else:
                if len(current) >= 2:
                    clusters.append(current)
                current = [kd]

        if len(current) >= 2:
            clusters.append(current)

        return clusters

    def _create_highlight(
        self, hid, cluster, player, tick_rate
    ):
        kill_count = len(cluster)
        start_tick = cluster[0]["tick"]
        end_tick = cluster[-1]["tick"]

        if kill_count >= 5:
            hl_type = "ace"
        elif kill_count == 4:
            hl_type = "4k"
        elif kill_count == 3:
            hl_type = "3k"
        else:
            hl_type = "2k"

        hs = sum(
            1 for k in cluster
            if k.get("headshot", False))
        noscope = any(
            k.get("noscope", False) for k in cluster)
        wallbang = any(
            k.get("penetrated", False)
            for k in cluster)
        smoke = any(
            k.get("thrusmoke", False)
            for k in cluster)

        score = self._calculate_score(
            kill_count, hs, noscope,
            wallbang, smoke, cluster, tick_rate)

        padded_start = start_tick - int(
            self.pre_buffer * tick_rate)
        padded_end = end_tick + int(
            self.post_buffer * tick_rate)

        desc = self._generate_description(
            hl_type, kill_count, hs,
            noscope, wallbang, smoke)

        return Highlight(
            highlight_id=hid,
            highlight_type=hl_type,
            player=player,
            start_tick=max(0, padded_start),
            end_tick=padded_end,
            start_seconds=max(
                0, padded_start / tick_rate),
            end_seconds=padded_end / tick_rate,
            score=score,
            kill_count=kill_count,
            headshot_count=hs,
            has_noscope=noscope,
            has_wallbang=wallbang,
            has_through_smoke=smoke,
            description=desc,
            kill_ticks=[k["tick"] for k in cluster],
        )

    def _create_kill_highlight(
        self, hid, row, player, tick_rate
    ):
        """Create a single-kill highlight."""
        tick = row.get("tick", 0)
        hs = bool(row.get("headshot", False))
        noscope = bool(row.get("noscope", False))
        wallbang = bool(
            row.get("penetrated", False))
        smoke = bool(
            row.get("thrusmoke", False))

        # Base score for single kill
        score = 15.0
        if hs:
            score += 5
        if noscope:
            score += 20
        if wallbang:
            score += 15
        if smoke:
            score += 10

        padded_start = tick - int(
            self.pre_buffer * tick_rate)
        padded_end = tick + int(
            self.post_buffer * tick_rate)

        parts = ["普通击杀"]
        tags = []
        if hs:
            tags.append("爆头")
        if noscope:
            tags.append("盲狙")
        if wallbang:
            tags.append("穿墙")
        if smoke:
            tags.append("烟雾")
        if tags:
            parts.append(" | ".join(tags))

        return Highlight(
            highlight_id=hid,
            highlight_type="kill",
            player=player,
            start_tick=max(0, padded_start),
            end_tick=padded_end,
            start_seconds=max(
                0, padded_start / tick_rate),
            end_seconds=padded_end / tick_rate,
            score=score,
            kill_count=1,
            headshot_count=1 if hs else 0,
            has_noscope=noscope,
            has_wallbang=wallbang,
            has_through_smoke=smoke,
            description=" - ".join(parts),
            kill_ticks=[tick],
        )

    def _calculate_score(
        self, kill_count, hs_count,
        noscope, wallbang, smoke,
        cluster, tick_rate
    ):
        base = {
            2: 30, 3: 60, 4: 120, 5: 250}
        score = base.get(
            kill_count, kill_count * 35)

        if kill_count > 0:
            ratio = hs_count / kill_count
            score += ratio * kill_count * 15

        if len(cluster) > 1:
            span = (
                (cluster[-1]["tick"]
                 - cluster[0]["tick"])
                / tick_rate)
            if span > 0:
                kps = kill_count / span
                score += min(kps * 20, 50)

        if noscope:
            score += 40
        if wallbang:
            score += 35
        if smoke:
            score += 30

        return round(score, 1)

    def _generate_description(
        self, hl_type, kill_count, hs_count,
        noscope, wallbang, smoke
    ):
        names = {
            "ace": "ACE 王牌",
            "4k": "四杀",
            "3k": "三杀",
            "2k": "双杀",
        }
        parts = [names.get(
            hl_type, "{}杀".format(kill_count))]

        tags = []
        if hs_count == kill_count and kill_count > 1:
            tags.append("全爆头")
        elif hs_count > 0:
            tags.append("{}爆头".format(hs_count))
        if noscope:
            tags.append("盲狙")
        if wallbang:
            tags.append("穿墙")
        if smoke:
            tags.append("烟雾")

        if tags:
            parts.append(" | ".join(tags))

        return " - ".join(parts)

    def _detect_clutches(self, kills_df, tick_rate):
        return []

    def _merge_overlapping(self, highlights):
        if not highlights:
            return []

        highlights.sort(key=lambda h: h.start_tick)
        merged = [highlights[0]]

        for hl in highlights[1:]:
            last = merged[-1]
            if hl.start_tick <= last.end_tick:
                if hl.score > last.score:
                    merged[-1] = hl
            else:
                merged.append(hl)

        return merged
