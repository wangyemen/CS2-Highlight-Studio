"""
高光时刻检测与评分引擎
分析击杀时间线，识别连杀、残局、精彩操作
"""
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
import numpy as np


@dataclass
class Highlight:
    """单个高光片段"""
    highlight_id: int
    highlight_type: str          # "2k", "3k", "4k", "ace", "clutch", "highlight"
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
        }
        return type_names.get(self.highlight_type, self.highlight_type)


class HighlightDetector:
    """高光时刻检测器"""

    def __init__(
        self,
        min_kills: int = 2,
        multi_kill_window: float = 8.0,
        score_threshold: float = 50.0,
        pre_buffer_seconds: float = 5.0,
        post_buffer_seconds: float = 3.0,
    ):
        self.min_kills = min_kills
        self.multi_kill_window = multi_kill_window
        self.score_threshold = score_threshold
        self.pre_buffer = pre_buffer_seconds
        self.post_buffer = post_buffer_seconds

    def detect(self, parsed_match) -> list[Highlight]:
        """
        从解析后的比赛数据中检测所有高光时刻

        Args:
            parsed_match: ParsedMatch 对象

        Returns:
            按评分降序排列的高光列表
        """
        if parsed_match.kills_df is None or parsed_match.kills_df.empty:
            return []

        kills_df = parsed_match.kills_df
        tick_rate = parsed_match.info.tick_rate

        highlights = []
        highlight_id = 0

        # 1. 按攻击者分组检测连杀
        for attacker in kills_df["attacker_name"].unique():
            attacker_kills = kills_df[
                kills_df["attacker_name"] == attacker
            ].sort_values("tick")

            if len(attacker_kills) < self.min_kills:
                continue

            clusters = self._find_kill_clusters(attacker_kills, tick_rate)

            for cluster in clusters:
                if len(cluster) < self.min_kills:
                    continue

                highlight_id += 1
                hl = self._create_highlight(
                    highlight_id, cluster, attacker, tick_rate
                )
                highlights.append(hl)

        # 2. 检测残局 (Clutch)
        clutch_highlights = self._detect_clutches(kills_df, tick_rate)
        for hl in clutch_highlights:
            highlight_id += 1
            hl.highlight_id = highlight_id
            highlights.append(hl)

        # 3. 去重和合并重叠片段
        highlights = self._merge_overlapping(highlights)

        # 4. 过滤低分和按评分排序
        highlights = [h for h in highlights if h.score >= self.score_threshold]
        highlights.sort(key=lambda h: h.score, reverse=True)

        return highlights

    def _find_kill_clusters(
        self, kills_df: pd.DataFrame, tick_rate: int
    ) -> list[list[dict]]:
        """
        将击杀按时间接近度聚类
        在 multi_kill_window 秒内的连续击杀归为同一集群
        """
        if kills_df.empty:
            return []

        window_ticks = int(self.multi_kill_window * tick_rate)
        clusters = []
        current_cluster = []

        for _, row in kills_df.iterrows():
            kill_data = row.to_dict()

            if not current_cluster:
                current_cluster.append(kill_data)
                continue

            last_tick = current_cluster[-1]["tick"]
            gap = kill_data["tick"] - last_tick

            if gap <= window_ticks:
                current_cluster.append(kill_data)
            else:
                if len(current_cluster) >= self.min_kills:
                    clusters.append(current_cluster)
                current_cluster = [kill_data]

        if len(current_cluster) >= self.min_kills:
            clusters.append(current_cluster)

        return clusters

    def _create_highlight(
        self,
        hid: int,
        cluster: list[dict],
        player: str,
        tick_rate: int,
    ) -> Highlight:
        kill_count = len(cluster)
        start_tick = cluster[0]["tick"]
        end_tick = cluster[-1]["tick"]

        # 类型判定
        if kill_count >= 5:
            hl_type = "ace"
        elif kill_count == 4:
            hl_type = "4k"
        elif kill_count == 3:
            hl_type = "3k"
        else:
            hl_type = "2k"

        # 统计
        headshot_count = sum(1 for k in cluster if k.get("headshot", False))
        has_noscope = any(k.get("noscope", False) for k in cluster)
        has_wallbang = any(k.get("penetrated", False) for k in cluster)
        has_smoke = any(k.get("thrusmoke", False) for k in cluster)

        # 评分
        score = self._calculate_score(
            kill_count, headshot_count,
            has_noscope, has_wallbang, has_smoke,
            cluster, tick_rate
        )

        # 时间范围 (含缓冲)
        padded_start = start_tick - int(self.pre_buffer * tick_rate)
        padded_end = end_tick + int(self.post_buffer * tick_rate)

        description = self._generate_description(
            hl_type, kill_count, headshot_count,
            has_noscope, has_wallbang, has_smoke
        )

        return Highlight(
            highlight_id=hid,
            highlight_type=hl_type,
            player=player,
            start_tick=max(0, padded_start),
            end_tick=padded_end,
            start_seconds=max(0, padded_start / tick_rate),
            end_seconds=padded_end / tick_rate,
            score=score,
            kill_count=kill_count,
            headshot_count=headshot_count,
            has_noscope=has_noscope,
            has_wallbang=has_wallbang,
            has_through_smoke=has_smoke,
            description=description,
            kill_ticks=[k["tick"] for k in cluster],
        )

    def _calculate_score(
        self,
        kill_count: int,
        headshot_count: int,
        has_noscope: bool,
        has_wallbang: bool,
        has_smoke: bool,
        cluster: list[dict],
        tick_rate: int,
    ) -> float:
        """计算高光片段的综合评分"""
        # 基础分: 连杀数指数增长
        base_scores = {2: 30, 3: 60, 4: 120, 5: 250}
        score = base_scores.get(kill_count, kill_count * 35)

        # 爆头奖励
        if kill_count > 0:
            hs_ratio = headshot_count / kill_count
            score += hs_ratio * kill_count * 15

        # 速度奖励: 击杀间隔越短越精彩
        if len(cluster) > 1:
            time_span = (cluster[-1]["tick"] - cluster[0]["tick"]) / tick_rate
            if time_span > 0:
                kills_per_second = kill_count / time_span
                speed_bonus = min(kills_per_second * 20, 50)
                score += speed_bonus

        # 特殊操作奖励
        if has_noscope:
            score += 40
        if has_wallbang:
            score += 35
        if has_smoke:
            score += 30

        return round(score, 1)

    def _generate_description(
        self, hl_type, kill_count, hs_count, noscope, wallbang, smoke
    ) -> str:
        parts = []
        type_names = {
            "ace": "ACE 王牌", "4k": "四杀", "3k": "三杀", "2k": "双杀"
        }
        parts.append(type_names.get(hl_type, f"{kill_count}杀"))

        tags = []
        if hs_count == kill_count and kill_count > 1:
            tags.append("全爆头")
        elif hs_count > 0:
            tags.append(f"{hs_count}爆头")
        if noscope:
            tags.append("盲狙")
        if wallbang:
            tags.append("穿墙")
        if smoke:
            tags.append("烟雾")

        if tags:
            parts.append(" | ".join(tags))

        return " - ".join(parts)

    def _detect_clutches(
        self, kills_df: pd.DataFrame, tick_rate: int
    ) -> list[Highlight]:
        """检测残局时刻 (简化版: 连续击杀且存活玩家少)"""
        # 简化实现: 找到单次回合内的连续击杀
        # 完整实现需要追踪存活玩家数
        highlights = []

        if "round" in kills_df.columns:
            for round_num in kills_df["round"].unique():
                round_kills = kills_df[kills_df["round"] == round_num]
                attackers = round_kills["attacker_name"].value_counts()
                for attacker, count in attackers.items():
                    if count >= 3:
                        pass  # 已在连杀检测中覆盖

        return highlights

    def _merge_overlapping(self, highlights: list[Highlight]) -> list[Highlight]:
        """合并时间重叠的高光片段，保留更高分的"""
        if not highlights:
            return []

        highlights.sort(key=lambda h: h.start_tick)
        merged = [highlights[0]]

        for hl in highlights[1:]:
            last = merged[-1]
            if hl.start_tick <= last.end_tick:
                # 重叠: 保留分数更高的
                if hl.score > last.score:
                    merged[-1] = hl
            else:
                merged.append(hl)

        return merged
