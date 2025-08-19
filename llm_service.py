# llm_service.py
import config
import json

# Import AI libraries based on what's needed
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

def get_ai_recommendations_gemini(prompt):
    """Sends the prompt to the Gemini API and gets transfer recommendations."""
    if not GEMINI_AVAILABLE:
        print("Gemini library not available. Install with: pip install google-generativeai")
        return None
        
    print(f"Using Gemini API Key: {config.GEMINI_API_KEY[:10]}...")
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash', tools=["google_search_retrieval"])
        response = model.generate_content(prompt)
        cleaned_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_json)
        
    except Exception as e:
        print(f"Error occurred with Gemini API: {e}")
        print(f"   Raw Response: {response.text if 'response' in locals() else 'No response'}")
        return None

def get_ai_recommendations_claude(prompt):
    """Sends the prompt to the Claude API and gets transfer recommendations."""
    if not CLAUDE_AVAILABLE:
        print("Claude library not available. Install with: pip install anthropic")
        return None
        
    print(f"Using Claude API Key: {config.CLAUDE_API_KEY[:10]}...")
    try:
        client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract JSON from Claude's response
        raw_text = response.content[0].text
        
        # Find JSON block between ```json and ```
        json_start = raw_text.find('```json')
        json_end = raw_text.find('```', json_start + 7)
        
        if json_start != -1 and json_end != -1:
            json_text = raw_text[json_start + 7:json_end].strip()
        else:
            # Fallback: look for { to } pattern
            start_brace = raw_text.find('{')
            end_brace = raw_text.rfind('}')
            if start_brace != -1 and end_brace != -1:
                json_text = raw_text[start_brace:end_brace + 1]
            else:
                raise ValueError("Could not find JSON in response")
                
        return json.loads(json_text)
        
    except Exception as e:
        print(f"Error occurred with Claude API: {e}")
        if 'response' in locals():
            try:
                raw_text = response.content[0].text
                print(f"   Raw Response Length: {len(raw_text)} characters")
                # Save response to file to avoid encoding issues
                with open('claude_response_debug.txt', 'w', encoding='utf-8') as f:
                    f.write(raw_text)
                print("   Full response saved to claude_response_debug.txt")
            except Exception as print_error:
                print(f"   Could not save response: {print_error}")
        return None

def get_ai_recommendations(prompt):
    """Main function that routes to the configured LLM provider."""
    if config.LLM_PROVIDER == "claude":
        return get_ai_recommendations_claude(prompt)
    elif config.LLM_PROVIDER == "gemini":
        return get_ai_recommendations_gemini(prompt)
    else:
        print(f"Unknown LLM provider: {config.LLM_PROVIDER}")
        return None