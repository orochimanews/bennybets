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

SPORT_SLUG_MAP = {
    Sport.FOOTBALL: "football",
    Sport.TENNIS: "tennis",
    Sport.BASKETBALL: "basketball",
}

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "cache")

class UnibetProvider(BaseProvider):
    """Fournisseur de cotes en temps réel pour Unibet France (API Kambi)"""

    def __init__(self, timeout_seconds: float = 12.0):
        self.timeout = timeout_seconds
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.cache_file = os.path.join(CACHE_DIR, "unibet_cache.json")

    @property
    def name(self) -> str:
        return "Unibet"

    def fetch_events(self, sport: Sport = Sport.FOOTBALL) -> List[Event]:
        sport_slug = SPORT_SLUG_MAP.get(sport, "football")
        url = f"https://eu-offering-api.kambicdn.com/offering/v2018/ub/listView/{sport_slug}.json?lang=fr_FR&market=FR"
        events: List[Event] = []
        data = None

        # Tentative 1 : curl_cffi
        if HAS_CURL_CFFI:
            try:
                r = cffi_requests.get(url, impersonate="chrome120", timeout=self.timeout)
                if r.status_code == 200:
                    data = r.json()
            except Exception as e:
                logger.debug(f"[Unibet] curl_cffi err: {e}")

        # Tentative 2 : httpx
        if not data:
            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
            except Exception as e:
                logger.debug(f"[Unibet] httpx err: {e}")

        # Parsing
        if data:
            events = self._parse_data(data, sport)
            if events:
                self._save_to_cache(data)
                return events

        # Fallback Cache
        if not events and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    events = self._parse_data(cached_data, sport)
                    logger.info(f"[Unibet] {len(events)} matchs charges depuis le cache.")
            except Exception:
                pass

        return events

    def _save_to_cache(self, data: dict):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _parse_data(self, data: dict, sport: Sport) -> List[Event]:
        events: List[Event] = []
        raw_events = data.get("events", [])

        for item in raw_events:
            try:
                ev = item.get("event", {})
                home = ev.get("homeName")
                away = ev.get("awayName")
                if not home or not away:
                    continue

                m_id = str(ev.get("id", ""))
                is_live = (ev.get("state") == "STARTED")
                comp = ev.get("group", "")
                
                # Date
                start_str = ev.get("start")
                start_time = None
                if start_str:
                    try:
                        clean_start = start_str.replace("Z", "+00:00")
                        start_time = datetime.fromisoformat(clean_start)
                    except Exception:
                        pass

                # Score
                score_str = None
                if is_live:
                    ld = item.get("liveData", {})
                    score_obj = ld.get("score", {})
                    h_s = score_obj.get("home")
                    a_s = score_obj.get("away")
                    if h_s is not None and a_s is not None:
                        score_str = f"{h_s} - {a_s}"

                # URL
                ev_url = ev.get("url", "")
                match_url = f"https://www.unibet.fr/sport/football/{ev_url}" if ev_url else "https://www.unibet.fr/sport/football"

                # Cotes 1N2
                market_outcomes = {}
                for bo in item.get("betOffers", []):
                    # On cherche le marché 1N2 ou Vainqueur
                    crit = bo.get("criterion", {})
                    c_label = crit.get("label", "").lower()
                    if "temps réglementaire" in c_label or "résultat" in c_label or "vainqueur" in c_label or len(bo.get("outcomes", [])) in (2, 3):
                        for o in bo.get("outcomes", []):
                            raw_odd = o.get("odds")
                            if not raw_odd or float(raw_odd) <= 1000:
                                continue
                            odd_val = round(raw_odd / 1000.0, 2)
                            otype = o.get("type", "")
                            
                            if otype == "OT_ONE":
                                out_code = "1"
                            elif otype == "OT_CROSS":
                                out_code = "N"
                            elif otype == "OT_TWO":
                                out_code = "2"
                            else:
                                lbl = str(o.get("label", "")).lower()
                                if lbl in ("1", "x", "2"):
                                    out_code = "N" if lbl == "x" else lbl
                                else:
                                    continue

                            market_outcomes[out_code] = Odd(
                                outcome=out_code,
                                label=o.get("label", out_code),
                                value=odd_val,
                                bookmaker=self.name,
                                url=match_url
                            )
                        if len(market_outcomes) >= 2:
                            break

                if len(market_outcomes) >= 2:
                    mkt_name = "1N2" if "N" in market_outcomes else "12"
                    events.append(Event(
                        id=f"unibet_{m_id}",
                        sport=sport,
                        home_team=home,
                        away_team=away,
                        start_time=start_time,
                        is_live=is_live,
                        bookmaker=self.name,
                        markets={mkt_name: Market(name=mkt_name, outcomes=market_outcomes)},
                        url=match_url,
                        competition=comp,
                        score=score_str
                    ))
            except Exception:
                continue

        return events
