# llm_service.py
import google.generativeai as genai
import config
import json

def get_ai_recommendations(prompt):
    """Sends the prompt to the Gemini API and gets transfer recommendations."""
    print(f"Attempting to use API Key: {config.GEMINI_API_KEY}")
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # --- THIS IS THE ONLY CHANGE ---
        # Enable the Google Search tool for grounding the response
        model = genai.GenerativeModel('gemini-1.5-flash', tools=["google_search_retrieval"])
        # -----------------------------

        response = model.generate_content(prompt)
        cleaned_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_json)
        
    except Exception as e:
        print(f"❌ An error occurred with the AI service: {e}")
        print(f"   Raw AI Response was: {response.text if 'response' in locals() else 'No response'}")
        return None