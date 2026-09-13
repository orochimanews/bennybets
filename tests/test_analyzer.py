from bennybets.core.models import Odd, Event, Sport, Market
from bennybets.core.analyzer import compute_surebet, detect_value_bets, aggregate_events

def test_compute_surebet():
    # Exemple de surebet mathématique : 1 à 2.10, N à 4.20, 2 à 4.20
    # 1/2.10 + 1/4.20 + 1/4.20 = 0.476 + 0.238 + 0.238 = 0.952 < 1.0 -> Surebet ~ +5%
    best_odds = {
        '1': Odd(outcome='1', label='Team A', value=2.10, bookmaker='Winamax', url='http://w.fr'),
        'N': Odd(outcome='N', label='Nul', value=4.20, bookmaker='Betclic', url='http://b.fr'),
        '2': Odd(outcome='2', label='Team B', value=4.20, bookmaker='Winamax', url='http://w.fr')
    }
    op = compute_surebet(best_odds, total_stake=100.0)
    assert op is not None
    assert op.profit_margin > 4.0
    assert len(op.stakes) == 3
    # Vérifier que chaque gain garanti est supérieur à la mise totale de 100€
    for s in op.stakes:
        assert s.payout >= 104.0

def test_no_surebet_standard_margin():
    # Cotes classiques avec marge du bookmaker : 1.80, 3.40, 4.50
    # 1/1.80 + 1/3.40 + 1/4.50 = 0.555 + 0.294 + 0.222 = 1.071 > 1.0
    odds = {
        '1': Odd(outcome='1', label='Team A', value=1.80, bookmaker='Winamax', url=''),
        'N': Odd(outcome='N', label='Nul', value=3.40, bookmaker='Betclic', url=''),
        '2': Odd(outcome='2', label='Team B', value=4.50, bookmaker='Winamax', url='')
    }
    op = compute_surebet(odds)
    assert op is None

def test_detect_value_bet_anomaly():
    # Cas où un bookmaker a une cote décalée de 15% par rapport à la médiane
    all_odds = {
        '1': [
            Odd(outcome='1', label='Team A', value=2.00, bookmaker='Winamax', url=''),
            Odd(outcome='1', label='Team A', value=2.05, bookmaker='Betclic', url=''),
            Odd(outcome='1', label='Team A', value=2.45, bookmaker='OutlierBookmaker', url=''),
        ]
    }
    # Médiane = 2.05. Outlier = 2.45. Ecart = (2.45 - 2.05)/2.05 = ~19.5%
    ops = detect_value_bets(all_odds, threshold_percent=10.0)
    assert len(ops) == 1
    assert ops[0].profit_margin > 15.0
    assert ops[0].best_odds['1'].bookmaker == 'OutlierBookmaker'

def test_aggregate_events_multi_bookmakers():
    e1 = Event(
        id='win_1',
        sport=Sport.FOOTBALL,
        home_team='Paris SG',
        away_team='Marseille',
        start_time=None,
        is_live=False,
        bookmaker='Winamax',
        markets={
            '1N2': Market(name='1N2', outcomes={
                '1': Odd(outcome='1', label='PSG', value=1.65, bookmaker='Winamax', url='http://winamax.fr/1'),
                'N': Odd(outcome='N', label='Nul', value=4.00, bookmaker='Winamax', url='http://winamax.fr/1'),
                '2': Odd(outcome='2', label='OM', value=5.50, bookmaker='Winamax', url='http://winamax.fr/1'),
            })
        },
        url='http://winamax.fr/1'
    )
    e2 = Event(
        id='bet_1',
        sport=Sport.FOOTBALL,
        home_team='Paris Saint-Germain',
        away_team='Olympique de Marseille',
        start_time=None,
        is_live=False,
        bookmaker='Betclic',
        markets={
            '1N2': Market(name='1N2', outcomes={
                '1': Odd(outcome='1', label='Paris SG', value=1.70, bookmaker='Betclic', url='http://betclic.fr/1'),
                'N': Odd(outcome='N', label='Nul', value=3.90, bookmaker='Betclic', url='http://betclic.fr/1'),
                '2': Odd(outcome='2', label='Marseille', value=5.80, bookmaker='Betclic', url='http://betclic.fr/1'),
            })
        },
        url='http://betclic.fr/1'
    )
    aggregated = aggregate_events([e1, e2])
    assert len(aggregated) == 1
    agg = aggregated[0]
    assert len(agg.bookmaker_events) == 2
    # Meilleure cote pour 1 doit être 1.70 (Betclic)
    assert agg.best_odds['1N2']['1'].value == 1.70
    assert agg.best_odds['1N2']['1'].bookmaker == 'Betclic'
    # Meilleure cote pour N doit être 4.00 (Winamax)
    assert agg.best_odds['1N2']['N'].value == 4.00
    assert agg.best_odds['1N2']['N'].bookmaker == 'Winamax'
    # Meilleure cote pour 2 doit être 5.80 (Betclic)
    assert agg.best_odds['1N2']['2'].value == 5.80
    assert agg.best_odds['1N2']['2'].bookmaker == 'Betclic'
