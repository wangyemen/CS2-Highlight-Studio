"""
CS2 Demo Parser - demoparser2 v0.41.x compatible
"""
import os
import logging
from pathlib import Path
from dataclasses import dataclass, field

import pandas as pd

logger = logging.getLogger(__name__)

DemoParser = None
_PARSER_VERSION = ""

try:
    import demoparser2
    DemoParser = demoparser2.DemoParser
    _PARSER_VERSION = getattr(
        demoparser2, "__version__", "unknown")
except ImportError:
    pass


@dataclass
class DemoInfo:
    filepath: str
    map_name: str = ""
    server_name: str = ""
    duration_seconds: float = 0.0
    tick_rate: int = 64
    total_ticks: int = 0
    score_ct: int = 0
    score_t: int = 0
    team_a_name: str = "Team A"
    team_b_name: str = "Team B"
    warmup_duration: float = 0.0
    competitive_rounds: int = 0
    video_offset_tick: int = 0

    @property
    def filename(self):
        return Path(self.filepath).name


@dataclass
class PlayerStats:
    name: str = ""
    team: str = ""
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    headshots: int = 0
    total_damage: float = 0.0
    adr: float = 0.0
    kd: float = 0.0

    def to_dict(self):
        return {
            "name": self.name,
            "team": self.team,
            "kills": self.kills,
            "deaths": self.deaths,
            "assists": self.assists,
            "headshots": self.headshots,
            "total_damage": round(
                self.total_damage, 1),
            "adr": round(self.adr, 1),
            "kd": round(self.kd, 2),
        }


@dataclass
class ParsedMatch:
    info: DemoInfo
    kills_df: pd.DataFrame = None
    rounds_df: pd.DataFrame = None
    hurt_df: pd.DataFrame = None
    round_end_df: pd.DataFrame = None
    tick_interval: float = 1.0 / 64.0
    player_stats_a: list = field(
        default_factory=list)
    player_stats_b: list = field(
        default_factory=list)
    steam_id: str = ""

    @property
    def total_kills(self):
        return (len(self.kills_df)
                if self.kills_df is not None
                else 0)


