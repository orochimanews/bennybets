import os
import json
import logging
import re
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

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "cache")

SPORT_URL_MAP = {
    Sport.FOOTBALL: "https://paris-sportifs.pmu.fr/pari-football",
    Sport.TENNIS: "https://paris-sportifs.pmu.fr/pari-tennis",
    Sport.BASKETBALL: "https://paris-sportifs.pmu.fr/pari-basketball",
}

class PmuProvider(BaseProvider):
    """Fournisseur de cotes pour PMU Sport France avec support SSR et cache résilient"""

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout = timeout_seconds
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.cache_file = os.path.join(CACHE_DIR, "pmu_cache.json")

    @property
    def name(self) -> str:
        return "PMU"

    def fetch_events(self, sport: Sport = Sport.FOOTBALL) -> List[Event]:
        url = SPORT_URL_MAP.get(sport, "https://paris-sportifs.pmu.fr/pari-football")
        events: List[Event] = []
        html = None

        if HAS_CURL_CFFI:
            try:
                r = cffi_requests.get(url, impersonate="chrome120", timeout=self.timeout)
                if r.status_code == 200:
                    html = r.text
            except Exception as e:
                logger.debug(f"[PMU] curl_cffi err: {e}")

        if not html:
            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=self.headers) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        html = resp.text
            except Exception as e:
                logger.debug(f"[PMU] httpx err: {e}")

        if html:
            events = self._parse_html(html, sport)
            if events:
                self._save_to_cache(html)
                return events

        # Fallback Cache
        if not events and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cached_html = f.read()
                    events = self._parse_html(cached_html, sport)
                    logger.info(f"[PMU] {len(events)} matchs charges depuis le cache.")
            except Exception as e:
                logger.debug(f"[PMU] Erreur lecture cache: {e}")

        return events

    def _save_to_cache(self, html: str):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception:
            pass

    def _parse_html(self, html: str, sport: Sport) -> List[Event]:
        events: List[Event] = []
        
        # 1. Extraction si __NEXT_DATA__ contient les props d'événements
        next_m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if next_m:
            try:
                data = json.loads(next_m.group(1))
                page_props = data.get("props", {}).get("pageProps", {})
                initial_state = page_props.get("initialState", {}) or page_props
                raw_events = initial_state.get("events", []) or initial_state.get("matches", [])
                for ev in raw_events:
                    try:
                        home = ev.get("homeTeam", {}).get("name") or ev.get("homeName")
                        away = ev.get("awayTeam", {}).get("name") or ev.get("awayName")
                        if not home or not away:
                            continue
                        ev_id = str(ev.get("id", ""))
                        ev_url = ev.get("url") or f"https://paris-sportifs.pmu.fr/evenement/{ev_id}"
                        outcomes = {}
                        for o in ev.get("outcomes", []):
                            code = str(o.get("label", ""))
                            val = float(o.get("odd", 0.0))
                            if val > 1.0:
                                outcomes[code] = Odd(outcome=code, label=code, value=round(val, 2), bookmaker=self.name, url=ev_url)
                        if len(outcomes) >= 2:
                            mkt = "1N2" if "N" in outcomes else "12"
                            events.append(Event(
                                id=f"pmu_{ev_id}",
                                sport=sport,
                                home_team=home,
                                away_team=away,
                                bookmaker=self.name,
                                markets={mkt: Market(name=mkt, outcomes=outcomes)},
                                url=ev_url
                            ))
                    except Exception:
                        continue
            except Exception:
                pass

        return events
