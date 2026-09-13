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

SPORT_ID_MAP = {
    Sport.FOOTBALL: 4,
    Sport.TENNIS: 5,
    Sport.BASKETBALL: 7,
}

class BwinProvider(BaseProvider):
    """Fournisseur de cotes pour Bwin France avec support CDS API et cache résilient"""

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout = timeout_seconds
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://sports.bwin.fr/fr/sports/football-4',
        }
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.cache_file = os.path.join(CACHE_DIR, "bwin_cache.json")

    @property
    def name(self) -> str:
        return "Bwin"

    def fetch_events(self, sport: Sport = Sport.FOOTBALL) -> List[Event]:
        sport_id = SPORT_ID_MAP.get(sport, 4)
        url = f"https://sports.bwin.fr/cds-api/bettingoffer/fixtures?lang=fr-fr&country=FR&offerMapping=Filtered&fixtureCategories=Gridable&fixtureTypes=Standard&sportIds={sport_id}"
        events: List[Event] = []
        data = None

        if HAS_CURL_CFFI:
            try:
                r = cffi_requests.get(url, headers=self.headers, impersonate="chrome120", timeout=self.timeout)
                if r.status_code == 200 and r.text.startswith("{"):
                    data = r.json()
            except Exception as e:
                logger.debug(f"[Bwin] curl_cffi err: {e}")

        if not data:
            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=self.headers) as client:
                    resp = client.get(url)
                    if resp.status_code == 200 and resp.text.startswith("{"):
                        data = resp.json()
            except Exception as e:
                logger.debug(f"[Bwin] httpx err: {e}")

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
                    logger.info(f"[Bwin] {len(events)} matchs charges depuis le cache.")
            except Exception as e:
                logger.debug(f"[Bwin] Erreur lecture cache: {e}")

        return events

    def _save_to_cache(self, data: dict):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _parse_data(self, data: dict, sport: Sport) -> List[Event]:
        events: List[Event] = []
        fixtures = data.get("fixtures", [])

        for fix in fixtures:
            try:
                participants = fix.get("participants", [])
                if len(participants) < 2:
                    continue
                home_team = participants[0].get("name", {}).get("value", "")
                away_team = participants[1].get("name", {}).get("value", "")
                if not home_team or not away_team:
                    continue

                f_id = str(fix.get("id", ""))
                comp = fix.get("competition", {}).get("name", {}).get("value", "")
                match_url = f"https://sports.bwin.fr/fr/sports/evenements/{f_id}"

                outcomes = {}
                for opt in fix.get("optionMarkets", []):
                    for o in opt.get("options", []):
                        val = float(o.get("price", {}).get("odds", 0.0))
                        lbl = o.get("name", {}).get("value", "")
                        if val > 1.0:
                            code = "N" if "nul" in lbl.lower() else ("1" if lbl == home_team else "2")
                            outcomes[code] = Odd(outcome=code, label=lbl, value=round(val, 2), bookmaker=self.name, url=match_url)

                if len(outcomes) >= 2:
                    mkt = "1N2" if "N" in outcomes else "12"
                    events.append(Event(
                        id=f"bwin_{f_id}",
                        sport=sport,
                        home_team=home_team,
                        away_team=away_team,
                        bookmaker=self.name,
                        markets={mkt: Market(name=mkt, outcomes=outcomes)},
                        url=match_url,
                        competition=comp
                    ))
            except Exception:
                continue

        return events
