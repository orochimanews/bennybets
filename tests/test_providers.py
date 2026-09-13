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
