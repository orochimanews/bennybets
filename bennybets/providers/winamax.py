import os
import json
import logging
from typing import List, Optional
from datetime import datetime

try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

import urllib.request
import httpx

from bennybets.core.models import Event, Sport, Market, Odd
from bennybets.providers.base import BaseProvider

logger = logging.getLogger(__name__)

SPORT_ID_MAP = {
    Sport.FOOTBALL: 1,
    Sport.TENNIS: 2,
    Sport.BASKETBALL: 5,
    Sport.RUGBY: 12,
}

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "cache")

class WinamaxProvider(BaseProvider):
    """Fournisseur de cotes en temps réel pour Winamax France avec bypass TLS et cache résilient"""

    def __init__(self, timeout_seconds: float = 12.0):
        self.timeout = timeout_seconds
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.cache_file = os.path.join(CACHE_DIR, "winamax_cache.json")

    @property
    def name(self) -> str:
        return "Winamax"

    def fetch_events(self, sport: Sport = Sport.FOOTBALL) -> List[Event]:
        sport_id = SPORT_ID_MAP.get(sport, 1)
        url = f"https://www.winamax.fr/paris-sportifs/sports/{sport_id}"
        events: List[Event] = []
        html = None

        # Méthode 1 (Ultra-fiable) : curl_cffi impersonate chrome120
        if HAS_CURL_CFFI:
            try:
                r = cffi_requests.get(url, impersonate="chrome120", timeout=self.timeout)
                if r.status_code == 200:
                    html = r.text
            except Exception as e:
                logger.debug(f"[Winamax] curl_cffi err: {e}")

        # Méthode 2 : urllib fallback
        if not html:
            try:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        html = resp.read().decode("utf-8", errors="ignore")
            except Exception as e:
                logger.debug(f"[Winamax] urllib err: {e}")

        # Méthode 3 : httpx fallback
        if not html:
            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=self.headers) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        html = resp.text
            except Exception as e:
                logger.debug(f"[Winamax] httpx err: {e}")

        # Parsing
        if html:
            idx = html.find("var PRELOADED_STATE = ")
            if idx != -1:
                try:
                    raw = html[idx + len("var PRELOADED_STATE = "):]
                    decoder = json.JSONDecoder()
                    data, _ = decoder.raw_decode(raw)
                    events = self._parse_state(data, sport)
                    if events:
                        self._save_to_cache(data)
                        return events
                except Exception as pe:
                    logger.debug(f"[Winamax] Erreur parsing: {pe}")

        # Fallback Cache
        if not events and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    events = self._parse_state(cached_data, sport)
                    logger.info(f"[Winamax] {len(events)} matchs charges depuis le cache.")
            except Exception:
                pass

        return events

    def _save_to_cache(self, data: dict):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _parse_state(self, data: dict, sport: Sport) -> List[Event]:
        events: List[Event] = []
        matches = data.get("matches", {})
        bets = data.get("bets", {})
        outcomes = data.get("outcomes", {})
        odds_dict = data.get("odds", {})
        tournaments = data.get("tournaments", {})

        for match_id, m in matches.items():
            try:
                title = m.get("title", "")
                if " - " in title:
                    parts = title.split(" - ", 1)
                    home_team, away_team = parts[0].strip(), parts[1].strip()
                elif " vs " in title.lower():
                    parts = title.lower().split(" vs ", 1)
                    home_team, away_team = parts[0].strip(), parts[1].strip()
                else:
                    continue

                status = m.get("status", "PREMATCH")
                is_live = (status == "LIVE")
                tourn_id = str(m.get("tournamentId", ""))
                competition = tournaments.get(tourn_id, {}).get("tournamentName", "")

                start_ts = m.get("matchStart")
                start_time = datetime.fromtimestamp(start_ts) if start_ts else None

                score_str = None
                if is_live:
                    live_data = m.get("live", {})
                    if live_data:
                        h_s = live_data.get("scoreHomeTeam")
                        a_s = live_data.get("scoreAwayTeam")
                        if h_s is not None and a_s is not None:
                            score_str = f"{h_s} - {a_s}"

                main_bet_id = str(m.get("mainBetId", ""))
                bet = bets.get(main_bet_id)
                if not bet:
                    continue

                outcome_ids = bet.get("outcomes", [])
                market_outcomes = {}
                match_url = f"https://www.winamax.fr/paris-sportifs/match/{match_id}"

                for oid in outcome_ids:
                    oid_str = str(oid)
                    out_info = outcomes.get(oid_str, {})
                    odd_val = odds_dict.get(oid_str)
                    if odd_val is None or float(odd_val) <= 1.0:
                        continue

                    odd_float = float(odd_val)
                    code = str(out_info.get("code", "")).lower()
                    label = out_info.get("label", "")

                    if code == "1" or "1" in code:
                        out_code = "1"
                    elif code in ("x", "n", "nul") or "nul" in label.lower():
                        out_code = "N"
                    elif code == "2" or "2" in code:
                        out_code = "2"
                    else:
                        out_code = label

                    market_outcomes[out_code] = Odd(
                        outcome=out_code,
                        label=label,
                        value=odd_float,
                        bookmaker=self.name,
                        url=match_url
                    )

                if len(market_outcomes) >= 2:
                    market_name = "1N2" if "N" in market_outcomes else "12"
                    events.append(Event(
                        id=f"winamax_{match_id}",
                        sport=sport,
                        home_team=home_team,
                        away_team=away_team,
                        start_time=start_time,
                        is_live=is_live,
                        bookmaker=self.name,
                        markets={market_name: Market(name=market_name, outcomes=market_outcomes)},
                        url=match_url,
                        competition=competition,
                        score=score_str
                    ))
            except Exception:
                continue

        return events
