# data_processor.py
import json

def get_team_name_map(bootstrap_data):
    """Creates a mapping from team ID to team short name (e.g., 1 -> ARS)."""
    return {team['id']: team['short_name'] for team in bootstrap_data['teams']}

def get_player_name_map(bootstrap_data):
    """Creates a mapping from player ID to player web name (e.g., 233 -> Salah)."""
    return {player['id']: player['web_name'] for player in bootstrap_data['elements']}

def get_my_team_details(my_team_data, player_name_map):
    """Processes the user's team data into a simple, readable format."""
    player_ids = [player['element'] for player in my_team_data['picks']]
    
    # Get free transfers, bank, and team value
    free_transfers = my_team_data['transfers']['limit'] if my_team_data.get('transfers') else 1
    bank = my_team_data['transfers']['bank'] / 10.0 if my_team_data.get('transfers') else 0
    team_value = my_team_data['transfers']['value'] / 10.0 if my_team_data.get('transfers') else 0

    return {
        "player_names": [player_name_map.get(pid, 'Unknown') for pid in player_ids],
        "free_transfers": free_transfers,
        "bank": bank,
        "value": team_value
    }

def process_players_of_interest(bootstrap_data, team_name_map):
    """
    Selects and simplifies data for the top players based on form and points.
    Returns a simplified list of dictionaries for the AI to analyze.
    """
    all_players = bootstrap_data['elements']
    
    # Sort players by form, then by total points as a tie-breaker
    sorted_players = sorted(all_players, key=lambda p: (float(p['form']), p['total_points']), reverse=True)
    
    players_of_interest = []
    # We'll select the top 50 players to keep the prompt focused
    for player in sorted_players[:50]:
        # Skip players with major injuries or suspensions
        if player.get('status') in ['i', 's', 'u'] and player.get('chance_of_playing_next_round', 100) == 0:
            continue
            
        players_of_interest.append({
            "name": player['web_name'],
            "team": team_name_map.get(player['team'], 'N/A'),
            "price": player['now_cost'] / 10.0,
            "form": float(player['form']),
            "points": player['total_points'],
            "news": player.get('news', 'No news').strip()
        })
        
    return players_of_interest

def process_fixture_difficulty(bootstrap_data, fixtures_data, team_name_map):
    """
    Analyzes upcoming fixtures for each team and creates a difficulty summary.
    Lower score = easier fixtures.
    """
    teams_data = bootstrap_data['teams']
    
    # Get the ID for the next gameweek
    next_gameweek_id = next((event['id'] for event in bootstrap_data['events'] if event['is_next']), None)
    
    if not next_gameweek_id:
        return {}

    team_fixtures = {team['id']: [] for team in teams_data}
    
    # Group fixtures by team for the next 5 gameweeks
    for fixture in fixtures_data:
        if fixture['event'] and next_gameweek_id <= fixture['event'] < next_gameweek_id + 5:
            if fixture['team_h']:
                team_fixtures[fixture['team_h']].append(fixture['team_h_difficulty'])
            if fixture['team_a']:
                team_fixtures[fixture['team_a']].append(fixture['team_a_difficulty'])

    # Calculate the average difficulty for each team
    fixture_difficulty_summary = {}
    for team_id, difficulties in team_fixtures.items():
        if difficulties:
            avg_difficulty = sum(difficulties) / len(difficulties)
            team_name = team_name_map.get(team_id, 'N/A')
            fixture_difficulty_summary[team_name] = round(avg_difficulty, 2)
            
    return fixture_difficulty_summary

def get_player_id_map(bootstrap_data):
    """Creates a mapping from player web name to player ID (e.g., Salah -> 233)."""
    return {player['web_name']: player['id'] for player in bootstrap_data['elements']}

def get_player_selling_price_map(my_team_data):
    """Creates a mapping of player IDs in your team to their current selling price."""
    return {player['element']: player['selling_price'] for player in my_team_data['picks']}

def get_squad_by_position(my_team_data, bootstrap_data, team_name_map):
    """Creates formatted strings of players in the squad, broken down by position."""
    
    player_details_map = {p['id']: p for p in bootstrap_data['elements']}
    position_map = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
    
    squad_by_pos = {"GKP": [], "DEF": [], "MID": [], "FWD": []}

    for pick in my_team_data['picks']:
        player_id = pick['element']
        player_detail = player_details_map.get(player_id)
        if not player_detail:
            continue
            
        position = position_map.get(player_detail['element_type'])
        team_name = team_name_map.get(player_detail['team'])
        price = player_detail['now_cost'] / 10.0
        player_name = player_detail['web_name']
        
        selling_price = pick['selling_price'] / 10.0
        formatted_string = f"{player_name} (£{price}m, sells £{selling_price}m, {team_name})"
        squad_by_pos[position].append(formatted_string)
        
    return {
        "squad_gkp_string": ", ".join(squad_by_pos["GKP"]),
        "squad_def_string": ", ".join(squad_by_pos["DEF"]),
        "squad_mid_string": ", ".join(squad_by_pos["MID"]),
        "squad_fwd_string": ", ".join(squad_by_pos["FWD"])
    }

def get_team_distribution(my_team_data, bootstrap_data, team_name_map):
    """Counts the number of players from each Premier League team in the squad."""
    
    player_team_map = {p['id']: p['team'] for p in bootstrap_data['elements']}
    team_counts = {}

    for pick in my_team_data['picks']:
        player_id = pick['element']
        team_id = player_team_map.get(player_id)
        team_name = team_name_map.get(team_id)
        
        if team_name:
            team_counts[team_name] = team_counts.get(team_name, 0) + 1
            
    return json.dumps(team_counts)