import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any

SETTINGS_FILE = 'settings.json'

@dataclass
class CustomSource:
    name: str
    url: str
    sport: str = 'football'
    enabled: bool = True
    description: str = ''

@dataclass
class AppSettings:
    font_size: int = 11                          # Taille de police par défaut
    theme: str = 'dark'                          # 'dark', 'midnight', 'light'
    auto_refresh_interval: int = 30              # Secondes (10, 30, 60, 0 = manuel)
    surebet_min_profit: float = 0.0              # Min ROI pour alerte Surebet (%)
    value_bet_threshold: float = 8.0             # Seuil décalage (%) pour anomalie
    enabled_providers: List[str] = field(default_factory=lambda: ['Winamax', 'Betclic', 'Unibet'])
    custom_sources: List[Dict[str, Any]] = field(default_factory=list)
    default_total_stake: float = 100.0           # Mise par défaut pour calculateur
    show_only_surebets: bool = False
    show_only_live: bool = False
    search_filter: str = ''
    sound_alert_on_surebet: bool = False

    @classmethod
    def load(cls, filepath: str = SETTINGS_FILE) -> 'AppSettings':
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception as e:
                print(f'Erreur chargement {filepath}: {e}, utilisation des valeurs par défaut.')
        settings = cls()
        settings.save(filepath)
        return settings

    def save(self, filepath: str = SETTINGS_FILE) -> None:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f'Erreur sauvegarde {filepath}: {e}')