class DemoParserEngine:

    ATTACKER_COLS = (
        "attacker_name", "attacker",
        "killer_name", "killer")
    VICTIM_COLS = (
        "user_name", "victim_name",
        "victim", "userid")
    ASSISTER_COLS = (
        "assister_name", "assister")
    TICK_COLS = (
        "tick", "tick_count", "ticks")
    HS_COLS = (
        "headshot", "hs", "is_headshot")
    DMG_COLS = (
        "dmg_health", "dmg", "damage")
    ARMOR_COLS = (
        "dmg_armor", "armor_damage")

    def __init__(self):
        if DemoParser is None:
            raise ImportError(
                "demoparser2 not installed. "
                "pip install demoparser2>=0.41.0")

    # ═══════════════════════════════════════
    #  Main parse
    # ═══════════════════════════════════════

    def parse_demo(self, filepath,
                   tick_rate=0, steam_id=""):
        filepath = str(
            Path(filepath).resolve())
        if not os.path.exists(filepath):
            raise FileNotFoundError(
                "Demo not found: " + filepath)

        parser = DemoParser(filepath)
        print("[Parser] File: {}".format(
            os.path.basename(filepath)))

        # 1. Tick data first (no tick rate needed)
        tick_info = self._parse_tick_info(parser)

        # 2. Tick rate
        # tick_rate=0 means Auto
        actual_tr = self._detect_tick_rate(
            parser, tick_rate, tick_info)
        print("[Parser] Tick rate: {}".format(
            actual_tr))

        # 3. Header
        header = {}
        try:
            header = parser.parse_header() or {}
        except Exception as e:
            print("[Parser] Header: {}".format(e))
        info = self._build_info(
            header, filepath, actual_tr)
        print("[Parser] Map: {}".format(
            info.map_name))

        # 4. Offset + round bounds
        warmup_end = tick_info["warmup_end_tick"]
        round_bounds = tick_info["rounds"]

        info.video_offset_tick = warmup_end
        info.warmup_duration = (
            warmup_end / actual_tr
            if actual_tr > 0 else 0)
        print("[Parser] Offset: tick {} "
              "(warmup {:.1f}s)".format(
                  warmup_end, info.warmup_duration))
        print("[Parser] Rounds: {}".format(
            len(round_bounds)))

        # 5. Events (v0.41 list API)
        kills_df = self._safe_parse(
            parser, "player_death",
            fields=["team_num", "X", "Y", "Z",
                     "headshot", "noscope",
                     "thrusmoke", "penetrated",
                     "flash_duration", "is_alive"])
        hurt_df = self._safe_parse(
            parser, "player_hurt",
            fields=["dmg_health", "dmg_armor",
                     "hitgroup", "weapon"])
        rounds_df = self._safe_parse(
            parser, "round_start")
        round_end_df = self._safe_parse(
            parser, "round_end")

        print("[Parser] Kills: {}".format(
            len(kills_df)
            if kills_df is not None
            and not kills_df.empty else 0))
        print("[Parser] Round start: {}".format(
            len(rounds_df)
            if rounds_df is not None
            and not rounds_df.empty else 0))
        print("[Parser] Round end: {}".format(
            len(round_end_df)
            if round_end_df is not None
            and not round_end_df.empty else 0))

        # 6. Clean kills
        kills_df = self._clean_kills(
            kills_df, actual_tr)

        # 7. Assign rounds to kills
        kills_df = self._assign_rounds(
            kills_df, round_bounds,
            rounds_df, round_end_df)

        # 8. Scores
        if (round_end_df is not None
                and not round_end_df.empty):
            self._extract_scores(
                info, round_end_df)
        print("[Parser] Score: {}-{}".format(
            info.score_ct, info.score_t))

        # 9. Build match
        match = ParsedMatch(
            info=info,
            kills_df=kills_df,
            rounds_df=rounds_df,
            hurt_df=hurt_df,
            round_end_df=round_end_df,
            tick_interval=1.0 / actual_tr,
            steam_id=steam_id,
        )

        self._compute_player_stats(match)
        print("[Parser] Team A: {} players, "
              "Team B: {} players".format(
                  len(match.player_stats_a),
                  len(match.player_stats_b)))

        return match

    # ═══════════════════════════════════════
    #  Tick rate detection
    # ═══════════════════════════════════════

    def _detect_tick_rate(self, parser,
                          configured, tick_info):
        """tick_rate > 0 → user chose 64/128.
        tick_rate == 0 → Auto: use round data
        to pick the most realistic tick rate."""

        # Non-Auto: use directly
        if configured and configured > 0:
            return configured

        # Parser attributes
        for attr in ("tick_rate", "_tick_rate",
                     "ticks_per_second"):
            val = getattr(parser, attr, None)
            if val:
                try:
                    v = int(val)
                    if v > 0:
                        print(
                            "[Parser] tick rate "
                            "from parser: "
                            "{}".format(v))
                        return v
                except (ValueError, TypeError):
                    pass

        # Header
        try:
            header = parser.parse_header() or {}
            for key in ("tick_rate",
                        "ticks_per_second"):
                if key in header:
                    v = int(header[key])
                    if v > 0:
                        print(
                            "[Parser] tick rate "
                            "from header: "
                            "{}".format(v))
                        return v
            if "interval_per_tick" in header:
                ival = float(
                    header["interval_per_tick"])
                if ival > 0:
                    return int(round(1.0 / ival))
        except Exception:
            pass

        # Round-boundary heuristic
        if (tick_info
                and tick_info.get("rounds")):
            rounds = tick_info["rounds"]
            warmup_end = tick_info.get(
                "warmup_end_tick", 0)

            # No warmup → can't determine
            if warmup_end < 10:
                print(
                    "[Parser] No warmup data, "
                    "defaulting to 64 tick")
                return 64

            all_ends = [
                b["end"]
                for b in rounds.values()]
            all_starts = [
                b["start"]
                for b in rounds.values()]
            comp_ticks = max(all_ends) - min(
                all_starts) if all_starts else 0
            num_rounds = len(rounds)

            print(
                "[Parser] Auto-detect: "
                "warmup_ticks={}, "
                "comp_ticks={}, "
                "rounds={}".format(
                    warmup_end, comp_ticks,
                    num_rounds))

            if comp_ticks > 0 and num_rounds > 0:
                best_tr = 64
                best_score = float("-inf")

                for cand in (128, 64, 256, 32):
                    warmup_s = warmup_end / cand
                    avg_round_s = (
                        comp_ticks
                        / num_rounds / cand)
                    total_s = comp_ticks / cand

                    score = 0

                    # Warmup: 10-120s valid
                    if 10 <= warmup_s <= 120:
                        score += 5
                    else:
                        score -= 5

                    # Avg round: 45-130s normal
                    if 45 <= avg_round_s <= 130:
                        score += 20
                    elif (30 <= avg_round_s
                          <= 180):
                        score += 5
                    else:
                        score -= 15

                    # Total: 10-50 min
                    if 600 <= total_s <= 3000:
                        score += 10
                    elif 300 <= total_s <= 4800:
                        score += 3
                    else:
                        score -= 10

                    print(
                        "  {} tick: "
                        "warmup={:.0f}s, "
                        "avg_round={:.0f}s, "
                        "total={:.0f}s "
                        "(score={})".format(
                            cand, warmup_s,
                            avg_round_s,
                            total_s, score))

                    if score > best_score:
                        best_score = score
                        best_tr = cand

                print(
                    "[Parser] Auto → "
                    "{}".format(best_tr))
                return best_tr

        # Fallback
        return 64

    # ═══════════════════════════════════════
    #  Tick data → offset + round bounds
    # ═══════════════════════════════════════

    def _parse_tick_info(self, parser):
        """From tick data: warmup end tick,
        round start/end ticks.
        Uses is_warmup_period + total_rounds_played."""
        result = {
            "warmup_end_tick": 0,
            "rounds": {}}

        try:
            print("[Parser] Parsing ticks...")
            tick_df = parser.parse_ticks(
                ["is_warmup_period",
                 "total_rounds_played"])
            if tick_df is None or tick_df.empty:
                print("[Parser] Tick data empty")
                return result

            tick_df = tick_df.drop_duplicates(
                subset=["tick"], keep="first")
            tick_df = tick_df.sort_values("tick")
            print("[Parser] Tick rows: {}".format(
                len(tick_df)))

            # Warmup end
            warmup = tick_df[
                tick_df["is_warmup_period"]
                .astype(str).str.lower()
                .isin(["true", "1", "1.0"])]
            if not warmup.empty:
                result["warmup_end_tick"] = int(
                    warmup["tick"].max()) + 1
            print("[Parser] Warmup end: tick {}".format(
                result["warmup_end_tick"]))

            # Round boundaries
            playing = tick_df[
                ~tick_df["is_warmup_period"]
                .astype(str).str.lower()
                .isin(["true", "1", "1.0"])]

            if not playing.empty:
                states = playing.groupby(
                    "total_rounds_played"
                )["tick"].agg(
                    ["min", "max"]).reset_index()

                for _, row in states.iterrows():
                    counter = int(
                        row["total_rounds_played"])
                    rnd = counter + 1
                    start = int(row["min"])
                    end = int(row["max"])
                    result["rounds"][rnd] = {
                        "start": start,
                        "end": end}

                for rnd, b in sorted(
                        result["rounds"].items()):
                    print("  Round {}: "
                          "tick {}~{}".format(
                              rnd, b["start"],
                              b["end"]))

        except Exception as e:
            print("[Parser] Tick error: {}".format(
                e))

        return result

    # ═══════════════════════════════════════
    #  Safe parse (v0.41 list API)
    # ═══════════════════════════════════════

    def _safe_parse(self, parser, event_name,
                    fields=None):
        attempts = []
        if fields:
            attempts.append(
                lambda: parser.parse_events(
                    [event_name], other=fields))
        attempts.append(
            lambda: parser.parse_events(
                [event_name]))
        if fields:
            attempts.append(
                lambda: parser.parse_events(
                    event_name, other=fields))
        attempts.append(
            lambda: parser.parse_events(
                event_name))

        for fn in attempts:
            try:
                result = fn()
                if result is None:
                    continue

                if isinstance(result,
                              pd.DataFrame):
                    if not result.empty:
                        return result
                    continue

                if hasattr(result, "to_pandas"):
                    df = result.to_pandas()
                    if not df.empty:
                        return df
                    continue

                if isinstance(result, list):
                    for item in result:
                        if (isinstance(item, tuple)
                                and len(item) >= 2):
                            df = item[1]
                            if (isinstance(
                                    df, pd.DataFrame)
                                    and not df.empty):
                                return df
                            if hasattr(
                                    df, "to_pandas"):
                                df = df.to_pandas()
                                if not df.empty:
                                    return df
                        elif (isinstance(
                                item, pd.DataFrame)
                              and not item.empty):
                            return item

            except Exception:
                continue

        return pd.DataFrame()

    # ═══════════════════════════════════════
    #  Assign rounds to kills
    # ═══════════════════════════════════════

    def _assign_rounds(self, kills_df,
                       round_bounds,
                       rounds_df=None,
                       round_end_df=None):
        if kills_df is None or kills_df.empty:
            return kills_df

        tc = self._find_col(
            kills_df.columns, self.TICK_COLS)
        if not tc:
            return kills_df

        # Primary: tick data
        if round_bounds:
            sorted_r = sorted(
                round_bounds.items())

            def find_round(tick):
                for rnd, b in sorted_r:
                    if (b["start"] <= tick
                            <= b["end"]):
                        return rnd
                if sorted_r:
                    first = sorted_r[0][1][
                        "start"]
                    if tick < first:
                        return 0
                return 0

            df = kills_df.copy()
            df["round"] = df[tc].apply(
                lambda t: find_round(int(t))
                if pd.notna(t) else 0)

            counts = (df["round"].value_counts()
                      .sort_index().to_dict())
            print("[Parser] Kill rounds: {}".format(
                counts))
            return df

        # Fallback: events
        return self._assign_rounds_from_events(
            kills_df, rounds_df, round_end_df)

    def _assign_rounds_from_events(
            self, kills_df, rounds_df,
            round_end_df):
        if kills_df is None or kills_df.empty:
            return kills_df

        tc = self._find_col(
            kills_df.columns, self.TICK_COLS)
        if not tc:
            return kills_df

        rounds = self._rounds_from_events(
            rounds_df, round_end_df)

        if not rounds:
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
            first = 0
            for rnd, b in sorted_r:
                if rnd >= 1:
                    first = b.get(
                        "start", 999999999)
                    break
            if tick < first:
                return 0
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

    def _rounds_from_events(self, rounds_df,
                            round_end_df):
        rounds = {}

        if (rounds_df is not None
                and not rounds_df.empty):
            rc = self._find_col(
                rounds_df.columns, ("round",))
            tc = self._find_col(
                rounds_df.columns,
                self.TICK_COLS)
            if rc and tc:
                for _, row in rounds_df.iterrows():
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

        if (round_end_df is not None
                and not round_end_df.empty):
            rc = self._find_col(
                round_end_df.columns,
                ("round",))
            tc = self._find_col(
                round_end_df.columns,
                self.TICK_COLS)
            if rc and tc:
                for _, row in round_end_df.iterrows():
                    try:
                        r = int(row[rc])
                        t = int(row[tc])
                    except (ValueError, TypeError):
                        continue
                    if r == 0:
                        rounds[0] = {
                            "start": 0, "end": t}
                    elif r > 0:
                        rounds.setdefault(
                            r, {})["end"] = t

        return rounds

    # ═══════════════════════════════════════
    #  Team detection via kill graph
    # ═══════════════════════════════════════

    def _detect_teams_from_kills(
            self, kills_df, attacker_col,
            victim_col):
        if kills_df is None or kills_df.empty:
            return {}
        if not attacker_col or not victim_col:
            return {}

        edges = {}
        for _, row in kills_df.iterrows():
            a = self._safe_str(
                row.get(attacker_col))
            v = self._safe_str(
                row.get(victim_col))
            if not a or not v or a == v:
                continue
            edges.setdefault(a, set()).add(v)
            edges.setdefault(v, set()).add(a)

        if not edges:
            return {}

        coloring = {}
        start = max(
            ((k, len(v))
             for k, v in edges.items()),
            key=lambda x: x[1])[0]

        queue = [start]
        coloring[start] = "A"
        visited = {start}

        while queue:
            current = queue.pop(0)
            nxt = ("B"
                   if coloring[current] == "A"
                   else "A")
            for nb in edges.get(current, set()):
                if nb in visited:
                    continue
                visited.add(nb)
                coloring[nb] = nxt
                queue.append(nb)

        return coloring

    # ═══════════════════════════════════════
    #  Player stats
    # ═══════════════════════════════════════

    def _compute_player_stats(self, match):
        kills_df = match.kills_df
        hurt_df = match.hurt_df
        info = match.info

        total_rounds = max(
            info.score_ct + info.score_t, 1)
        info.competitive_rounds = total_rounds

        if ("round" in kills_df.columns
                and not kills_df.empty):
            kills_df = kills_df[
                kills_df["round"] > 0].copy()
            print("[Parser] Formal kills: {}".format(
                len(kills_df)))

        att_col = (self._find_col(
            kills_df.columns, self.ATTACKER_COLS)
            if not kills_df.empty else None)
        vic_col = (self._find_col(
            kills_df.columns, self.VICTIM_COLS)
            if not kills_df.empty else None)
        hs_col = (self._find_col(
            kills_df.columns, self.HS_COLS)
            if not kills_df.empty else None)

        coloring = self._detect_teams_from_kills(
            kills_df, att_col, vic_col)
        print("[Parser] Teams: {}".format(
            coloring))

        player_data = {}

        def ensure(name):
            if not name:
                return
            if name not in player_data:
                player_data[name] = {
                    "team": coloring.get(name, ""),
                    "kills": 0, "deaths": 0,
                    "assists": 0, "headshots": 0,
                    "total_damage": 0.0}

        if kills_df is not None \
                and not kills_df.empty:
            for _, row in kills_df.iterrows():
                if att_col:
                    attacker = self._safe_str(
                        row.get(att_col))
                    if attacker:
                        ensure(attacker)
                        player_data[attacker][
                            "kills"] += 1
                        if hs_col:
                            hs = row.get(
                                hs_col, False)
                            if (hs is True
                                    or str(hs).lower()
                                    == "true"):
                                player_data[
                                    attacker][
                                    "headshots"] += 1

                if vic_col:
                    victim = self._safe_str(
                        row.get(vic_col))
                    if victim:
                        ensure(victim)
                        player_data[victim][
                            "deaths"] += 1

                as_col = self._find_col(
                    kills_df.columns,
                    self.ASSISTER_COLS)
                if as_col:
                    assister = self._safe_str(
                        row.get(as_col))
                    if assister:
                        ensure(assister)
                        player_data[assister][
                            "assists"] += 1

        if hurt_df is not None \
                and not hurt_df.empty:
            h_att = self._find_col(
                hurt_df.columns,
                self.ATTACKER_COLS)
            h_dmg = self._find_col(
                hurt_df.columns, self.DMG_COLS)
            h_arm = self._find_col(
                hurt_df.columns, self.ARMOR_COLS)

            if h_att and h_dmg:
                for _, row in hurt_df.iterrows():
                    a = self._safe_str(
                        row.get(h_att))
                    if not a:
                        continue
                    ensure(a)
                    dmg = 0.0
                    v = row.get(h_dmg)
                    if (v is not None
                            and not self._is_nan(v)):
                        try:
                            dmg += float(v)
                        except (ValueError,
                                TypeError):
                            pass
                    if h_arm:
                        v2 = row.get(h_arm)
                        if (v2 is not None
                                and not self._is_nan(
                                    v2)):
                            try:
                                dmg += float(v2)
                            except (ValueError,
                                    TypeError):
                                pass
                    player_data[a][
                        "total_damage"] += dmg

        out_a, out_b, out_unknown = [], [], []

        for name, d in player_data.items():
            kd = round(
                d["kills"]
                / max(d["deaths"], 1), 2)
            adr = (round(
                d["total_damage"]
                / total_rounds, 1)
                if total_rounds > 0 else 0)

            ps = PlayerStats(
                name=name, team=d["team"],
                kills=d["kills"],
                deaths=d["deaths"],
                assists=d["assists"],
                headshots=d["headshots"],
                total_damage=round(
                    d["total_damage"], 1),
                adr=adr, kd=kd,
            ).to_dict()

            if d["team"] == "A":
                out_a.append(ps)
            elif d["team"] == "B":
                out_b.append(ps)
            else:
                out_unknown.append(ps)

        for ps in out_unknown:
            if len(out_a) <= len(out_b):
                out_a.append(ps)
            else:
                out_b.append(ps)

        out_a.sort(
            key=lambda p: p["adr"],
            reverse=True)
        out_b.sort(
            key=lambda p: p["adr"],
            reverse=True)

        match.player_stats_a = out_a
        match.player_stats_b = out_b

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
    def _safe_str(val):
        if val is None:
            return ""
        if isinstance(val, float) \
                and pd.isna(val):
            return ""
        s = str(val).strip()
        if not s or s in ("nan", "None",
                          "<NULL>"):
            return ""
        return s

    @staticmethod
    def _is_nan(val):
        try:
            if val is None:
                return True
            if isinstance(val, float) \
                    and pd.isna(val):
                return True
        except Exception:
            pass
        return False

    def _build_info(self, header, filepath,
                    tick_rate):
        info = DemoInfo(filepath=filepath)
        info.tick_rate = tick_rate
        if header:
            info.map_name = header.get(
                "map_name", "")
            info.server_name = header.get(
                "server_name", "")
            info.total_ticks = header.get(
                "ticks", 0)
            if tick_rate > 0:
                info.duration_seconds = (
                    info.total_ticks / tick_rate)
        return info

    def _clean_kills(self, df, tick_rate):
        if df is None or df.empty:
            return pd.DataFrame()

        att = self._find_col(
            df.columns, self.ATTACKER_COLS)
        tic = self._find_col(
            df.columns, self.TICK_COLS)
        vic = self._find_col(
            df.columns, self.VICTIM_COLS)

        if not att or not tic:
            print("[Parser] Missing kill columns: "
                  "{}".format(list(df.columns)))
            return pd.DataFrame()

        df = df.copy()
        df["tick"] = (
            df[tic].astype(float)
            if tic != "tick" else df["tick"])
        if "time_seconds" not in df.columns:
            df["time_seconds"] = (
                df[tic].astype(float)
                / tick_rate)

        for col in ("headshot", "noscope",
                    "thrusmoke", "penetrated",
                    "attackerblind"):
            if col not in df.columns:
                df[col] = False
            else:
                df[col] = df[col].astype(bool)

        df = df[df[att].apply(
            lambda x: bool(
                self._safe_str(x)))]
        if vic:
            df = df[df[vic].apply(
                lambda x: bool(
                    self._safe_str(x)))]
            df = df[df[att] != df[vic]]
        df = df[df[tic].notna()]
        df = df.sort_values(tic).reset_index(
            drop=True)
        return df

    def _extract_scores(self, info, redf):
        winner_col = None
        for col in ("winner", "winner_team",
                    "winning_team"):
            if col in redf.columns:
                winner_col = col
                break
        if not winner_col:
            return
        ct, t = 0, 0
        for _, row in redf.iterrows():
            w = str(
                row.get(winner_col, "")).upper()
            if "CT" in w:
                ct += 1
            elif "T" in w:
                t += 1
        info.score_ct = ct
        info.score_t = t

    @staticmethod
    def get_version_info():
        import sys
        return (
            "demoparser2 v{}, pandas v{}, "
            "Python {}".format(
                _PARSER_VERSION,
                pd.__version__,
                sys.version.split()[0]))

    @staticmethod
    def scan_demo_folder(folder):
        p = Path(folder)
        if not p.exists():
            return []
        return [str(f) for f in sorted(
            p.rglob("*.dem"))]
