import math
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .utils import (
    DATA_DIR, load_json, save_json, load_jsonl, 
    load_aliases, normalize_name
)
from .parser import parse_date

class EloSystem:
    def __init__(self, k_factor=32, initial_elo=1000, custom_initial_elos=None):
        self.k_factor = k_factor
        self.initial_elo = initial_elo
        self.custom_initial_elos = custom_initial_elos or {}
        self.player_elos = defaultdict(lambda: {
            'elo': initial_elo, 'games': 0, 'wins': 0, 'losses': 0
        })
    
    def get_initial_elo(self, player_name: str) -> float:
        return self.custom_initial_elos.get(player_name, self.initial_elo)
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))
    
    def update_elo(self, player_elo: float, expected: float, actual: float) -> float:
        return player_elo + self.k_factor * (actual - expected)
    
    def process_match(self, match: Dict[str, Any]):
        team1_players = match.get('team1_players', [])
        team2_players = match.get('team2_players', [])
        winning_team = match.get('winning_team', 0)
        
        if not team1_players or not team2_players or winning_team == 0:
            return
        
        # Initialize players
        for player in team1_players + team2_players:
            name = player['name']
            if name not in self.player_elos:
                initial = self.get_initial_elo(name)
                self.player_elos[name] = {
                    'elo': initial,
                    'games': 0,
                    'wins': 0,
                    'losses': 0,
                    'initial_elo': initial
                }
        
        # Calculate team averages
        team1_avg = sum(self.player_elos[p['name']]['elo'] for p in team1_players) / len(team1_players)
        team2_avg = sum(self.player_elos[p['name']]['elo'] for p in team2_players) / len(team2_players)
        
        # Expected scores
        team1_expected = self.expected_score(team1_avg, team2_avg)
        team2_expected = self.expected_score(team2_avg, team1_avg)
        
        # Actual scores
        team1_actual = 1.0 if winning_team == 1 else 0.0
        team2_actual = 1.0 if winning_team == 2 else 0.0
        
        # Update team 1
        for player in team1_players:
            name = player['name']
            old_elo = self.player_elos[name]['elo']
            self.player_elos[name]['elo'] = self.update_elo(old_elo, team1_expected, team1_actual)
            self.player_elos[name]['games'] += 1
            if team1_actual == 1.0:
                self.player_elos[name]['wins'] += 1
            else:
                self.player_elos[name]['losses'] += 1
        
        # Update team 2
        for player in team2_players:
            name = player['name']
            old_elo = self.player_elos[name]['elo']
            self.player_elos[name]['elo'] = self.update_elo(old_elo, team2_expected, team2_actual)
            self.player_elos[name]['games'] += 1
            if team2_actual == 1.0:
                self.player_elos[name]['wins'] += 1
            else:
                self.player_elos[name]['losses'] += 1
    
    def get_player_stats(self) -> List[Dict[str, Any]]:
        stats = []
        for name, data in self.player_elos.items():
            initial = data.get('initial_elo', self.initial_elo)
            current = data['elo']
            stats.append({
                'name': name,
                'elo': round(current, 2),
                'initial_elo': round(initial, 2),
                'elo_change': round(current - initial, 2),
                'games': data['games'],
                'wins': data['wins'],
                'losses': data['losses'],
                'win_rate': round(data['wins'] / data['games'] * 100, 2) if data['games'] > 0 else 0
            })
        stats.sort(key=lambda x: x['elo'], reverse=True)
        return stats

def load_initial_elos(filepath: Path, aliases: Dict[str, str]) -> Dict[str, float]:
    """Load initial ELOs with alias normalization"""
    data = load_json(filepath, {})
    
    normalized = {}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'name' in item and 'elo' in item:
                name = normalize_name(item['name'], aliases)
                normalized[name] = item['elo']
    else:
        for name, elo in data.items():
            canonical = normalize_name(name, aliases)
            normalized[canonical] = elo
    
    return normalized

def calculate_elos(
    matches_file: str = None,
    output_file: str = None,
    k_factor: int = 32,
    initial_elo_file: str = None,
    alias_file: str = None
) -> List[Dict[str, Any]]:
    """Calculate ELOs from match history"""
    
    if matches_file is None:
        matches_file = DATA_DIR / "cs_matches.jsonl"
    if output_file is None:
        output_file = DATA_DIR / "player_elos.json"
    
    # Load aliases
    aliases = load_aliases(Path(alias_file) if alias_file else None)
    
    # Load initial ELOs
    custom_initial_elos = {}
    if initial_elo_file:
        custom_initial_elos = load_initial_elos(Path(initial_elo_file), aliases)
    else:
        default_initial = DATA_DIR / "initial_elos.json"
        if default_initial.exists():
            custom_initial_elos = load_initial_elos(default_initial, aliases)
    
    # Load matches
    matches = load_jsonl(Path(matches_file))
    
    # Sort by date (oldest first)
    matches.sort(key=lambda m: parse_date(m.get('date', '')))
    
    # Process matches
    elo_system = EloSystem(k_factor=k_factor, custom_initial_elos=custom_initial_elos)
    for match in matches:
        elo_system.process_match(match)
    
    # Get and save stats
    player_stats = elo_system.get_player_stats()
    save_json(Path(output_file), player_stats)
    
    return player_stats