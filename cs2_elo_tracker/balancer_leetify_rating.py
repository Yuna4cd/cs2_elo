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
    # leetify_ids_path = DATA_DIR / "leetify_ids.json"
    # ratings = load_ratings(leetify_ids_path)
    # print(ratings)

    ratings = {'nanase': {'aim': 65.1732, 'positioning': 45.6205, 'utility': 43.5168, 'clutch': 0.0942, 'opening': -0.0376, 'ct_leetify': -0.0123, 't_leetify': -0.0115}, '901': {'aim': 41.6834, 'positioning': 54.7758, 'utility': 43.7122, 'clutch': 0.0978, 'opening': -0.0085, 'ct_leetify': -0.006, 't_leetify': -0.0206}, 'a1': {'aim': 56.3559, 'positioning': 47.2097, 'utility': 42.1476, 'clutch': 0.0985, 'opening': -0.002, 'ct_leetify': 0.0002, 't_leetify': -0.0008}, '炒饭': {'aim': 88.493, 'positioning': 61.7911, 'utility': 42.078, 'clutch': 0.1133, 'opening': 0.0284, 'ct_leetify': 0.0051, 't_leetify': 0.02}, '龟哥': {'aim': 42.4655, 'positioning': 37.07, 'utility': 21.0866, 'clutch': 0.0607, 'opening': -0.0526, 'ct_leetify': -0.0262, 't_leetify': -0.0237}, '色魔': {'aim': 59.8706, 'positioning': 49.6011, 'utility': 37.1807, 'clutch': 0.1096, 'opening': -0.0056, 'ct_leetify': 0, 't_leetify': 0.0215}, 'steven': {'aim': 50, 'positioning': 62.5516, 'utility': 42.4634, 'clutch': 0.0775, 'opening': 0.0077, 'ct_leetify': -0.0061, 't_leetify': 0.0151}, 'rbc': {'aim': 62.5516, 'positioning': 39.7432, 'utility': 61.4688, 'clutch': 0.0737, 'opening': -0.0332, 'ct_leetify': -0.0282, 't_leetify': -0.0136}, 'guaaaaa': {'aim': 79.6731, 'positioning': 57.1424, 'utility': 59.3607, 'clutch': 0.1169, 'opening': -0.0073, 'ct_leetify': 0.0147, 't_leetify': 0.0082}, 'db': {'aim': 75.8036, 'positioning': 64.8027, 'utility': 48.5725, 'clutch': 0.1201, 'opening': 0.0214, 'ct_leetify': 0.022, 't_leetify': 0.0268}}
    
    players = list(ratings.keys())
    
    balanced_teams = balance_teams(players, ratings, rating_key="aim")
    
    for team1, team2, diff, team1_rating, team2_rating in balanced_teams[:5]:
        print(f"Team 1: {team1} (Avg Aim: {team1_rating:.2f})")
        print(f"Team 2: {team2} (Avg Aim: {team2_rating:.2f})")
        print(f"Difference in Avg Aim: {diff:.2f}\n")
    