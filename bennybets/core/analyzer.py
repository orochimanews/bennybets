from typing import List, Dict, Optional, Tuple
import statistics
from bennybets.core.models import (
    Event, AggregatedEvent, Market, Odd, Opportunity, OpportunityType,
    StakeRecommendation, Sport
)
from bennybets.core.normalizer import are_teams_matching, generate_match_key

def compute_surebet(best_odds: Dict[str, Odd], total_stake: float = 100.0) -> Optional[Opportunity]:
    # Vérifier que nous avons les issues requises (ex: '1', 'N', '2' ou '1', '2')
    required_3 = {'1', 'N', '2'}
    required_2 = {'1', '2'}
    
    outcomes = set(best_odds.keys())
    active_keys = []
    if required_3.issubset(outcomes):
        active_keys = ['1', 'N', '2']
    elif required_2.issubset(outcomes):
        active_keys = ['1', '2']
    else:
        return None

    # Somme des inverses
    try:
        inv_sum = sum(1.0 / best_odds[k].value for k in active_keys if best_odds[k].value > 1.0)
    except ZeroDivisionError:
        return None

    if inv_sum <= 0:
        return None

    # Si la somme des inverses est inférieure à 1.0, c\'est un surebet !
    roi_percent = (1.0 / inv_sum - 1.0) * 100.0
    
    if inv_sum < 1.0:
        # Calcul des mises recommandées
        stakes = []
        for k in active_keys:
            odd = best_odds[k]
            stake = round(total_stake / (inv_sum * odd.value), 2)
            payout = round(stake * odd.value, 2)
            stakes.append(StakeRecommendation(
                outcome=k,
                bookmaker=odd.bookmaker,
                odd_value=odd.value,
                stake_amount=stake,
                payout=payout,
                url=odd.url
            ))
        
        desc = f'Surebet garanti ! ROI de +{roi_percent:.2f}% (Somme inverses: {inv_sum:.4f})'
        return Opportunity(
            op_type=OpportunityType.SUREBET,
            market_name='1N2' if len(active_keys) == 3 else '12',
            profit_margin=round(roi_percent, 2),
            best_odds={k: best_odds[k] for k in active_keys},
            description=desc,
            stakes=stakes
        )
    return None

def detect_value_bets(
    all_odds_by_outcome: Dict[str, List[Odd]],
    threshold_percent: float = 8.0
) -> List[Opportunity]:
    opportunities = []
    
    for outcome, odds_list in all_odds_by_outcome.items():
        if len(odds_list) < 2:
            continue
        values = [o.value for o in odds_list if o.value > 1.0]
        if len(values) < 2:
            continue
        
        median_val = statistics.median(values)
        max_odd = max(odds_list, key=lambda o: o.value)
        
        spread_percent = ((max_odd.value - median_val) / median_val) * 100.0
        if spread_percent >= threshold_percent:
            desc = (
                f'Gros décalage de cote sur {outcome} ({max_odd.label}) : '
                f'{max_odd.bookmaker} offre {max_odd.value:.2f} '
                f'vs médiane marché {median_val:.2f} (+{spread_percent:.1f}%)'
            )
            opportunities.append(Opportunity(
                op_type=OpportunityType.VALUE_BET,
                market_name='1N2',
                profit_margin=round(spread_percent, 2),
                best_odds={outcome: max_odd},
                description=desc,
                stakes=[]
            ))
    return opportunities

def aggregate_events(
    events: List[Event],
    value_bet_threshold: float = 8.0,
    min_surebet_profit: float = 0.0,
    total_stake: float = 100.0
) -> List[AggregatedEvent]:
    aggregated_map: Dict[str, AggregatedEvent] = {}
    
    for event in events:
        matched_agg_id: Optional[str] = None
        
        # Chercher une correspondance existante
        for agg_id, agg_event in aggregated_map.items():
            if agg_event.sport != event.sport:
                continue
            if are_teams_matching(agg_event.home_team, event.home_team) and                are_teams_matching(agg_event.away_team, event.away_team):
                matched_agg_id = agg_id
                break
            # Vérifier inversion home/away au cas où
            if are_teams_matching(agg_event.home_team, event.away_team) and                are_teams_matching(agg_event.away_team, event.home_team):
                matched_agg_id = agg_id
                break
        
        if not matched_agg_id:
            matched_agg_id = generate_match_key(event.home_team, event.away_team, str(event.sport))
            aggregated_map[matched_agg_id] = AggregatedEvent(
                id=matched_agg_id,
                sport=event.sport,
                home_team=event.home_team,
                away_team=event.away_team,
                start_time=event.start_time,
                is_live=event.is_live,
                competition=event.competition,
                score=event.score,
                bookmaker_events={}
            )
        
        agg = aggregated_map[matched_agg_id]
        agg.bookmaker_events[event.bookmaker] = event
        if event.is_live:
            agg.is_live = True
        if event.score:
            agg.score = event.score
        if not agg.competition and event.competition:
            agg.competition = event.competition

    # Pour chaque événement agrégé, calculer les meilleures cotes et opportunités
    for agg in aggregated_map.values():
        agg.best_odds = {}
        agg.opportunities = []
        
        # Consolider les marchés (notamment '1N2')
        # Regrouper les cotes de chaque issue par marché
        market_odds: Dict[str, Dict[str, List[Odd]]] = {} # market_name -> outcome -> [Odd]
        
        for bk_name, bk_event in agg.bookmaker_events.items():
            for mkt_name, mkt in bk_event.markets.items():
                if mkt_name not in market_odds:
                    market_odds[mkt_name] = {}
                for out_code, odd in mkt.outcomes.items():
                    if out_code not in market_odds[mkt_name]:
                        market_odds[mkt_name][out_code] = []
                    market_odds[mkt_name][out_code].append(odd)

        # Calculer les best_odds pour chaque marché
        for mkt_name, outcomes_dict in market_odds.items():
            agg.best_odds[mkt_name] = {}
            for out_code, odds_list in outcomes_dict.items():
                if odds_list:
                    best = max(odds_list, key=lambda o: o.value)
                    agg.best_odds[mkt_name][out_code] = best
            
            # Vérifier Surebet
            surebet_op = compute_surebet(agg.best_odds[mkt_name], total_stake=total_stake)
            if surebet_op and surebet_op.profit_margin >= min_surebet_profit:
                agg.opportunities.append(surebet_op)
            
            # Vérifier Value bets / Décalages
            val_ops = detect_value_bets(outcomes_dict, threshold_percent=value_bet_threshold)
            agg.opportunities.extend(val_ops)

    # Trier : d\'abord les live, puis ceux avec opportunités (plus fort profit d\'abord), puis par nom
    results = list(aggregated_map.values())
    results.sort(
        key=lambda a: (
            1 if a.is_live else 0,
            1 if a.has_surebet else 0,
            a.max_profit_margin,
            len(a.bookmaker_events)
        ),
        reverse=True
    )
    return results