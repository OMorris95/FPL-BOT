import logger
import fpl_api
import data_processor
import json
import smtplib
from email.message import EmailMessage

def _send_approval_email(ai_response, config):
    """Sends an email notification when a points hit is required."""
    msg = EmailMessage()
    msg.set_content(f"FPL Bot requires approval for a transfer with a points hit.\n\nRecommendations:\n{json.dumps(ai_response, indent=2)}")
    msg['Subject'] = 'FPL Bot: Manual Approval Required'
    msg['From'] = config.EMAIL_ADDRESS
    msg['To'] = config.EMAIL_RECIPIENT

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ Approval email sent.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def _prepare_transfer_payload(transfers_to_make, team_id, gameweek, player_id_map, selling_price_map, bootstrap_data):
    """Constructs the JSON payload required by the FPL transfers API."""
    
    payload_transfers = []
    all_players = bootstrap_data['elements']

    for transfer in transfers_to_make:
        player_out_name = transfer['player_out']
        player_in_name = transfer['player_in']

        # Find the IDs and prices needed for the payload
        player_out_id = player_id_map.get(player_out_name)
        player_in_id = player_id_map.get(player_in_name)
        
        if not player_out_id or not player_in_id:
            print(f"⚠️ Warning: Could not find ID for {player_out_name} or {player_in_name}. Skipping transfer.")
            continue

        selling_price = selling_price_map.get(player_out_id)
        purchase_price = next((p['now_cost'] for p in all_players if p['id'] == player_in_id), None)

        payload_transfers.append({
            "element_in": player_in_id,
            "element_out": player_out_id,
            "purchase_price": purchase_price,
            "selling_price": selling_price
        })

    return {
        "chips": None,
        "entry": team_id,
        "event": gameweek,
        "transfers": payload_transfers
    }

def execute_transfers(session, payload):
    """⚠️ DANGEROUS! This function executes transfers on your FPL team."""
    print("Executing transfers...")
    try:
        fpl_api.make_transfers(session, payload)
        # --- ADD LOGGING HERE ---
        for transfer in payload['transfers']:
            log_message = (f"TRANSFER MADE: OUT - {transfer['element_out']}, "
                           f"IN - {transfer['element_in']}")
            logger.log_action(log_message)
        # ------------------------
        print("✅ Transfers successfully executed!")
    except Exception as e:
        print(f"❌ An error occurred while executing transfers: {e}")

def handle_ai_recommendations(session, ai_response, config, bootstrap_data, my_team_data):
    """The main logic for deciding what to do with the AI's recommendations."""
    
    transfers = ai_response.get('transfers', [])
    if not transfers:
        print("AI recommends no transfers. No action taken.")
        return

    num_transfers = len(transfers)
    free_transfers = my_team_data['transfers']['limit']
    points_hit = max(0, num_transfers - free_transfers) * 4

    print("\n--- Decision Engine ---")
    print(f"AI has suggested {num_transfers} transfer(s).")
    if points_hit > 0:
        print(f"This will incur a points hit of -{points_hit} points.")
        points_hit = max(0, num_transfers - free_transfers) * 4

        print("\n--- Decision Engine ---")
        print(f"AI has suggested {num_transfers} transfer(s).")
        if points_hit > 0:
            message = f"This will incur a points hit of -{points_hit} points."
            print(message)
            # --- ADD LOGGING HERE ---
            logger.log_action(f"POINTS HIT: A hit of -{points_hit} was taken.")

    # --- Autonomy Logic ---
    if config.USER_MODE == 'suggest':
        print("Operating in 'suggest' mode. Here are the recommendations:")
        print(json.dumps(ai_response, indent=2))
        print("Please make the transfers manually on the FPL website.")
        
    elif config.USER_MODE == 'hybrid':
        print("Operating in 'hybrid' mode.")
        if points_hit > 0:
            print("Point hit required. Sending email for manual approval.")
            _send_approval_email(ai_response, config)
        else:
            print("No point hit required. Proceeding with automatic transfer.")
            gameweek = next((event['id'] for event in bootstrap_data['events'] if event['is_next']), None)
            player_id_map = data_processor.get_player_id_map(bootstrap_data)
            selling_price_map = data_processor.get_player_selling_price_map(my_team_data)
            
            payload = _prepare_transfer_payload(transfers, config.TEAM_ID, gameweek, player_id_map, selling_price_map, bootstrap_data)
            execute_transfers(session, payload)
            
            payload = _prepare_transfer_payload(transfers, config.TEAM_ID, gameweek, player_id_map, selling_price_map, bootstrap_data)
            execute_transfers(session, payload)
            
    elif config.USER_MODE == 'auto':
        print("Operating in 'auto' mode. Proceeding with automatic transfer.")
        # All preparation for making the transfer goes here
        gameweek = next((event['id'] for event in bootstrap_data['events'] if event['is_next']), None)
        player_id_map = data_processor.get_player_id_map(bootstrap_data)
        selling_price_map = data_processor.get_player_selling_price_map(my_team_data)
        
        payload = _prepare_transfer_payload(transfers, config.TEAM_ID, gameweek, player_id_map, selling_price_map, bootstrap_data)
        execute_transfers(session, payload)