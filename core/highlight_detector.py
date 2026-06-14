"""
Highlight detection engine - round-based
"""
from dataclasses import dataclass, field
import logging
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class Highlight:
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
    max_streak: int = 0

    @property
    def duration_seconds(self):
        return self.end_seconds - self.start_seconds

    @property
    def display_type(self):
        return {
            "ace": "王牌 ACE",
            "4k": "四杀 4K",
            "3k": "三杀 3K",
            "2k": "双杀 2K",
            "clutch": "残局",
            "highlight": "精彩",
            "kill": "普通击杀",
        }.get(self.highlight_type,
              self.highlight_type)


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

    def detect(self, parsed_match):
        if (parsed_match.kills_df is None
                or parsed_match.kills_df.empty):
            return []

        kills_df = parsed_match.kills_df
        tick_rate = parsed_match.info.tick_rate

        # 1. Build round boundaries
        rounds = self._build_rounds(parsed_match)

        # 2. Assign round to each kill
        if rounds:
            kills_df = self._assign_rounds(
                kills_df, rounds)

        # 3. Find attacker column
        attacker_col = self._find_col(
            kills_df.columns,
            ("attacker_name", "attacker",
             "killer_name", "killer"))
        if not attacker_col:
            return []

        tick_col = self._find_col(
            kills_df.columns, ("tick",))
        if not tick_col:
            return []

        highlights = []
        hid = 0

        # 4. Skip warmup (round <= 0)
        round_col = "round" if "round" in kills_df.columns else None
        if round_col:
            kills_df = kills_df[
                kills_df[round_col] > 0]

        # 5. Group by (attacker, round)
        if round_col:
            groups = kills_df.groupby(
                [attacker_col, round_col])
        else:
            groups = kills_df.groupby([attacker_col])

        for keys, group in groups:
            if isinstance(keys, tuple):
                attacker = keys[0]
                rnd = keys[1] if len(keys) > 1 else 0
            else:
                attacker = keys
                rnd = 0

            attacker = str(attacker).strip()
            if not attacker or attacker == "nan":
                continue

            kills = group.sort_values(tick_col)
            n = len(kills)

            if n == 0:
                continue

            if n >= 2:
                hid += 1
                hl = self._create_multi_highlight(
                    hid, kills, attacker, rnd,
                    tick_col, tick_rate)
                highlights.append(hl)
            elif n == 1 and self.include_single_kills:
                hid += 1
                hl = self._create_single_highlight(
                    hid, kills.iloc[0], attacker,
                    rnd, tick_col, tick_rate)
                highlights.append(hl)

        # 6. Filter
        highlights = [
            h for h in highlights
            if (h.highlight_type == "kill"
                or h.score >= self.score_threshold)]

        # 7. Sort and re-number
        highlights.sort(key=lambda h: h.start_tick)
        for i, h in enumerate(highlights):
            h.highlight_id = i + 1

        # 8. Video offset from demo parser
        offset = parsed_match.info.video_offset_tick
        logger.info(
            "Video offset: tick %d", offset)

        for h in highlights:
            raw_s = h.start_tick - offset
            raw_e = h.end_tick - offset
            h.start_seconds = max(
                0, raw_s / tick_rate)
            h.end_seconds = max(
                0, raw_e / tick_rate)

        return highlights

    # ═══════════════════════════════════════
    #  Round boundaries
    # ═══════════════════════════════════════

    def _build_rounds(self, parsed_match):
        rounds = {}

        # round_end first (for round 0 = warmup end)
        redf = getattr(
            parsed_match, "round_end_df", None)
        if redf is not None and not redf.empty:
            rc = self._find_col(
                redf.columns, ("round",))
            tc = self._find_col(
                redf.columns, ("tick",))
            if rc and tc:
                for _, row in redf.iterrows():
                    try:
                        r = int(row[rc])
                        t = int(row[tc])
                    except (ValueError, TypeError):
                        continue
                    if r == 0:
                        rounds[0] = {
                            "start": 0, "end": t}

        # round_start (same round → latest tick)
        rsdf = getattr(
            parsed_match, "rounds_df", None)
        if rsdf is not None and not rsdf.empty:
            rc = self._find_col(
                rsdf.columns, ("round",))
            tc = self._find_col(
                rsdf.columns, ("tick",))
            if rc and tc:
                for _, row in rsdf.iterrows():
                    try:
                        r = int(row[rc])
                        t = int(row[tc])
                    except (ValueError, TypeError):
                        continue
                    if r <= 0:
                        continue
                    old = rounds.get(
                        r, {}).get("start", 0)
                    if t > old:
                        rounds.setdefault(
                            r, {})["start"] = t

        # round_end (round > 0)
        if redf is not None and not redf.empty:
            rc = self._find_col(
                redf.columns, ("round",))
            tc = self._find_col(
                redf.columns, ("tick",))
            if rc and tc:
                for _, row in redf.iterrows():
                    try:
                        r = int(row[rc])
                        t = int(row[tc])
                    except (ValueError, TypeError):
                        continue
                    if r <= 0:
                        continue
                    rounds.setdefault(
                        r, {})["end"] = t

        return rounds

    def _assign_rounds(self, kills_df, rounds):
        tc = self._find_col(
            kills_df.columns, ("tick",))
        if not tc or not rounds:
            df = kills_df.copy()
            df["round"] = 0
            return df

        sorted_r = sorted(rounds.items())

        def find(tick):
            for rnd, b in sorted_r:
                s = b.get("start", 0)
                e = b.get("end", 999999999)
                if s <= tick <= e:
                    return rnd
            # Before round 1 → round 0 (warmup)
            first_formal = 0
            for rnd, b in sorted_r:
                if rnd >= 1:
                    first_formal = b.get(
                        "start", 999999999)
                    break
            if tick < first_formal:
                return 0
            # Fallback: nearest round
            best, bd = 0, float("inf")
            for rnd, b in sorted_r:
                if rnd < 1:
                    continue
                d = abs(
                    tick - b.get("start", 0))
                if d < bd:
                    bd = d
                    best = rnd
            return best

        df = kills_df.copy()
        df["round"] = df[tc].apply(
            lambda t: find(int(t))
            if pd.notna(t) else 0)
        return df

    # ═══════════════════════════════════════
    #  Create highlights
    # ═══════════════════════════════════════

    def _create_multi_highlight(
            self, hid, kills, player, round_num,
            tick_col, tick_rate):
        n = len(kills)
        s_tick = int(kills[tick_col].iloc[0])
        e_tick = int(kills[tick_col].iloc[-1])

        if n >= 5:
            hl_type = "ace"
        elif n == 4:
            hl_type = "4k"
        elif n == 3:
            hl_type = "3k"
        else:
            hl_type = "2k"

        # Stats
        hs = self._count_bool(kills, "headshot")
        nos = self._any_bool(kills, "noscope")
        wb = self._any_bool(kills, "penetrated")
        sm = self._any_bool(kills, "thrusmoke")

        # Best 8s streak
        streak = self._find_streak(
            kills[tick_col].tolist(), tick_rate)

        score = self._calc_score(
            n, hs, nos, wb, sm, streak)

        desc = self._make_desc(
            hl_type, n, hs, nos, wb, sm, streak)

        pad_s = s_tick - int(self.pre_buffer * tick_rate)
        pad_e = e_tick + int(self.post_buffer * tick_rate)

        k_ticks = [
            int(t) for t in kills[tick_col].tolist()
            if pd.notna(t)]

        return Highlight(
            highlight_id=hid,
            highlight_type=hl_type,
            player=player,
            start_tick=max(0, pad_s),
            end_tick=pad_e,
            start_seconds=0,
            end_seconds=0,
            score=score,
            kill_count=n,
            headshot_count=hs,
            has_noscope=nos,
            has_wallbang=wb,
            has_through_smoke=sm,
            round_num=round_num,
            description=desc,
            kill_ticks=k_ticks,
            max_streak=streak)

    def _create_single_highlight(
            self, hid, row, player, round_num,
            tick_col, tick_rate):
        tick = int(row.get("tick", 0))
        hs = bool(row.get("headshot", False))
        nos = bool(row.get("noscope", False))
        wb = bool(row.get("penetrated", False))
        sm = bool(row.get("thrusmoke", False))

        score = 15.0
        if hs:
            score += 5
        if nos:
            score += 20
        if wb:
            score += 15
        if sm:
            score += 10

        pad_s = tick - int(self.pre_buffer * tick_rate)
        pad_e = tick + int(self.post_buffer * tick_rate)

        parts = ["普通击杀"]
        tags = []
        if hs:
            tags.append("爆头")
        if nos:
            tags.append("盲狙")
        if wb:
            tags.append("穿墙")
        if sm:
            tags.append("烟雾")
        if tags:
            parts.append(" | ".join(tags))

        return Highlight(
            highlight_id=hid,
            highlight_type="kill",
            player=player,
            start_tick=max(0, pad_s),
            end_tick=pad_e,
            start_seconds=0,
            end_seconds=0,
            score=score,
            kill_count=1,
            headshot_count=1 if hs else 0,
            has_noscope=nos,
            has_wallbang=wb,
            has_through_smoke=sm,
            round_num=round_num,
            description=" - ".join(parts),
            kill_ticks=[tick],
            max_streak=1)

    # ═══════════════════════════════════════
    #  Streak detection (8s window)
    # ═══════════════════════════════════════

    def _find_streak(self, ticks_raw, tick_rate):
        """Best multi-kill streak within 8s."""
        ticks = sorted(
            [int(t) for t in ticks_raw
             if pd.notna(t)])
        if len(ticks) <= 1:
            return len(ticks)

        window = int(self.multi_kill_window * tick_rate)
        best = 1

        for i in range(len(ticks)):
            count = 1
            for j in range(i + 1, len(ticks)):
                if ticks[j] - ticks[i] <= window:
                    count += 1
                else:
                    break
            best = max(best, count)

        return best

    # ═══════════════════════════════════════
    #  Scoring
    # ═══════════════════════════════════════

    def _calc_score(self, n, hs, nos, wb, sm,
                    streak):
        base = {2: 30, 3: 60, 4: 120, 5: 250}
        score = base.get(n, n * 35)

        if n > 0:
            score += (hs / n) * n * 15

        if streak > 1:
            score += min(streak * 15, 50)

        if nos:
            score += 40
        if wb:
            score += 35
        if sm:
            score += 30

        return round(score, 1)

    # ═══════════════════════════════════════
    #  Description
    # ═══════════════════════════════════════

    def _make_desc(self, hl_type, n, hs, nos,
                   wb, sm, streak):
        names = {
            "ace": "ACE 王牌", "4k": "四杀",
            "3k": "三杀", "2k": "双杀"}
        parts = [names.get(
            hl_type, "{}杀".format(n))]

        tags = []

        if streak >= 2 and streak < n:
            tags.append("含{}连杀".format(streak))
        elif streak >= 2 and streak == n:
            tags.append("连杀")

        if hs == n and n > 1:
            tags.append("全爆头")
        elif hs > 0:
            tags.append("{}爆头".format(hs))

        if nos:
            tags.append("盲狙")
        if wb:
            tags.append("穿墙")
        if sm:
            tags.append("烟雾")

        if tags:
            parts.append(" | ".join(tags))
        return " - ".join(parts)

    # ═══════════════════════════════════════
    #  Helpers
    # ═══════════════════════════════════════

    @staticmethod
    def _find_col(columns, candidates):
        for name in candidates:
            if name in columns:
                return name
        return None

    @staticmethod
    def _count_bool(df, col):
        c = None
        for name in (col,):
            if name in df.columns:
                c = name
                break
        if c is None:
            return 0
        return int(df[c].astype(str).str.lower()
                   .isin(["true", "1", "yes"]).sum())

    @staticmethod
    def _any_bool(df, col):
        c = None
        for name in (col,):
            if name in df.columns:
                c = name
                break
        if c is None:
            return False
        return bool(df[c].astype(str).str.lower()
                    .isin(["true", "1", "yes"]).any())
