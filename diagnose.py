import fpl_api
import config

def run_final_diagnostic():
    """
    This is the definitive test. It gets the Team ID directly from the
    server and immediately tries to use it.
    """
    print("--- Starting Final FPL API Diagnostic ---")
    
    session = None
    me_data = None
    
    # 1. Authenticate the session
    try:
        session = fpl_api.login_and_get_session()
        print("✅ STEP 1: Login and session SUCCEEDED.")
    except Exception as e:
        print(f"❌ STEP 1: Login and session FAILED. Please double-check your .env file. Error: {e}")
        return

    # 2. Get the Team ID from the server
    try:
        me_data = fpl_api.get_me(session)
        if not me_data.get('player'):
            print("❌ STEP 2: Fetching /api/me/ FAILED. The server's response does not contain a 'player' object.")
            print("   This can happen if you haven't finished setting up your FPL team for the season on the website.")
            return
            
        server_confirmed_id = me_data['player']['entry']
        print(f"✅ STEP 2: Fetching /api/me/ SUCCEEDED. The server confirms your Team ID is: {server_confirmed_id}")
    except Exception as e:
        print(f"❌ STEP 2: Fetching /api/me/ FAILED. Error: {e}")
        return

    # 3. Use the server-confirmed ID to fetch the team
    print(f"\n--- Attempting to fetch team data using the confirmed ID: {server_confirmed_id} ---")
    try:
        # We will create the URL manually using the ID we just got
        team_url = f"https://fantasy.premierleague.com/api/my-team/{server_confirmed_id}/"
        response = session.get(team_url, headers=fpl_api.HEADERS)
        response.raise_for_status() # Raise an error for bad responses
        
        print("✅ FINAL RESULT: SUCCEEDED! Successfully fetched team data.")
        print("   This means the bot can now access your team.")

    except Exception as e:
        print(f"❌ FINAL RESULT: FAILED. We used the correct ID confirmed by the server, but still failed.")
        print(f"   Error: {e}")
        print("\n   This definitively means the issue is NOT your code or a wrong ID, but an unusual problem with your FPL account's permissions or a temporary FPL server-side bug.")

if __name__ == "__main__":
    run_final_diagnostic()