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
    # This URL is on a different domain, so it's kept separate
    login_url = "https://users.premierleague.com/accounts/login/"

    payload = {
        "login": config.FPL_EMAIL,
        "password": config.FPL_PASSWORD,
        "redirect_uri": "https://fantasy.premierleague.com/",
        "app": "plfpl-web"
    }
    
    session.post(login_url, data=payload, headers=HEADERS)
    
    # Verify session is authenticated
    response = session.get(constants.API_URLS["me"], headers=HEADERS) 
    if response.status_code != 200:
        raise Exception("Failed to authenticate session. Please check your credentials.")
        
    return session

def get_me(session):
    """Fetches the /api/me/ endpoint data using the authenticated session."""
    url = constants.API_URLS["me"] 
    response = session.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_my_team(session):
    """Fetches the user's current team using an authenticated session."""
    url = constants.API_URLS["user_team"].format(config.TEAM_ID) 
    response = session.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_bootstrap_data():
    """Fetches the main bootstrap-static data (all players, teams, etc.)."""
    url = constants.API_URLS["static"] 
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def make_transfers(session, payload):
    """Submits the transfer payload to the FPL API."""
    url = constants.API_URLS["transfers"] 
    response = session.post(url, json=payload, headers=HEADERS)
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