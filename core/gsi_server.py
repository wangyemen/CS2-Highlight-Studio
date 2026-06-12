"""
GSI Server - correct KDA/round paths, timeout detection
"""
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GameState:
    connected: bool = False
    player_name: str = ""
    player_health: int = 0
    player_armor: int = 0
    player_team: str = ""
    player_activity: str = ""
    map_name: str = ""
    map_phase: str = ""
    game_mode: str = ""
    round_phase: str = ""
    bomb_state: str = ""
    score_ct: int = 0
    score_t: int = 0
    round_num: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    mvps: int = 0
    match_started: bool = False
    match_ended: bool = False
    warmup_ended: bool = False
    last_event: dict = field(default_factory=dict)
    event_history: list = field(default_factory=list)


class GSIServer:

    CONFIG_FILENAME = "gamestate_integration_cs2highlight.cfg"
    TIMEOUT_SECONDS = 30

    def __init__(self, settings=None, port=3010):
        self.settings = settings
        self.port = settings.get("gsi_port") if settings else port
        self.state = GameState()
        self._server = None
        self._thread = None
        self._callbacks = []
        self._running = False
        self._last_data_time = 0
        self._was_receiving = False
        self._timeout_thread = None
        self._timeout_checking = False

    def add_callback(self, callback):
        self._callbacks.append(callback)

    def _notify(self):
        for cb in self._callbacks:
            try:
                cb(self.state)
            except Exception:
                pass

    def start(self):
        if self._running:
            return

        self._auto_install_config()
        server_ref = self

        class GSIHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                try:
                    data = json.loads(body)
                    server_ref._process_gsi_data(data)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"OK")

            def log_message(self, fmt, *args):
                pass

        try:
            self._server = HTTPServer(("0.0.0.0", self.port), GSIHandler)
            self._running = True
            self._last_data_time = 0
            self._thread = threading.Thread(
                target=self._server.serve_forever, daemon=True)
            self._thread.start()
            self._start_timeout_check()
            print("GSI started on port {}".format(self.port))
        except OSError as e:
            print("GSI failed: {}".format(e))

    def stop(self):
        self._running = False
        self._timeout_checking = False
        if self._server:
            self._server.shutdown()
            self._server = None
        self.state.connected = False

    # ═══════════════════════════════════════
    #  Timeout detection
    # ═══════════════════════════════════════

    def _start_timeout_check(self):
        self._timeout_checking = True
        self._timeout_thread = threading.Thread(
            target=self._timeout_loop, daemon=True)
        self._timeout_thread.start()

    def _timeout_loop(self):
        while self._timeout_checking and self._running:
            time.sleep(5)
            if self._last_data_time == 0:
                continue
            elapsed = time.time() - self._last_data_time
            if self._was_receiving and elapsed > self.TIMEOUT_SECONDS:
                if self.state.match_started and not self.state.match_ended:
                    print("GSI timeout ({:.0f}s), match ended".format(elapsed))
                    self.state.match_ended = True
                    self.state.match_started = False
                    self._notify()
                if self.state.connected:
                    self.state.connected = False
                    self._notify()
                self._was_receiving = False

    # ═══════════════════════════════════════
    #  Process GSI data - fixed KDA/round paths
    # ═══════════════════════════════════════

    def _process_gsi_data(self, data):
        self.state.connected = True
        self._last_data_time = time.time()
        self._was_receiving = True
        old_map_phase = self.state.map_phase

        # ── Provider ──
        provider = data.get("provider", {})
        if provider:
            self.state.player_name = provider.get(
                "name", self.state.player_name)

        # ── Player ──
        player = data.get("player", {})
        if player:
            self.state.player_activity = player.get("activity", "")
            self.state.player_team = player.get(
                "team", self.state.player_team)

            # Health/armor from player.state
            st = player.get("state", {})
            if st:
                self.state.player_health = st.get(
                    "health", self.state.player_health)
                self.state.player_armor = st.get(
                    "armor", self.state.player_armor)

            # K/D/A from player.match_stats (CORRECT path for CS2)
            ms = player.get("match_stats", {})
            if not ms:
                ms = player.get("stats", {})
            if ms:
                self.state.kills = ms.get("kills", self.state.kills)
                self.state.deaths = ms.get("deaths", self.state.deaths)
                self.state.assists = ms.get("assists", self.state.assists)
                self.state.mvps = ms.get("mvps", self.state.mvps)
            # Fallback: some versions put kda in player.state
            elif st:
                self.state.kills = st.get("kills", self.state.kills)
                self.state.deaths = st.get("deaths", self.state.deaths)
                self.state.assists = st.get(
                    "assists", self.state.assists)

        # ── Map ──
        gmap = data.get("map", {})
        if gmap:
            new_phase = gmap.get("phase", "")
            self.state.map_name = gmap.get(
                "name", self.state.map_name)
            self.state.map_phase = new_phase
            self.state.game_mode = gmap.get(
                "mode", self.state.game_mode)
            self.state.score_ct = gmap.get("team_ct", {}).get(
                "score", self.state.score_ct)
            self.state.score_t = gmap.get("team_t", {}).get(
                "score", self.state.score_t)

            # Round number from map (fallback)
            map_rnd = gmap.get("round")
            if isinstance(map_rnd, int) and map_rnd > 0:
                self.state.round_num = map_rnd

            # warmup → live = first round started
            if old_map_phase == "warmup" and new_phase == "live":
                self.state.warmup_ended = True
            # match ended
            if old_map_phase != "gameover" and new_phase == "gameover":
                self.state.match_ended = True
                self.state.match_started = False
            # new match
            if new_phase in ("live", "warmup") \
                    and not self.state.match_started:
                self.state.match_started = True
                self.state.match_ended = False
                self.state.warmup_ended = False

        # ── Round (primary source for round number) ──
        rnd = data.get("round", {})
        if rnd:
            rp = rnd.get("phase", "")
            if rp:
                self.state.round_phase = rp
            rn = rnd.get("round")
            if isinstance(rn, int) and rn > 0:
                self.state.round_num = rn
            bs = rnd.get("bomb", "")
            if bs:
                self.state.bomb_state = bs

        self.state.last_event = data
        self.state.event_history.append(data)
        if len(self.state.event_history) > 100:
            self.state.event_history = self.state.event_history[-50:]

        self._notify()

    # ═══════════════════════════════════════
    #  Status
    # ═══════════════════════════════════════

    def is_gsi_receiving(self):
        if self._last_data_time == 0:
            return False
        return (time.time() - self._last_data_time) < 10

    def get_status_text(self):
        if not self.state.connected:
            return "GSI 未连接"
        if self.state.map_phase == "gameover":
            return "比赛结束"
        if self.state.match_started:
            return "{} {}-{}".format(
                self.state.map_name,
                self.state.score_ct,
                self.state.score_t)
        return "GSI 就绪"

    # ═══════════════════════════════════════
    #  Config auto-install
    # ═══════════════════════════════════════

    def _auto_install_config(self):
        if not self.settings:
            return
        cs2_path = self.settings.get("cs2_install_path", "")
        if not cs2_path:
            try:
                from core.game_detector import auto_detect_cs2
                cs2_path, _ = auto_detect_cs2()
                if cs2_path:
                    self.settings.set("cs2_install_path", cs2_path)
                    self.settings.save()
            except Exception:
                pass
        if not cs2_path:
            return
        for sub in ("game/csgo/cfg", "game/cs2/cfg", "csgo/cfg"):
            d = Path(cs2_path) / sub
            if d.exists():
                try:
                    (d / self.CONFIG_FILENAME).write_text(
                        self._make_config(), encoding="utf-8")
                    print("GSI config: " + str(d / self.CONFIG_FILENAME))
                    return
                except Exception:
                    continue

    def _make_config(self):
        return (
            '"CS2 Highlight Studio"\n'
            '{{\n'
            '    "uri"       "http://127.0.0.1:{port}/"\n'
            '    "timeout"   "5.0"\n'
            '    "buffer"    "0.1"\n'
            '    "throttle"  "0.5"\n'
            '    "heartbeat" "30.0"\n'
            '    "data" {{\n'
            '        "provider"            "1"\n'
            '        "map"                 "1"\n'
            '        "round"               "1"\n'
            '        "player_id"           "1"\n'
            '        "player_state"        "1"\n'
            '        "player_weapons"      "1"\n'
            '        "player_match_stats"  "1"\n'
            '        "allplayers_id"       "1"\n'
            '        "allplayers_state"    "1"\n'
            '        "allplayers_match_stats" "1"\n'
            '    }}\n'
            '}}\n'
        ).format(port=self.port)

    def install_gsi_config(self, cs2_path):
        for sub in ("game/csgo/cfg", "game/cs2/cfg", "csgo/cfg"):
            d = Path(cs2_path) / sub
            if d.exists():
                (d / self.CONFIG_FILENAME).write_text(
                    self._make_config(), encoding="utf-8")
                return True
        return False

    def get_config_status(self):
        cs2 = self.settings.get("cs2_install_path", "") \
            if self.settings else ""
        if not cs2:
            return False, "CS2 路径未设置"
        for sub in ("game/csgo/cfg", "game/cs2/cfg"):
            f = Path(cs2) / sub / self.CONFIG_FILENAME
            if f.exists():
                return True, str(f)
        return False, "未找到 GSI 配置"
