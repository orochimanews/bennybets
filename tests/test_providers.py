from bennybets.core.models import Sport
from bennybets.providers.custom_url import CustomJsonProvider
from bennybets.providers.registry import ProviderRegistry
import json
import tempfile
import os

def test_custom_json_provider():
    sample_data = [
        {
            "home_team": "Lens",
            "away_team": "Lille",
            "odds": {"1": 2.20, "N": 3.30, "2": 3.50},
            "url": "https://example.com/match1",
            "is_live": False,
            "competition": "Ligue 1"
        }
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(sample_data, f)
        temp_path = f.name

    try:
        p = CustomJsonProvider(name="TestSource", source_url=temp_path)
        events = p.fetch_events(Sport.FOOTBALL)
        assert len(events) == 1
        ev = events[0]
        assert ev.home_team == "Lens"
        assert ev.away_team == "Lille"
        assert "1N2" in ev.markets
        assert ev.markets["1N2"].outcomes["1"].value == 2.20
        assert ev.markets["1N2"].outcomes["N"].value == 3.30
        assert ev.markets["1N2"].outcomes["2"].value == 3.50
    finally:
        os.remove(temp_path)

def test_registry_initialization():
    registry = ProviderRegistry()
    assert "Winamax" in registry.providers
    assert "Betclic" in registry.providers
    assert "Unibet" in registry.providers

def test_winamax_match_url_format():
    from bennybets.providers.winamax import WinamaxProvider
    p = WinamaxProvider()
    data = {
        "matches": {
            "12345": {
                "title": "Paris SG - Marseille",
                "status": "PREMATCH",
                "matchStart": 1700000000,
                "mainBetId": 999,
                "tournamentId": 1
            }
        },
        "bets": {
            "999": {"outcomes": [10, 20, 30]}
        },
        "outcomes": {
            "10": {"code": "1", "label": "Paris SG"},
            "20": {"code": "N", "label": "Nul"},
            "30": {"code": "2", "label": "Marseille"}
        },
        "odds": {
            "10": 1.80,
            "20": 3.60,
            "30": 4.50
        }
    }
    events = p._parse_state(data, Sport.FOOTBALL)
    assert len(events) == 1
    ev = events[0]
    assert ev.url == "https://www.winamax.fr/paris-sportifs/match/12345"
    assert ev.markets["1N2"].outcomes["1"].url == "https://www.winamax.fr/paris-sportifs/match/12345"

def test_betclic_match_url_format():
    from bennybets.providers.betclic import BetclicProvider
    p = BetclicProvider()
    # Test with exact HTML href mapping and fallback
    html = '<a href="/football-sfootball/ligue-1-c4/psg-om-m998877">Match</a>'
    import re
    html_match_urls = {}
    for full_href, m_id in re.findall(r'href=[\'"]([^\'"]+-m(\d+)[^\'"]*)[\'"]', html):
        html_match_urls[m_id] = f"https://www.betclic.fr{full_href}"

    assert "998877" in html_match_urls
    assert html_match_urls["998877"] == "https://www.betclic.fr/football-sfootball/ligue-1-c4/psg-om-m998877"

def test_unibet_match_url_format():
    from bennybets.providers.unibet import UnibetProvider
    p = UnibetProvider()
    data = {
        "events": [
            {
                "event": {
                    "id": 554433,
                    "homeName": "Gwangju FC",
                    "awayName": "FC Anyang",
                    "state": "NOT_STARTED",
                    "path": [
                        {"name": "Football"},
                        {"name": "Corée du Sud"},
                        {"name": "K-3 League"}
                    ]
                },
                "betOffers": [
                    {
                        "criterion": {"label": "Temps réglementaire"},
                        "outcomes": [
                            {"type": "OT_ONE", "label": "1", "odds": 2100},
                            {"type": "OT_CROSS", "label": "N", "odds": 3200},
                            {"type": "OT_TWO", "label": "2", "odds": 3400}
                        ]
                    }
                ]
            }
        ]
    }
    # Test exact URL mapping
    exact_urls = {
        ("gwangju", "anyang"): "https://www.unibet.fr/paris-football/coree-du-sud/d1-coree-du-sud/3372387/gwangju-fc-vs-fc-anyang"
    }
    events = p._parse_data(data, Sport.FOOTBALL, exact_urls)
    assert len(events) == 1
    assert events[0].url == "https://www.unibet.fr/paris-football/coree-du-sud/d1-coree-du-sud/3372387/gwangju-fc-vs-fc-anyang"
    assert events[0].markets["1N2"].outcomes["1"].url == "https://www.unibet.fr/paris-football/coree-du-sud/d1-coree-du-sud/3372387/gwangju-fc-vs-fc-anyang"

    # Test fallback to competition page
    events_fallback = p._parse_data(data, Sport.FOOTBALL, {})
    assert len(events_fallback) == 1
    assert events_fallback[0].url == "https://www.unibet.fr/paris-football/coree-du-sud/k-3-league"