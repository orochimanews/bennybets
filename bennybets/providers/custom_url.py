import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx

from bennybets.core.models import Event, Sport, Market, Odd
from bennybets.providers.base import BaseProvider

logger = logging.getLogger(__name__)

class CustomJsonProvider(BaseProvider):
    """
    Fournisseur configurable permettant d'ajouter dynamiquement n'importe quelle source
    (URL d'API JSON, webhook, ou fichier local) d'événements et de cotes.
    """

    def __init__(self, name: str, source_url: str, sport: Sport = Sport.FOOTBALL, timeout_seconds: float = 8.0):
        self._name = name
        self.source_url = source_url
        self._sport = sport
        self.timeout = timeout_seconds

    @property
    def name(self) -> str:
        return self._name

    def fetch_events(self, sport: Sport = Sport.FOOTBALL) -> List[Event]:
        events: List[Event] = []
        if not self.source_url:
            return events

        try:
            # Si c'est un fichier local
            if self.source_url.startswith("file://") or self.source_url.endswith(".json") and "://" not in self.source_url:
                local_path = self.source_url.replace("file://", "")
                with open(local_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                    resp = client.get(self.source_url)
                    if resp.status_code != 200:
                        logger.warning(f"[{self.name}] Code réponse HTTP {resp.status_code}")
                        return events
                    data = resp.json()

            items = data if isinstance(data, list) else data.get("events", data.get("matches", []))

            for idx, item in enumerate(items):
                try:
                    home = item.get("home_team") or item.get("home") or item.get("team1")
                    away = item.get("away_team") or item.get("away") or item.get("team2")
                    if not home or not away:
                        continue

                    odds_data = item.get("odds", {})
                    market_outcomes = {}
                    item_url = item.get("url") or self.source_url

                    for code, val in odds_data.items():
                        norm_code = str(code).upper()
                        if norm_code in ("X", "DRAW", "NUL"):
                            norm_code = "N"
                        market_outcomes[norm_code] = Odd(
                            outcome=norm_code,
                            label=home if norm_code == "1" else (away if norm_code == "2" else "Nul"),
                            value=float(val),
                            bookmaker=self.name,
                            url=item_url
                        )

                    if len(market_outcomes) >= 2:
                        market_name = "1N2" if "N" in market_outcomes else "12"
                        ev = Event(
                            id=f"{self.name.lower()}_{idx}_{item.get('id', '')}",
                            sport=sport,
                            home_team=home,
                            away_team=away,
                            start_time=None,
                            is_live=bool(item.get("is_live", False)),
                            bookmaker=self.name,
                            markets={market_name: Market(name=market_name, outcomes=market_outcomes)},
                            url=item_url,
                            competition=item.get("competition", "")
                        )
                        events.append(ev)
                except Exception as ie:
                    logger.debug(f"[{self.name}] Erreur item: {ie}")
                    continue

        except Exception as e:
            logger.error(f"[{self.name}] Erreur lors de la récupération: {e}")

        return events
