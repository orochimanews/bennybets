import abc
from typing import List
from bennybets.core.models import Event, Sport

class BaseProvider(abc.ABC):
    """Interface de base pour tous les providers de cotes (Winamax, Betclic, etc.)"""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Nom unique du bookmaker"""
        pass

    @property
    def supported_sports(self) -> List[Sport]:
        """Liste des sports supportés"""
        return [Sport.FOOTBALL, Sport.TENNIS, Sport.BASKETBALL]

    @abc.abstractmethod
    def fetch_events(self, sport: Sport = Sport.FOOTBALL) -> List[Event]:
        """Récupère et parse les événements et cotes réelles pour le sport donné"""
        pass
