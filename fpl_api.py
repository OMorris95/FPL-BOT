import requests
import config
import constants  

# Define headers once to be used in all requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def login_and_get_session():
    """Logs into FPL and returns an authenticated session object."""
    session = requests.Session()
    login_url = "https://users.premierleague.com/accounts/login/"

    payload = {
        "login": config.FPL_EMAIL,
        "password": config.FPL_PASSWORD,
        "redirect_uri": "https://fantasy.premierleague.com/",
        "app": "plfpl-web"
    }
    
    # Login request
    login_response = session.post(login_url, data=payload, headers=HEADERS)
    
    # Verify session is authenticated by checking if we can access protected data
    response = session.get(constants.API_URLS["user"].format(config.TEAM_ID), headers=HEADERS) 
    if response.status_code != 200:
        raise Exception(f"Failed to authenticate session. Status: {response.status_code}. Please check your credentials.")
        
    return session

def get_me(session):
    """Fetches the /api/me/ endpoint data using the authenticated session."""
    url = constants.API_URLS["me"] 
    response = session.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_my_team(session):
    """Fetches the user's current team using an authenticated session."""
    # Get bootstrap data to find current gameweek
    bootstrap_data = get_bootstrap_data()
    current_gameweek = next((event['id'] for event in bootstrap_data['events'] if event['is_current']), 1)
    
    # Use the picks endpoint instead of my-team which returns 403
    url = constants.API_URLS["user_picks"].format(config.TEAM_ID, current_gameweek)
    response = session.get(url, headers=HEADERS)
    response.raise_for_status()
    picks_data = response.json()
    
    # Also get transfer data from entry endpoint
    entry_url = constants.API_URLS["user"].format(config.TEAM_ID)
    entry_response = session.get(entry_url, headers=HEADERS)
    entry_response.raise_for_status()
    entry_data = entry_response.json()
    
    # Transform the data to match the expected format
    transformed_data = {
        'picks': picks_data['picks'],
        'transfers': {
            'limit': entry_data.get('last_deadline_total_transfers', 1) + 1,  # Add 1 for free transfer
            'bank': picks_data['entry_history']['bank'],
            'value': picks_data['entry_history']['value']
        }
    }
    
    # Add selling prices to picks - for now use current price as selling price
    # (In reality, selling price might be different, but we don't have this data)
    player_map = {p['id']: p for p in bootstrap_data['elements']}
    for pick in transformed_data['picks']:
        player = player_map.get(pick['element'])
        pick['selling_price'] = player['now_cost'] if player else 0
    
    return transformed_data

def get_bootstrap_data():
    """Fetches the main bootstrap-static data (all players, teams, etc.)."""
    url = constants.API_URLS["static"] 
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def make_transfers(session, payload):
    """Submits the transfer payload to the FPL API."""
    url = constants.API_URLS["transfers"] 
    
    # Add additional headers that might be required
    transfer_headers = HEADERS.copy()
    transfer_headers.update({
        'Content-Type': 'application/json',
        'Referer': 'https://fantasy.premierleague.com/'
    })
    
    print(f"Making transfer request to: {url}")
    print(f"Payload: {payload}")
    
    response = session.post(url, json=payload, headers=transfer_headers)
    
    print(f"Transfer response status: {response.status_code}")
    print(f"Transfer response: {response.text}")
    
    response.raise_for_status()
    return response.status_code

def get_fixtures_data():
    """Fetches the full list of fixtures for the season."""
    url = constants.API_URLS["fixtures"] 
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_gameweek_picks(session, team_id, gameweek_id):
    """Fetches the full details of a user's team for a specific gameweek."""
    url = constants.API_URLS["user_picks"].format(team_id, gameweek_id)
    response = session.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()