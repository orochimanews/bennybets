import logging
from typing import List, Optional
from PyQt6.QtCore import QThread, pyqtSignal

from bennybets.core.models import AggregatedEvent, Sport
from bennybets.core.settings import AppSettings
from bennybets.core.analyzer import aggregate_events
from bennybets.providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)

class OddsFetchWorker(QThread):
    """Thread d'arrière-plan pour le scraping et l'agrégation des cotes en direct"""

    data_loaded = pyqtSignal(list)       # List[AggregatedEvent]
    status_message = pyqtSignal(str)     # Info statut pour la StatusBar
    error_message = pyqtSignal(str)      # Message d'erreur si incident

    def __init__(self, sport: Sport, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.sport = sport
        self.settings = settings
        self._is_running = True

    def run(self):
        try:
            self.status_message.emit(f"Récupération des cotes réelles ({self.sport.value.capitalize()})...")
            registry = ProviderRegistry(self.settings)
            
            raw_events = registry.fetch_all(sport=self.sport)
            
            self.status_message.emit(f"{len(raw_events)} événements bruts collectés. Analyse des opportunités...")
            
            aggregated = aggregate_events(
                events=raw_events,
                value_bet_threshold=self.settings.value_bet_threshold,
                min_surebet_profit=self.settings.surebet_min_profit,
                total_stake=self.settings.default_total_stake
            )
            
            self.data_loaded.emit(aggregated)
            self.status_message.emit(f"{len(aggregated)} matchs analysés avec succès.")
        except Exception as e:
            logger.exception("Erreur lors de la récupération des cotes")
            self.error_message.emit(f"Erreur : {str(e)}")
