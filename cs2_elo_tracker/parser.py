import re
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from .utils import (
    DATA_DIR, load_jsonl, save_jsonl, load_aliases, 
    normalize_name
)

def parse_mvp_stars(star_text: str) -> int:
    """Parse MVP stars from text"""
    if not star_text or star_text.strip() == '':
        return 0
    star_text = star_text.strip()
    match = re.search(r'★(\d+)', star_text)
    if match:
        return int(match.group(1))
    elif '★' in star_text:
        return 1
    return 0

def parse_percentage(pct_text: str) -> int:
    """Parse percentage from text"""
    if not pct_text or pct_text.strip() == '':
        return None
    match = re.search(r'(\d+)%', pct_text)
    if match:
        return int(match.group(1))
    return None

def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime"""
    try:
        return datetime.strptime(date_str.replace(' GMT', ''), '%Y-%m-%d %H:%M:%S')
    except:
        return datetime(1970, 1, 1)

def parse_player_data(name_line: str, stats_line: str, aliases: Dict[str, str] = None) -> Dict[str, Any]:
    """Parse player data from name and stats lines"""
    player_name = name_line.strip()
    
    if not player_name or player_name == 'Player Name':
        return None
    
    if aliases:
        player_name = normalize_name(player_name, aliases)
    
    parts = [p.strip() for p in stats_line.split('\t')]
    
    if len(parts) < 4:
        return None
    
    try:
        return {
            'name': player_name,
            'ping': int(parts[0]) if parts[0] and parts[0].isdigit() else 0,
            'kills': int(parts[1]) if parts[1] and parts[1].isdigit() else 0,
            'assists': int(parts[2]) if parts[2] and parts[2].isdigit() else 0,
            'deaths': int(parts[3]) if parts[3] and parts[3].isdigit() else 0,
            'mvp_stars': parse_mvp_stars(parts[4]) if len(parts) > 4 else 0,
            'headshot_percentage': parse_percentage(parts[5]) if len(parts) > 5 else None,
            'score': int(parts[6]) if len(parts) > 6 and parts[6].isdigit() else 0
        }
    except (ValueError, IndexError):
        return None

def create_match_id(match: Dict[str, Any]) -> str:
    """Create unique match identifier"""
    date = match.get('date', '')
    map_name = match.get('map', '')
    score1 = match.get('team1_score', 0)
    score2 = match.get('team2_score', 0)
    team1_names = sorted([p['name'] for p in match.get('team1_players', [])])
    team2_names = sorted([p['name'] for p in match.get('team2_players', [])])
    return f"{date}|{map_name}|{score1}:{score2}|{','.join(team1_names[:3])}|{','.join(team2_names[:3])}"

def parse_matches_from_text(content: str, aliases: Dict[str, str] = None) -> List[Dict[str, Any]]:
    """Parse CS2 match history from text content"""
    if aliases is None:
        aliases = {}
    
    matches = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('Competitive'):
            match_data = {}
            
            map_match = re.match(r'Competitive\s+(.+)', line)
            if map_match:
                match_data['map'] = map_match.group(1).strip()
            
            i += 1
            
            # Parse date
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                match_data['date'] = lines[i].strip()
                i += 1
            
            # Parse wait time and duration
            while i < len(lines):
                line = lines[i].strip()
                if 'Wait Time:' in line:
                    wait_match = re.search(r'Wait Time:\s*(.+)', line)
                    if wait_match:
                        match_data['wait_time'] = wait_match.group(1).strip()
                    i += 1
                elif 'Match Duration:' in line:
                    duration_match = re.search(r'Match Duration:\s*(.+)', line)
                    if duration_match:
                        match_data['match_duration'] = duration_match.group(1).strip()
                    i += 1
                    break
                else:
                    i += 1
                    if i - 1 > 10:
                        break
            
            # Skip to player header
            while i < len(lines) and 'Player Name' not in lines[i]:
                i += 1
            
            if i >= len(lines):
                break
            
            i += 1
            
            while i < len(lines) and not lines[i].strip():
                i += 1
            
            # Parse team 1
            team1_players = []
            while i < len(lines):
                line = lines[i].strip()
                
                if not line:
                    i += 1
                    continue
                
                score_match = re.match(r'^(\d+)\s*:\s*(\d+)$', line)
                if score_match:
                    match_data['team1_score'] = int(score_match.group(1))
                    match_data['team2_score'] = int(score_match.group(2))
                    i += 1
                    break
                
                if i + 1 < len(lines):
                    player = parse_player_data(lines[i], lines[i + 1], aliases)
                    if player:
                        team1_players.append(player)
                        i += 2
                    else:
                        i += 1
                else:
                    i += 1
            
            match_data['team1_players'] = team1_players
            
            while i < len(lines) and not lines[i].strip():
                i += 1
            
            # Parse team 2
            team2_players = []
            while i < len(lines):
                line = lines[i].strip()
                
                if not line:
                    i += 1
                    continue
                
                if line.startswith('Competitive'):
                    break
                
                if i + 1 < len(lines):
                    if lines[i + 1].strip().startswith('Competitive'):
                        break
                    
                    player = parse_player_data(lines[i], lines[i + 1], aliases)
                    if player:
                        team2_players.append(player)
                        i += 2
                    else:
                        i += 1
                        if len(team2_players) > 0:
                            break
                else:
                    i += 1
                    break
            
            match_data['team2_players'] = team2_players
            
            # Determine winner
            if 'team1_score' in match_data and 'team2_score' in match_data:
                if match_data['team1_score'] > match_data['team2_score']:
                    match_data['winning_team'] = 1
                elif match_data['team2_score'] > match_data['team1_score']:
                    match_data['winning_team'] = 2
                else:
                    match_data['winning_team'] = 0
            
            if team1_players or team2_players:
                matches.append(match_data)
        else:
            i += 1
    
    return matches

def parse_and_save(input_file: str, output_file: str = None, alias_file: str = None) -> tuple:
    """Parse matches from file and save to database"""
    if output_file is None:
        output_file = DATA_DIR / "cs_matches.jsonl"
    else:
        output_file = Path(output_file)
    
    # Load aliases
    aliases = load_aliases(Path(alias_file) if alias_file else None)
    
    # Read input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse new matches
    new_matches = parse_matches_from_text(content, aliases)
    
    # Load existing matches
    existing_matches = load_jsonl(output_file)
    
    # Merge and deduplicate
    match_dict = {}
    for match in existing_matches:
        match_dict[create_match_id(match)] = match
    
    new_count = 0
    for match in new_matches:
        match_id = create_match_id(match)
        if match_id not in match_dict:
            new_count += 1
        match_dict[match_id] = match
    
    # Sort by date (newest first)
    all_matches = list(match_dict.values())
    all_matches.sort(key=lambda m: parse_date(m.get('date', '')), reverse=True)
    
    # Save
    save_jsonl(output_file, all_matches)
    
    return len(new_matches), new_count, len(all_matches)