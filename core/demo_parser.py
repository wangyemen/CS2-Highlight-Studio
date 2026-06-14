"""
CS2 Demo Parser - uses raw column names, no renaming
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
    _PARSER_VERSION = getattr(demoparser2, "__version__", "unknown")
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
            "total_damage": round(self.total_damage, 1),
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
    player_stats_a: list = field(default_factory=list)
    player_stats_b: list = field(default_factory=list)
    steam_id: str = ""

    @property
    def total_kills(self):
        return len(self.kills_df) if self.kills_df is not None else 0


class DemoParserEngine:

    # Possible column names for attacker / victim across versions
    ATTACKER_COLS = ("attacker_name", "attacker", "killer_name", "killer")
    VICTIM_COLS = ("user_name", "victim_name", "victim", "userid")
    ASSISTER_COLS = ("assister_name", "assister")
    TICK_COLS = ("tick", "tick_count", "ticks")
    HS_COLS = ("headshot", "hs", "is_headshot")
    DMG_COLS = ("dmg_health", "dmg", "damage")
    ARMOR_COLS = ("dmg_armor", "armor_damage")

    def __init__(self):
        if DemoParser is None:
            raise ImportError(
                "demoparser2 not installed. pip install demoparser2>=0.22.0")

    # ═══════════════════════════════════════
    #  Main parse
    # ═══════════════════════════════════════

    def parse_demo(self, filepath, tick_rate=64, steam_id=""):
        filepath = str(Path(filepath).resolve())
        if not os.path.exists(filepath):
            raise FileNotFoundError("Demo not found: " + filepath)

        parser = DemoParser(filepath)

        header = {}
        try:
            header = parser.parse_header() or {}
        except Exception as e:
            logger.warning("parse_header: %s", e)

        info = self._build_info(header, filepath, tick_rate)

        # Parse events with extra fields to ensure we get all data
        kills_df = self._safe_parse(parser, "player_death",
            fields=["team_num", "X", "Y", "Z", "headshot",
                     "noscope", "thrusmoke", "penetrated",
                     "flash_duration", "is_alive"])

        hurt_df = self._safe_parse(parser, "player_hurt",
            fields=["dmg_health", "dmg_armor", "hitgroup", "weapon"])

        rounds_df = self._safe_parse(parser, "round_start")
        round_end_df = self._safe_parse(parser, "round_end")

        # Debug
        if not kills_df.empty:
            logger.info("KILLS columns: %s", list(kills_df.columns))
            for i in range(min(3, len(kills_df))):
                row = kills_df.iloc[i]
                a_col = self._find_col(row.index, self.ATTACKER_COLS)
                v_col = self._find_col(row.index, self.VICTIM_COLS)
                logger.info("  row[%d] attacker=%s victim=%s",
                    i, row.get(a_col, "?"), row.get(v_col, "?"))

        if not hurt_df.empty:
            logger.info("HURT columns: %s", list(hurt_df.columns))

        # Video alignment
        info.video_offset_tick = self._find_video_offset(
            parser, steam_id)

        # Warmup
        tick_col = self._find_col(kills_df.columns, self.TICK_COLS) if not kills_df.empty else None
        kills_df, warmup_kills = self._split_warmup(kills_df, tick_rate, tick_col)
        hurt_df, _ = self._split_warmup(hurt_df, tick_rate,
            self._find_col(hurt_df.columns, self.TICK_COLS) if not hurt_df.empty else None)

        warmup_dur = 0.0
        if warmup_kills is not None and not warmup_kills.empty and tick_col:
            warmup_dur = warmup_kills[tick_col].max() / tick_rate
        if warmup_dur == 0 and rounds_df is not None and not rounds_df.empty:
            rtc = self._find_col(rounds_df.columns, self.TICK_COLS)
            if rtc:
                warmup_dur = rounds_df[rtc].min() / tick_rate
        info.warmup_duration = warmup_dur

        # Clean kills
        kills_df = self._clean_kills(kills_df, tick_rate)

        # Assign rounds to kills
        kills_df = self._assign_rounds_to_kills(
            kills_df, rounds_df, round_end_df)

        # Scores
        if round_end_df is not None and not round_end_df.empty:
            self._extract_scores(info, round_end_df)

        match = ParsedMatch(
            info=info, kills_df=kills_df, rounds_df=rounds_df,
            hurt_df=hurt_df, round_end_df=round_end_df,
            tick_interval=1.0 / tick_rate, steam_id=steam_id,
        )

        self._compute_player_stats(match)
        return match

    # ═══════════════════════════════════════
    #  Find column by multiple possible names
    # ═══════════════════════════════════════

    def _find_col(self, columns, candidates):
        """Find first matching column name from candidates tuple."""
        for name in candidates:
            if name in columns:
                return name
        return None

    # ═══════════════════════════════════════
    #  Safe parse
    # ═══════════════════════════════════════

    def _safe_parse(self, parser, event_name, fields=None):
        for fn in [
            (lambda: parser.parse_events(event_name, other=fields)) if fields else None,
            lambda: parser.parse_events(event_name),
            (lambda: parser.parse_event(event_name, other=fields)) if fields else None,
            lambda: parser.parse_event(event_name),
        ]:
            if fn is None:
                continue
            try:
                result = fn()
                if result is None:
                    continue
                if isinstance(result, pd.DataFrame):
                    return result
                if hasattr(result, "to_pandas"):
                    return result.to_pandas()
                # Handle list of tuples format
                # demoparser2 returns [(event_name, df)]
                if isinstance(result, list):
                    for item in result:
                        if (isinstance(item, tuple)
                                and len(item) >= 2):
                            df = item[1]
                            if isinstance(
                                    df, pd.DataFrame):
                                return df
                        elif isinstance(
                                item, pd.DataFrame):
                            return item
            except Exception:
                continue
        return pd.DataFrame()

    # ═══════════════════════════════════════
    #  Warmup
    # ═══════════════════════════════════════

    def _split_warmup(self, df, tick_rate, tick_col=None):
        """Keep all data including warmup.
        Video recording starts from demo beginning."""
        return df, None

    # ═══════════════════════════════════════
    #  Team detection via kill graph
    # ═══════════════════════════════════════

    def _detect_teams_from_kills(self, kills_df, attacker_col, victim_col):
        if kills_df is None or kills_df.empty:
            return {}
        if not attacker_col or not victim_col:
            return {}

        edges = {}
        for _, row in kills_df.iterrows():
            a = self._safe_str(row.get(attacker_col))
            v = self._safe_str(row.get(victim_col))
            if not a or not v or a == v:
                continue
            edges.setdefault(a, set()).add(v)
            edges.setdefault(v, set()).add(a)

        if not edges:
            return {}

        # BFS bipartite coloring
        coloring = {}
        start = max(
            ((k, len(v)) for k, v in edges.items()),
            key=lambda x: x[1])[0]

        queue = [start]
        coloring[start] = "A"
        visited = {start}

        while queue:
            current = queue.pop(0)
            next_team = "B" if coloring[current] == "A" else "A"
            for neighbor in edges.get(current, set()):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                coloring[neighbor] = next_team
                queue.append(neighbor)

        return coloring

    # ═══════════════════════════════════════
    #  Player stats
    # ═══════════════════════════════════════

    def _compute_player_stats(self, match):
        kills_df = match.kills_df
        hurt_df = match.hurt_df
        info = match.info

        total_rounds = max(info.score_ct + info.score_t, 1)
        info.competitive_rounds = total_rounds

        # Filter to formal rounds only (exclude warmup)
        if ("round" in kills_df.columns
                and not kills_df.empty):
            kills_df = kills_df[
                kills_df["round"] > 0].copy()
            logger.info(
                "Formal kills for stats: %d",
                len(kills_df))

        # Find columns dynamically
        att_col = self._find_col(kills_df.columns, self.ATTACKER_COLS) if not kills_df.empty else None
        vic_col = self._find_col(kills_df.columns, self.VICTIM_COLS) if not kills_df.empty else None
        hs_col = self._find_col(kills_df.columns, self.HS_COLS) if not kills_df.empty else None

        logger.info("Stats using: attacker=%s, victim=%s, hs=%s",
                     att_col, vic_col, hs_col)

        # Team detection
        coloring = self._detect_teams_from_kills(kills_df, att_col, vic_col)
        logger.info("Teams: %s", coloring)

        player_data = {}

        def ensure(name):
            if not name:
                return
            if name not in player_data:
                player_data[name] = {
                    "team": coloring.get(name, ""),
                    "kills": 0, "deaths": 0,
                    "assists": 0, "headshots": 0,
                    "total_damage": 0.0,
                }

        # ── Kills & Deaths ──
        if kills_df is not None and not kills_df.empty:
            for _, row in kills_df.iterrows():
                # Attacker
                if att_col:
                    attacker = self._safe_str(row.get(att_col))
                    if attacker:
                        ensure(attacker)
                        player_data[attacker]["kills"] += 1
                        if hs_col:
                            hs = row.get(hs_col, False)
                            if hs is True or str(hs).lower() == "true":
                                player_data[attacker]["headshots"] += 1

                # Victim
                if vic_col:
                    victim = self._safe_str(row.get(vic_col))
                    if victim:
                        ensure(victim)
                        player_data[victim]["deaths"] += 1

                # Assists
                as_col = self._find_col(kills_df.columns, self.ASSISTER_COLS)
                if as_col:
                    assister = self._safe_str(row.get(as_col))
                    if assister:
                        ensure(assister)
                        player_data[assister]["assists"] += 1

        logger.info("After kills: %s", {
            k: {"k": v["kills"], "d": v["deaths"]}
            for k, v in player_data.items()})

        # ── Damage ──
        if hurt_df is not None and not hurt_df.empty:
            h_att = self._find_col(hurt_df.columns, self.ATTACKER_COLS)
            h_dmg = self._find_col(hurt_df.columns, self.DMG_COLS)
            h_arm = self._find_col(hurt_df.columns, self.ARMOR_COLS)

            if h_att and h_dmg:
                for _, row in hurt_df.iterrows():
                    a = self._safe_str(row.get(h_att))
                    if not a:
                        continue
                    ensure(a)
                    dmg = 0.0
                    v = row.get(h_dmg)
                    if v is not None and not self._is_nan(v):
                        try:
                            dmg += float(v)
                        except (ValueError, TypeError):
                            pass
                    if h_arm:
                        v2 = row.get(h_arm)
                        if v2 is not None and not self._is_nan(v2):
                            try:
                                dmg += float(v2)
                            except (ValueError, TypeError):
                                pass
                    player_data[a]["total_damage"] += dmg

        # ── Build output ──
        out_a, out_b, out_unknown = [], [], []

        for name, d in player_data.items():
            kd = round(d["kills"] / max(d["deaths"], 1), 2)
            adr = round(d["total_damage"] / total_rounds, 1) \
                if total_rounds > 0 else 0

            ps = PlayerStats(
                name=name, team=d["team"],
                kills=d["kills"], deaths=d["deaths"],
                assists=d["assists"], headshots=d["headshots"],
                total_damage=round(d["total_damage"], 1),
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

        out_a.sort(key=lambda p: p["adr"], reverse=True)
        out_b.sort(key=lambda p: p["adr"], reverse=True)

        match.player_stats_a = out_a
        match.player_stats_b = out_b

    # ═══════════════════════════════════════
    #  Helpers
    # ═══════════════════════════════════════

    @staticmethod
    def _safe_str(val):
        if val is None:
            return ""
        if isinstance(val, float) and pd.isna(val):
            return ""
        s = str(val).strip()
        if not s or s in ("nan", "None", "<NULL>"):
            return ""
        return s

    @staticmethod
    def _is_nan(val):
        try:
            if val is None:
                return True
            if isinstance(val, float) and pd.isna(val):
                return True
        except Exception:
            pass
        return False

    def _build_info(self, header, filepath, tick_rate):
        info = DemoInfo(filepath=filepath)
        info.tick_rate = tick_rate
        if header:
            info.map_name = header.get("map_name", "")
            info.server_name = header.get("server_name", "")
            info.total_ticks = header.get("ticks", 0)
            if tick_rate > 0:
                info.duration_seconds = info.total_ticks / tick_rate
        return info

    def _clean_kills(self, df, tick_rate):
        if df is None or df.empty:
            return pd.DataFrame()

        att = self._find_col(df.columns, self.ATTACKER_COLS)
        tic = self._find_col(df.columns, self.TICK_COLS)
        vic = self._find_col(df.columns, self.VICTIM_COLS)

        if not att or not tic:
            logger.error("Missing attacker or tick column: %s", list(df.columns))
            return pd.DataFrame()

        df = df.copy()
        df["tick"] = df[tic].astype(float) if tic != "tick" else df["tick"]
        if "time_seconds" not in df.columns:
            df["time_seconds"] = df[tic].astype(float) / tick_rate

        for col in ("headshot", "noscope", "thrusmoke", "penetrated", "attackerblind"):
            if col not in df.columns:
                df[col] = False
            else:
                df[col] = df[col].astype(bool)

        df = df[df[att].apply(lambda x: bool(self._safe_str(x)))]
        if vic:
            df = df[df[vic].apply(lambda x: bool(self._safe_str(x)))]
            df = df[df[att] != df[vic]]
        df = df[df[tic].notna()]
        df = df.sort_values(tic).reset_index(drop=True)

        logger.info("Clean kills: %d rows", len(df))
        return df

    def _extract_scores(self, info, redf):
        winner_col = None
        for col in ("winner", "winner_team", "winning_team"):
            if col in redf.columns:
                winner_col = col
                break
        if not winner_col:
            return
        ct, t = 0, 0
        for _, row in redf.iterrows():
            w = str(row.get(winner_col, "")).upper()
            if "CT" in w:
                ct += 1
            elif "T" in w:
                t += 1
        info.score_ct = ct
        info.score_t = t

    @staticmethod
    def get_version_info():
        import sys
        return "demoparser2 v{}, pandas v{}, Python {}".format(
            _PARSER_VERSION, pd.__version__, sys.version.split()[0])

    def _find_video_offset(self, parser, steam_id):
        """Find first tick where user is alive.
        If no steam_id, find earliest alive tick
        from any player."""
        try:
            ticks_df = parser.parse_ticks([
                "steamid", "is_alive"])
            if ticks_df is None or ticks_df.empty:
                return 0

            alive = ticks_df[
                ticks_df["is_alive"] == True]

            if alive.empty:
                return 0

            if steam_id:
                player = alive[
                    alive["steamid"].astype(str)
                    == str(steam_id)]
                if not player.empty:
                    offset = int(
                        player["tick"].min())
                    logger.info(
                        "Video offset: tick %d "
                        "(steamid=%s)",
                        offset, steam_id)
                    return offset

            # Fallback: earliest alive tick
            offset = int(alive["tick"].min())
            logger.info(
                "Video offset (fallback): tick %d",
                offset)
            return offset
        except Exception as e:
            logger.warning(
                "Video offset failed: %s", e)
            return 0

    def _assign_rounds_to_kills(
            self, kills_df, rounds_df, round_end_df):
        """Assign round number to each kill."""
        if kills_df is None or kills_df.empty:
            return kills_df

        tc = self._find_col(
            kills_df.columns, self.TICK_COLS)
        if not tc:
            return kills_df

        # Build round boundaries
        rounds = {}

        if (round_end_df is not None
                and not round_end_df.empty):
            rc = self._find_col(
                round_end_df.columns, ("round",))
            te = self._find_col(
                round_end_df.columns, ("tick",))
            if rc and te:
                for _, row in round_end_df.iterrows():
                    try:
                        r = int(row[rc])
                        t = int(row[te])
                    except (ValueError, TypeError):
                        continue
                    if r == 0:
                        rounds[0] = {
                            "start": 0, "end": t}

        if (rounds_df is not None
                and not rounds_df.empty):
            rc = self._find_col(
                rounds_df.columns, ("round",))
            te = self._find_col(
                rounds_df.columns, ("tick",))
            if rc and te:
                for _, row in rounds_df.iterrows():
                    try:
                        r = int(row[rc])
                        t = int(row[te])
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
                round_end_df.columns, ("round",))
            te = self._find_col(
                round_end_df.columns, ("tick",))
            if rc and te:
                for _, row in round_end_df.iterrows():
                    try:
                        r = int(row[rc])
                        t = int(row[te])
                    except (ValueError, TypeError):
                        continue
                    if r <= 0:
                        continue
                    rounds.setdefault(
                        r, {})["end"] = t

        if not rounds:
            return kills_df

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

    @staticmethod
    def scan_demo_folder(folder):
        p = Path(folder)
        if not p.exists():
            return []
        return [str(f) for f in sorted(p.rglob("*.dem"))]
