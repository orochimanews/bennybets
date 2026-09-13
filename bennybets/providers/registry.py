import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from bennybets.core.models import Event, Sport
from bennybets.core.settings import AppSettings
from bennybets.providers.base import BaseProvider
from bennybets.providers.winamax import WinamaxProvider
from bennybets.providers.betclic import BetclicProvider
from bennybets.providers.custom_url import CustomJsonProvider

logger = logging.getLogger(__name__)

class ProviderRegistry:
    """Gestionnaire et orchestrateur de tous les fournisseurs de cotes"""

    def __init__(self, settings: Optional[AppSettings] = None):
        self.settings = settings or AppSettings.load()
        self.providers: Dict[str, BaseProvider] = {}
        self._init_default_providers()
        self._load_custom_providers()

    def _init_default_providers(self):
        w = WinamaxProvider()
        b = BetclicProvider()
        self.providers[w.name] = w
        self.providers[b.name] = b

    def _load_custom_providers(self):
        for src in self.settings.custom_sources:
            if src.get("enabled", True):
                name = src.get("name", "Source Personnalisée")
                url = src.get("url", "")
                sport_name = src.get("sport", "football")
                sport_enum = Sport.FOOTBALL
                try:
                    sport_enum = Sport(sport_name)
                except Exception:
                    pass
                if url:
                    self.providers[name] = CustomJsonProvider(name=name, source_url=url, sport=sport_enum)

    def register(self, provider: BaseProvider):
        self.providers[provider.name] = provider

    def fetch_all(self, sport: Sport = Sport.FOOTBALL) -> List[Event]:
        """Récupère les événements en parallèle depuis tous les providers actifs"""
        all_events: List[Event] = []
        enabled = self.settings.enabled_providers

        active_providers = [
            p for name, p in self.providers.items()
            if name in enabled or not enabled
        ]

        if not active_providers:
            active_providers = list(self.providers.values())

        with ThreadPoolExecutor(max_workers=max(1, len(active_providers))) as executor:
            future_to_provider = {
                executor.submit(p.fetch_events, sport): p.name
                for p in active_providers
            }
            for future in as_completed(future_to_provider):
                p_name = future_to_provider[future]
                try:
                    events = future.result()
                    logger.info(f"[{p_name}] {len(events)} événements récupérés avec succès.")
                    all_events.extend(events)
                except Exception as e:
                    logger.error(f"[{p_name}] Échec de récupération: {e}")

        return all_events
