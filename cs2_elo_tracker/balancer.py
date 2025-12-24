from typing import List, Dict, Tuple
from itertools import combinations
from pathlib import Path

from .utils import DATA_DIR, load_json, save_json, load_aliases, normalize_name

def load_elos(filepath: Path = None) -> Dict[str, float]:
    """Load ELO ratings from file"""
    if filepath is None:
        filepath = DATA_DIR / "player_elos.json"
    
    data = load_json(filepath, [])
    return {player['name']: player['elo'] for player in data}

def calculate_team_balance(
    team1: List[str], 
    team2: List[str], 
    elos: Dict[str, float]
) -> Tuple[float, float, float]:
    """Calculate team balance metrics"""
    team1_elo = sum(elos.get(p, 1000) for p in team1) / len(team1)
    team2_elo = sum(elos.get(p, 1000) for p in team2) / len(team2)
    difference = abs(team1_elo - team2_elo)
    return team1_elo, team2_elo, difference

def balance_teams(
    players: List[str], 
    elos: Dict[str, float], 
    team_size: int = 5
) -> List[Tuple[List[str], List[str], float, float, float]]:
    """Find balanced team configurations"""
    if len(players) != team_size * 2:
        raise ValueError(f"Need exactly {team_size * 2} players, got {len(players)}")
    
    player_elos = {p: elos.get(p, 1000) for p in players}
    
    all_combinations = []
    seen_matchups = set()
    
    for team1 in combinations(players, team_size):
        team1 = list(team1)
        team2 = [p for p in players if p not in team1]
        
        matchup_key = tuple(sorted([tuple(sorted(team1)), tuple(sorted(team2))]))
        
        if matchup_key in seen_matchups:
            continue
        seen_matchups.add(matchup_key)
        
        team1_elo, team2_elo, diff = calculate_team_balance(team1, team2, player_elos)
        all_combinations.append((team1, team2, diff, team1_elo, team2_elo))
    
    all_combinations.sort(key=lambda x: x[2])
    
    return all_combinations

def get_balanced_teams(
    player_names: List[str],
    elo_file: str = None,
    alias_file: str = None,
    num_results: int = 5
) -> List[Dict]:
    """Get balanced team configurations for given players"""
    
    # Load data
    aliases = load_aliases(Path(alias_file) if alias_file else None)
    elos = load_elos(Path(elo_file) if elo_file else None)
    
    # Normalize names
    normalized = [normalize_name(name, aliases) for name in player_names]
    
    # Get configurations
    configs = balance_teams(normalized, elos)
    
    results = []
    for i, (team1, team2, diff, t1_elo, t2_elo) in enumerate(configs[:num_results]):
        # Sort by ELO within teams
        team1_sorted = sorted(team1, key=lambda p: elos.get(p, 1000), reverse=True)
        team2_sorted = sorted(team2, key=lambda p: elos.get(p, 1000), reverse=True)
        
        results.append({
            'rank': i + 1,
            'team1': team1_sorted,
            'team2': team2_sorted,
            'team1_avg_elo': round(t1_elo, 2),
            'team2_avg_elo': round(t2_elo, 2),
            'elo_difference': round(diff, 2),
            'team1_elos': {p: round(elos.get(p, 1000), 2) for p in team1_sorted},
            'team2_elos': {p: round(elos.get(p, 1000), 2) for p in team2_sorted}
        })
    
    # Save best config
    if results:
        save_json(DATA_DIR / "balanced_teams.json", results[0])
    
    return results