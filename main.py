import logger
import fpl_api
import data_processor
import llm_service
import fpl_executor
import json
import config

def run_gameweek_summary(session, config, bootstrap_data):
    """Checks for finished gameweeks and logs their performance summary."""
    print("\n--- Checking for finished gameweeks to log ---")
    
    player_name_map = data_processor.get_player_name_map(bootstrap_data)
    last_logged_gw = logger.get_last_logged_gameweek()
    
    finished_gameweeks = [gw for gw in bootstrap_data['events'] if gw['is_previous'] or (gw['is_current'] and gw['finished'])]
    
    for gw in finished_gameweeks:
        gw_id = gw['id']
        if gw_id > last_logged_gw:
            try:
                print(f"Found new finished Gameweek {gw_id} to log.")
                picks = fpl_api.get_gameweek_picks(session, config.TEAM_ID, gw_id)
                
                # Extract summary data
                points = picks['entry_history']['points']
                points_deducted = picks['entry_history']['event_transfers_cost']
                active_chip = picks.get('active_chip', 'None')
                
                captain_id = next((p['element'] for p in picks['picks'] if p['is_captain']), None)
                vice_captain_id = next((p['element'] for p in picks['picks'] if p['is_vice_captain']), None)
                captain_name = player_name_map.get(captain_id, 'N/A')
                vice_captain_name = player_name_map.get(vice_captain_id, 'N/A')
                
                bench = [player_name_map.get(p['element']) for p in picks['picks'] if p['multiplier'] == 0]

                # Log the summary
                logger.log_action(f"Gameweek Summary for GW{gw_id}:")
                logger.log_action(f"  - Points: {points}")
                logger.log_action(f"  - Points Deducted: -{points_deducted}")
                logger.log_action(f"  - Captain: {captain_name}")
                logger.log_action(f"  - Vice-Captain: {vice_captain_name}")
                logger.log_action(f"  - Chip Played: {active_chip}")
                logger.log_action(f"  - Bench: {', '.join(bench)}")
                print(f"Logged summary for Gameweek {gw_id}.")

            except Exception as e:
                print(f"Failed to log summary for GW{gw_id}: {e}")

def main():
    """Main function for the FPL AI Manager."""
    print("Starting FPL AI Manager...")

    # --- Phase 1: Fetching FPL Data ---
    print("\n--- Phase 1: Fetching FPL Data ---")
    try:
        session = fpl_api.login_and_get_session()
        print("Login and session verified!")
        
        bootstrap_data = fpl_api.get_bootstrap_data()
        fixtures_data = fpl_api.get_fixtures_data()
        
        # --- TEMPORARY PRE-SEASON FIX ---
        # Comment out the live API call
        my_team_data = fpl_api.get_my_team(session)
        
        # Load the local sample file instead
        #print("   -> NOTE: Using local 'my_team_sample.json' for pre-season testing.")
        #with open('my_team_sample.json') as f:
            #my_team_data = json.load(f)
        # ------------------------------

        print("All data fetched successfully.")
    except Exception as e:
        print(f"Failed during data fetching: {e}")
        return

    # --- Phase 2: Processing Data and Consulting AI ---
    print("\n--- Phase 2: Processing Data and Consulting AI ---")
    
    # Process all the data required for the new prompt
    team_name_map = data_processor.get_team_name_map(bootstrap_data)
    player_name_map = data_processor.get_player_name_map(bootstrap_data)
    my_team_details = data_processor.get_my_team_details(my_team_data, player_name_map)
    players_of_interest = data_processor.process_players_of_interest(bootstrap_data, team_name_map)
    current_gameweek = next((event['id'] for event in bootstrap_data['events'] if event['is_next']), None)
    fixture_difficulty = data_processor.process_fixture_difficulty(bootstrap_data, fixtures_data, team_name_map)
    
    # The API 'value' field appears to be total budget (squad + bank), not just squad value
    total_budget = my_team_details.get('value', 0)
    
    # Get the new detailed squad breakdown strings
    squad_breakdown = data_processor.get_squad_by_position(my_team_data, bootstrap_data, team_name_map)
    team_distribution = data_processor.get_team_distribution(my_team_data, bootstrap_data, team_name_map)
    
    print("Data processed.")

    # Build the prompt with all the new placeholders
    try:
        with open('strategy_prompt.txt', 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        prompt = prompt_template.format(
            my_team_string=json.dumps(my_team_details['player_names']),
            bank=my_team_details['bank'],
            free_transfers=my_team_details['free_transfers'],
            gameweek=current_gameweek,
            total_budget=round(total_budget, 1),
            squad_gkp_string=squad_breakdown['squad_gkp_string'],
            squad_def_string=squad_breakdown['squad_def_string'],
            squad_mid_string=squad_breakdown['squad_mid_string'],
            squad_fwd_string=squad_breakdown['squad_fwd_string'],
            team_distribution_string=team_distribution,
            fixture_difficulty_string=json.dumps(fixture_difficulty, indent=2),
            players_of_interest_string=json.dumps(players_of_interest, indent=2)
        )
    except Exception as e:
        print(f"Error building prompt: {e}")
        return
        
    print("Prompt created. Sending to AI for analysis...")
    ai_response = llm_service.get_ai_recommendations(prompt)
    
    if not ai_response:
        print("\nAI analysis failed. Please check error messages above.")
        return
    print("AI analysis complete.")

    # --- Phase 3: Decision Making and Execution ---
    fpl_executor.handle_ai_recommendations(session, ai_response, config, bootstrap_data, my_team_data)

     # --- Run the post-gameweek summary logger ---
    run_gameweek_summary(session, config, bootstrap_data)
    
    print("\nFPL Bot run complete.")


if __name__ == "__main__":
    main()