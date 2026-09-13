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
    Sport.FOOTBALL: "https://sport.genybet.fr/football",
    Sport.TENNIS: "https://sport.genybet.fr/tennis",
    Sport.BASKETBALL: "https://sport.genybet.fr/basketball",
}

class GenybetProvider(BaseProvider):
    """Fournisseur de cotes en direct pour Genybet (moteur Sportnco / France-Pari)"""

    def __init__(self, timeout_seconds: float = 12.0):
        self.timeout = timeout_seconds
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.cache_file = os.path.join(CACHE_DIR, "genybet_cache.json")

    @property
    def name(self) -> str:
        return "Genybet"

    def fetch_events(self, sport: Sport = Sport.FOOTBALL) -> List[Event]:
        url = SPORT_URL_MAP.get(sport, "https://sport.genybet.fr/football")
        events: List[Event] = []
        html = None

        # 1. Requête via curl_cffi (impersonate chrome120)
        if HAS_CURL_CFFI:
            try:
                r = cffi_requests.get(url, impersonate="chrome120", timeout=self.timeout)
                if r.status_code == 200:
                    html = r.text
            except Exception as e:
                logger.debug(f"[Genybet] curl_cffi err: {e}")

        # 2. Requête via httpx
        if not html:
            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=self.headers) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        html = resp.text
            except Exception as e:
                logger.debug(f"[Genybet] httpx err: {e}")

        # 3. Requête via urllib
        if not html:
            try:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        html = resp.read().decode("utf-8", errors="ignore")
            except Exception as e:
                logger.debug(f"[Genybet] urllib err: {e}")

        # Parsing
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
                    logger.info(f"[Genybet] {len(events)} matchs charges depuis le cache.")
            except Exception as e:
                logger.debug(f"[Genybet] Erreur lecture cache: {e}")

        return events

    def _save_to_cache(self, html: str):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception:
            pass

    def _parse_html(self, html: str, sport: Sport) -> List[Event]:
        events: List[Event] = []
        
        event_pattern = re.compile(
            r'\{\s*id:\s*(\d+)\s*,'
            r'\s*label:\s*"([^"]+)"\s*,'
            r'\s*url:\s*"([^"]+)"\s*,'
            r'(?:\s*statisticsUrl:[^,]+,)?'
            r'\s*live:\s*([^,]+)\s*,'
            r'\s*becomeLive:[^,]+,'
            r'\s*start:\s*"([^"]+)"\s*,'
            r'.*?'
            r'choices:\s*\{\s*question:\s*\{\s*label:\s*"(?:Qui va gagner le match \?|Vainqueur du match \?|Vainqueur\?)",\s*short_label:\s*"[^"]*"\s*\}\s*,\s*choices:\s*\[(.*?)\]\s*\}',
            re.DOTALL
        )

        for m in event_pattern.finditer(html):
            try:
                ev_id, label, url_part, live_val, start_str, choices_str = m.groups()
                clean_label = label.encode().decode('unicode_escape')

                parts = None
                for sep in [" / ", " - ", " vs "]:
                    if sep in clean_label:
                        p = clean_label.split(sep, 1)
                        parts = (p[0].strip(), p[1].strip())
                        break
                if not parts:
                    continue

                home_team, away_team = parts
                clean_url = "https://sport.genybet.fr" + url_part.encode().decode('unicode_escape')
                is_live = (live_val.strip() not in ("null", "false", "a", "b"))

                try:
                    start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                except Exception:
                    start_time = None

                # Extraction des cotes
                choice_pattern = re.compile(r'odd:\s*([\d\.]+),.*?label:\s*"([^"]+)"')
                choice_matches = choice_pattern.findall(choices_str)

                outcomes = {}
                for odd_str, o_label in choice_matches:
                    val = float(odd_str)
                    if val <= 1.0:
                        continue
                    ol_clean = o_label.encode().decode('unicode_escape').strip()
                    ol_lower = ol_clean.lower()

                    if ol_lower in ("nul", "match nul", "x", "draw"):
                        out_code = "N"
                    elif ol_clean == home_team or home_team in ol_clean:
                        out_code = "1"
                    elif ol_clean == away_team or away_team in ol_clean:
                        out_code = "2"
                    elif len(outcomes) == 0:
                        out_code = "1"
                    elif len(outcomes) == 1 and "N" not in outcomes:
                        out_code = "N"
                    elif len(outcomes) == 2:
                        out_code = "2"
                    else:
                        continue

                    if out_code not in outcomes:
                        outcomes[out_code] = Odd(
                            outcome=out_code,
                            label=ol_clean,
                            value=round(val, 2),
                            bookmaker=self.name,
                            url=clean_url
                        )

                if len(outcomes) >= 2:
                    mkt_name = "1N2" if "N" in outcomes else "12"
                    events.append(Event(
                        id=f"genybet_{ev_id}",
                        sport=sport,
                        home_team=home_team,
                        away_team=away_team,
                        start_time=start_time,
                        is_live=is_live,
                        bookmaker=self.name,
                        markets={mkt_name: Market(name=mkt_name, outcomes=outcomes)},
                        url=clean_url,
                    ))
            except Exception:
                continue

        return events
