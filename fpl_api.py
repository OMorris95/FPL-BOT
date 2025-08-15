import requests
import config

# --- Define headers once to be used in all requests ---
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
    
    session.post(login_url, data=payload, headers=HEADERS)
    
    # Verify session is authenticated
    response = session.get("https://fantasy.premierleague.com/api/me/", headers=HEADERS)
    if response.status_code != 200:
        raise Exception("Failed to authenticate session. Please check your credentials.")
        
    return session

# --- NEW FUNCTION ---
def get_me(session):
    """Fetches the /api/me/ endpoint data using the authenticated session."""
    url = "https://fantasy.premierleague.com/api/me/"
    response = session.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

# --- UPDATED FUNCTION ---
def get_my_team(session):
    """Fetches the user's current team using an authenticated session."""
    url = f"https://fantasy.premierleague.com/api/my-team/{config.TEAM_ID}/"
    response = session.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_bootstrap_data():
    """Fetches the main bootstrap-static data (all players, teams, etc.)."""
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_fixtures_data():
    """Fetches the full list of fixtures for the season."""
    url = "https://fantasy.premierleague.com/api/fixtures/"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def make_transfers(session, payload):
    """Submits the transfer payload to the FPL API."""
    url = "https://fantasy.premierleague.com/api/transfers/"
    response = session.post(url, json=payload, headers=HEADERS)
    response.raise_for_status() # Will raise an error for non-200 responses
    return response.status_code

def get_gameweek_picks(session, team_id, gameweek_id):
    """Fetches the full details of a user's team for a specific gameweek."""
    url = f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gameweek_id}/picks/"
    response = session.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()