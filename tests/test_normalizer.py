from bennybets.core.normalizer import clean_text, normalize_team_name, are_teams_matching

def test_clean_text():
    assert clean_text('Saint-Étienne') == 'saint etienne'
    assert clean_text('Paris SG') == 'paris sg'

def test_normalize_aliases():
    assert normalize_team_name('PSG') == 'paris saint germain'
    assert normalize_team_name('Paris SG') == 'paris saint germain'
    assert normalize_team_name('OM') == 'marseille'
    assert normalize_team_name('Olympique de Marseille') == 'marseille'

def test_are_teams_matching():
    assert are_teams_matching('Paris Saint-Germain', 'Paris SG')
    assert are_teams_matching('AS Monaco', 'Monaco')
    assert are_teams_matching('Real Madrid CF', 'Real Madrid')
    assert are_teams_matching('Manchester United', 'Man Utd')
    assert not are_teams_matching('Arsenal', 'Chelsea')