import os
import json
import logging
import re
from typing import List, Optional
from datetime import datetime, date

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
    Sport.FOOTBALL: "https://www.pokerstarssports.fr/sports/football",
    Sport.TENNIS: "https://www.pokerstarssports.fr/sports/tennis",
    Sport.BASKETBALL: "https://www.pokerstarssports.fr/sports/basketball",
}

class PokerStarsProvider(BaseProvider):
    """Fournisseur de cotes en temps réel pour PokerStars Sports France"""

    def __init__(self, timeout_seconds: float = 12.0):
        self.timeout = timeout_seconds
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.cache_file = os.path.join(CACHE_DIR, "pokerstars_cache.json")

    @property
    def name(self) -> str:
        return "PokerStars"

    def fetch_events(self, sport: Sport = Sport.FOOTBALL) -> List[Event]:
        url = SPORT_URL_MAP.get(sport, "https://www.pokerstarssports.fr/sports/football")
        events: List[Event] = []
        html = None

        if HAS_CURL_CFFI:
            try:
                r = cffi_requests.get(url, impersonate="chrome120", timeout=self.timeout)
                if r.status_code == 200:
                    html = r.text
            except Exception as e:
                logger.debug(f"[PokerStars] curl_cffi err: {e}")

        if not html:
            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=self.headers) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        html = resp.text
            except Exception as e:
                logger.debug(f"[PokerStars] httpx err: {e}")

        if not html:
            try:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        html = resp.read().decode("utf-8", errors="ignore")
            except Exception as e:
                logger.debug(f"[PokerStars] urllib err: {e}")

        if html:
            events = self._parse_html(html, sport)
            if events:
                self._save_to_cache(html)
                return events

        if not events and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cached_html = f.read()
                    events = self._parse_html(cached_html, sport)
                    logger.info(f"[PokerStars] {len(events)} matchs charges depuis le cache.")
            except Exception as e:
                logger.debug(f"[PokerStars] Erreur lecture cache: {e}")

        return events

    def _save_to_cache(self, html: str):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception:
            pass

    def _parse_html(self, html: str, sport: Sport) -> List[Event]:
        events: List[Event] = []
        raw_events = re.findall(r'<li[^>]*data-testid="event"[^>]*>(.*?)</li>', html, re.DOTALL)

        for ev_html in raw_events:
            try:
                # 1. Lien du match et competition
                link_m = re.search(r'href="([^"]+)"', ev_html)
                if not link_m:
                    continue
                path = link_m.group(1)
                full_url = f"https://www.pokerstarssports.fr{path}" if path.startswith("/") else path
                
                # Extraire competition du slug d'URL
                comp_name = ""
                parts = path.strip("/").split("/")
                if len(parts) >= 4:
                    comp_slug = parts[3]
                    comp_name = comp_slug.replace("-", " ").title()

                # Extraire ID du match
                m_id = parts[-1] if parts else str(hash(path))

                # 2. Participants
                parts_block = re.search(r'data-testid="event-participants"[^>]*>(.*?)</div>', ev_html, re.DOTALL)
                if not parts_block:
                    continue
                p_text = parts_block.group(1)
                # Supprimer le span ' vs '
                clean_p = re.sub(r'<span[^>]*>\s*vs\s*</span>', ' vs ', p_text, flags=re.IGNORECASE)
                clean_p = re.sub(r'<[^>]+>', '', clean_p).strip()
                
                if " vs " not in clean_p:
                    continue
                h_name, a_name = clean_p.split(" vs ", 1)
                home_team = h_name.strip()
                away_team = a_name.strip()
                if not home_team or not away_team:
                    continue

                # 3. Horaires / Date
                time_m = re.search(r'<time[^>]*dateTime="([^"]*)"[^>]*>([^<]*)</time>', ev_html)
                start_time = None
                if time_m:
                    dt_val = time_m.group(1) or time_m.group(2)
                    if ":" in dt_val and len(dt_val) <= 5:
                        # Heure simple HH:MM aujourd'hui
                        try:
                            h, m = map(int, dt_val.split(":"))
                            today = date.today()
                            start_time = datetime(today.year, today.month, today.day, h, m)
                        except Exception:
                            pass
                    else:
                        try:
                            clean_dt = dt_val.replace("Z", "+00:00")
                            start_time = datetime.fromisoformat(clean_dt)
                        except Exception:
                            pass

                # 4. Cotes (1, N, 2)
                odds_raw = re.findall(r'<strong>([0-9]+,[0-9]+)</strong>', ev_html)
                if len(odds_raw) < 2:
                    continue

                outcomes = {}
                # Pour le football standard, 3 boutons : 1, N, 2
                if len(odds_raw) >= 3:
                    o_values = [float(o.replace(",", ".")) for o in odds_raw[:3]]
                    codes = ["1", "N", "2"]
                    labels = [home_team, "Nul", away_team]
                    for code, lbl, val in zip(codes, labels, o_values):
                        if val > 1.0:
                            outcomes[code] = Odd(
                                outcome=code,
                                label=lbl,
                                value=round(val, 2),
                                bookmaker=self.name,
                                url=full_url
                            )
                elif len(odds_raw) == 2:
                    o_values = [float(o.replace(",", ".")) for o in odds_raw[:2]]
                    codes = ["1", "2"]
                    labels = [home_team, away_team]
                    for code, lbl, val in zip(codes, labels, o_values):
                        if val > 1.0:
                            outcomes[code] = Odd(
                                outcome=code,
                                label=lbl,
                                value=round(val, 2),
                                bookmaker=self.name,
                                url=full_url
                            )

                if len(outcomes) >= 2:
                    mkt_name = "1N2" if "N" in outcomes else "12"
                    events.append(Event(
                        id=f"pokerstars_{m_id}",
                        sport=sport,
                        home_team=home_team,
                        away_team=away_team,
                        start_time=start_time,
                        is_live=False,
                        bookmaker=self.name,
                        markets={mkt_name: Market(name=mkt_name, outcomes=outcomes)},
                        url=full_url,
                        competition=comp_name
                    ))
            except Exception:
                continue

        return events
