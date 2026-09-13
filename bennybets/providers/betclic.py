import json
import re
import logging
from typing import List, Optional
from datetime import datetime
import httpx

from bennybets.core.models import Event, Sport, Market, Odd
from bennybets.providers.base import BaseProvider

logger = logging.getLogger(__name__)

SPORT_SLUG_MAP = {
    Sport.FOOTBALL: "football-s1",
    Sport.TENNIS: "tennis-s2",
    Sport.BASKETBALL: "basket-ball-s4",
}

class BetclicProvider(BaseProvider):
    """Fournisseur de cotes en temps réel pour Betclic France"""

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout = timeout_seconds
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        }

    @property
    def name(self) -> str:
        return "Betclic"

    def fetch_events(self, sport: Sport = Sport.FOOTBALL) -> List[Event]:
        slug = SPORT_SLUG_MAP.get(sport, "football-s1")
        url = f"https://www.betclic.fr/{slug}"
        events: List[Event] = []

        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=self.headers) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"[Betclic] Réponse HTTP {resp.status_code}")
                    return events
                html = resp.text

            m = re.search(r'<script\s+id="ng-state"[^>]*>(.*?)</script>', html, re.DOTALL)
            if not m:
                logger.warning("[Betclic] Script ng-state introuvable dans le HTML.")
                return events

            state_data = json.loads(m.group(1).strip())
            
            # Recherche de la liste des matches dans les clés gRPC ou payload
            raw_matches = []
            for k, v in state_data.items():
                if isinstance(v, dict):
                    # Chercher dans v.response.payload.matches ou v.payload.matches ou v.body.matches
                    payload = v.get("response", {}).get("payload", {})
                    if not payload and "payload" in v:
                        payload = v.get("payload", {})
                    if not payload and "b" in v:
                        payload = v.get("b", {})

                    if isinstance(payload, dict) and "matches" in payload:
                        cand = payload.get("matches", [])
                        if isinstance(cand, list) and len(cand) > len(raw_matches):
                            raw_matches = cand

            for m_data in raw_matches:
                try:
                    name = m_data.get("name", "")
                    if " - " in name:
                        parts = name.split(" - ", 1)
                        home_team, away_team = parts[0].strip(), parts[1].strip()
                    elif " / " in name:
                        parts = name.split(" / ", 1)
                        home_team, away_team = parts[0].strip(), parts[1].strip()
                    else:
                        continue

                    match_id = str(m_data.get("matchId", ""))
                    is_live = bool(m_data.get("isLive", False))
                    comp_name = m_data.get("competition", {}).get("name", "")

                    # Date
                    date_str = m_data.get("matchDateUtc")
                    start_time = None
                    if date_str:
                        try:
                            clean_date = date_str.split(".")[0]
                            start_time = datetime.fromisoformat(clean_date)
                        except Exception:
                            pass

                    # Score si live
                    score_str = None
                    if is_live:
                        sc = m_data.get("scoreboard", {})
                        if sc and isinstance(sc, dict):
                            h_s = sc.get("homeScore")
                            a_s = sc.get("awayScore")
                            if h_s is not None and a_s is not None:
                                score_str = f"{h_s} - {a_s}"

                    # Marché principal
                    market = m_data.get("market")
                    if not market or not isinstance(market, dict):
                        continue

                    selections = market.get("mainSelections", [])
                    if not selections:
                        continue

                    market_outcomes = {}
                    # URL match
                    rel_url = m_data.get("relative_desktop_url") or m_data.get("desktopUrl")
                    if rel_url:
                        match_url = f"https://www.betclic.fr{rel_url}" if rel_url.startswith("/") else f"https://www.betclic.fr/{rel_url}"
                    else:
                        match_url = f"https://www.betclic.fr/{slug}"

                    # Traitement des sélections 1, N, 2 ou 1, 2
                    if len(selections) == 3:
                        # [0] = Equipe 1, [1] = Nul, [2] = Equipe 2
                        codes = ["1", "N", "2"]
                        for idx, sel in enumerate(selections):
                            code = codes[idx]
                            odd_val = sel.get("odds")
                            if odd_val and float(odd_val) > 1.0:
                                market_outcomes[code] = Odd(
                                    outcome=code,
                                    label=sel.get("name", code),
                                    value=float(odd_val),
                                    bookmaker=self.name,
                                    url=match_url
                                )
                    elif len(selections) == 2:
                        codes = ["1", "2"]
                        for idx, sel in enumerate(selections):
                            code = codes[idx]
                            odd_val = sel.get("odds")
                            if odd_val and float(odd_val) > 1.0:
                                market_outcomes[code] = Odd(
                                    outcome=code,
                                    label=sel.get("name", code),
                                    value=float(odd_val),
                                    bookmaker=self.name,
                                    url=match_url
                                )

                    if len(market_outcomes) >= 2:
                        market_name = "1N2" if "N" in market_outcomes else "12"
                        event = Event(
                            id=f"betclic_{match_id}",
                            sport=sport,
                            home_team=home_team,
                            away_team=away_team,
                            start_time=start_time,
                            is_live=is_live,
                            bookmaker=self.name,
                            markets={
                                market_name: Market(name=market_name, outcomes=market_outcomes)
                            },
                            url=match_url,
                            competition=comp_name,
                            score=score_str
                        )
                        events.append(event)
                except Exception as ex:
                    logger.debug(f"[Betclic] Erreur parsing match {m_data.get('matchId')}: {ex}")
                    continue

        except Exception as e:
            logger.error(f"[Betclic] Erreur de récupération: {e}")

        return events
