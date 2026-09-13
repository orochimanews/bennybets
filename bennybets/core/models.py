from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime

class Sport(str, Enum):
    FOOTBALL = 'football'
    TENNIS = 'tennis'
    BASKETBALL = 'basketball'
    RUGBY = 'rugby'
    OTHER = 'other'

class OpportunityType(str, Enum):
    SUREBET = 'surebet'          # Arbitrage strict avec ROI garanti > 0
    VALUE_BET = 'value_bet'      # Décalage significatif par rapport à la médiane
    HIGH_SPREAD = 'high_spread'  # Écart important entre les cotes proposées

@dataclass
class Odd:
    outcome: str                 # '1', 'N', '2' ou 'Over', 'Under', etc.
    label: str                   # Nom d\'affichage (ex: 'Paris SG', 'Match Nul')
    value: float                 # Cote décimale (ex: 2.15)
    bookmaker: str               # 'Winamax', 'Betclic', etc.
    url: str                     # Lien direct vers le match/marché
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

@dataclass
class Market:
    name: str                    # '1N2', 'Over/Under', etc.
    outcomes: Dict[str, Odd] = field(default_factory=dict) # outcome_key -> Odd

@dataclass
class Event:
    id: str                      # ID unique côté bookmaker
    sport: Sport
    home_team: str
    away_team: str
    start_time: Optional[datetime]
    is_live: bool
    bookmaker: str
    markets: Dict[str, Market] = field(default_factory=dict) # market_name -> Market
    url: str = ''
    competition: str = ''
    score: Optional[str] = None  # ex: '2 - 1' si live

    @property
    def title(self) -> str:
        return f'{self.home_team} vs {self.away_team}'

@dataclass
class StakeRecommendation:
    outcome: str
    bookmaker: str
    odd_value: float
    stake_amount: float
    payout: float
    url: str

@dataclass
class Opportunity:
    op_type: OpportunityType
    market_name: str
    profit_margin: float         # En pourcentage (ex: +3.4% ou +12.5%)
    best_odds: Dict[str, Odd]    # outcome -> Odd
    description: str
    stakes: List[StakeRecommendation] = field(default_factory=list)

@dataclass
class AggregatedEvent:
    id: str                      # Clé d\'agrégation unifiée (ex: 'football:psg_om_20260913')
    sport: Sport
    home_team: str
    away_team: str
    start_time: Optional[datetime]
    is_live: bool
    competition: str
    score: Optional[str] = None
    bookmaker_events: Dict[str, Event] = field(default_factory=dict) # bookmaker_name -> Event
    best_odds: Dict[str, Dict[str, Odd]] = field(default_factory=dict) # market_name -> {outcome -> Odd}
    opportunities: List[Opportunity] = field(default_factory=list)

    @property
    def title(self) -> str:
        return f'{self.home_team} vs {self.away_team}'

    @property
    def has_surebet(self) -> bool:
        return any(op.op_type == OpportunityType.SUREBET for op in self.opportunities)

    @property
    def has_value_bet(self) -> bool:
        return any(op.op_type == OpportunityType.VALUE_BET for op in self.opportunities)

    @property
    def max_profit_margin(self) -> float:
        if not self.opportunities:
            return 0.0
        return max(op.profit_margin for op in self.opportunities)