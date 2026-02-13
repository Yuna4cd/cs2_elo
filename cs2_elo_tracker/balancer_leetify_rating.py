from typing import List, Dict, Tuple, Optional, Any
from itertools import combinations
from pathlib import Path
from leetify_crawler import fetch_leetify_rating_by_leetify_id
from utils import load_json, save_json, DATA_DIR


def load_ratings(filepath: Path = None) -> Dict[str, Dict[str, float]]:
    """Load Leetify id from file"""
    if filepath is None:
        filepath = DATA_DIR / "leetify_ids.json"
    
    data = load_json(filepath, [])
    return {
        name: fetch_leetify_rating_by_leetify_id(leetify_id)
        for name, leetify_id in data.items()
    }

def calculate_team_balance(
    team1: List[str], 
    team2: List[str], 
    ratings: Dict[str, Dict[str, float]],
    rating_key: str = "aim"
) -> Tuple[float, float, float]:
    """Calculate team balance metrics based on specific rating key"""
    team1_rating = sum(ratings.get(p, {}).get(rating_key, 0) for p in team1) / len(team1)
    team2_rating = sum(ratings.get(p, {}).get(rating_key, 0) for p in team2) / len(team2)
    difference = abs(team1_rating - team2_rating)
    return team1_rating, team2_rating, difference

def balance_teams(
    players: List[str], 
    ratings: Dict[str, Dict[str, float]], 
    team_size: int = 5,
    rating_key: str = "aim"
) -> List[Tuple[List[str], List[str], float, float, float]]:
    """Find balanced team configurations based on specific rating key"""
    if len(players) != team_size * 2:
        raise ValueError(f"Need exactly {team_size * 2} players, got {len(players)}")
    
    all_combinations = []
    seen_matchups = set()
    
    for team1 in combinations(players, team_size):
        team1 = list(team1)
        team2 = [p for p in players if p not in team1]
        
        matchup_key = tuple(sorted([tuple(sorted(team1)), tuple(sorted(team2))]))
        
        if matchup_key in seen_matchups:
            continue
        seen_matchups.add(matchup_key)
        
        team1_rating, team2_rating, diff = calculate_team_balance(team1, team2, ratings, rating_key)
        all_combinations.append((team1, team2, diff, team1_rating, team2_rating))
    
    all_combinations.sort(key=lambda x: x[2])
    
    return all_combinations


if __name__ == "__main__":
    leetify_ids_path = DATA_DIR / "leetify_ids.json"
    ratings = load_ratings(leetify_ids_path)
    print(ratings)
    
    players = list(ratings.keys())
    
    balanced_teams = balance_teams(players, ratings, rating_key="aim")
    
    for team1, team2, diff, team1_rating, team2_rating in balanced_teams[:5]:
        print(f"Team 1: {team1} (Avg Aim: {team1_rating:.2f})")
        print(f"Team 2: {team2} (Avg Aim: {team2_rating:.2f})")
        print(f"Difference in Avg Aim: {diff:.2f}\n")

    
