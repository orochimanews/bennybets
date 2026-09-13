import pytest
from datetime import datetime
from bennybets.core.models import Sport, Event, Market, Odd
from bennybets.providers.genybet import GenybetProvider
from bennybets.providers.pokerstars import PokerStarsProvider
from bennybets.providers.pmu import PmuProvider
from bennybets.providers.bwin import BwinProvider

def test_genybet_provider_initialization():
    p = GenybetProvider()
    assert p.name == "Genybet"
    assert Sport.FOOTBALL in p.supported_sports

def test_pokerstars_provider_initialization():
    p = PokerStarsProvider()
    assert p.name == "PokerStars"
    assert Sport.FOOTBALL in p.supported_sports

def test_pmu_provider_initialization():
    p = PmuProvider()
    assert p.name == "PMU"
    assert Sport.FOOTBALL in p.supported_sports

def test_bwin_provider_initialization():
    p = BwinProvider()
    assert p.name == "Bwin"
    assert Sport.FOOTBALL in p.supported_sports

def test_genybet_parse_sample_html():
    p = GenybetProvider()
    sample_html = '''
    <script>
    window.__NUXT__=(function(){ return {
        state: {
            UFWSClient: {
                components: {
                    top_bets: {
                        data: {
                            events: [
                                {
                                    id: 999001,
                                    label: "Marseille / Lyon",
                                    url: "/evenement/999001-marseille-lyon",
                                    live: null,
                                    becomeLive: false,
                                    start: "2026-09-15T21:00:00.000+02:00",
                                    choices: {
                                        question: { label: "Qui va gagner le match ?", short_label: "1N2" },
                                        choices: [
                                            { id: 1, odd: 2.10, actor: { label: "Marseille" } },
                                            { id: 2, odd: 3.40, actor: { label: "Nul" } },
                                            { id: 3, odd: 3.20, actor: { label: "Lyon" } }
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
    }; })();
    </script>
    '''
    events = p._parse_html(sample_html, Sport.FOOTBALL)
    assert len(events) == 1
    ev = events[0]
    assert ev.home_team == "Marseille"
    assert ev.away_team == "Lyon"
    assert "1N2" in ev.markets
    m = ev.markets["1N2"]
    assert m.outcomes["1"].value == 2.10
    assert m.outcomes["N"].value == 3.40
    assert m.outcomes["2"].value == 3.20
    assert "evenement/999001-marseille-lyon" in ev.url

def test_pokerstars_parse_sample_html():
    p = PokerStarsProvider()
    sample_html = '''
    <li data-testid="event">
        <div class="_43626d7">
            <div class="_1711781">
                <a href="/sports/football/1/ligue-1/55/psg-monaco/36009999/">
                    <div data-testid="event-participants">
                        <span>Paris SG<span> vs </span></span>
                        <span>Monaco</span>
                    </div>
                </a>
            </div>
            <div>
                <button data-testid="selection"><strong>1,55</strong></button>
                <button data-testid="selection"><strong>4,20</strong></button>
                <button data-testid="selection"><strong>5,80</strong></button>
            </div>
            <div>
                <time dateTime="20:45">20:45</time>
            </div>
        </div>
    </li>
    '''
    events = p._parse_html(sample_html, Sport.FOOTBALL)
    assert len(events) == 1
    ev = events[0]
    assert ev.home_team == "Paris SG"
    assert ev.away_team == "Monaco"
    assert "1N2" in ev.markets
    m = ev.markets["1N2"]
    assert m.outcomes["1"].value == 1.55
    assert m.outcomes["N"].value == 4.20
    assert m.outcomes["2"].value == 5.80
    assert "psg-monaco" in ev.url
