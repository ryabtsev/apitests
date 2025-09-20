import requests
import os
import json
import re

def extract_json_from_text(text):
    """
    Extracts a JSON string from a markdown code block.
    """
    match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
    if match:
        return match.group(1)
    return None

def generate_gemini_content(api_key, text_prompt):
    """
    Generates content using the Gemini API.
    """
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    params = {
        'key': api_key,
    }
    
    data = {
        'contents': [{
            'parts': [{
                'text': text_prompt
            }]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, params=params, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def get_payload(method, url):
    parsed_json = None
    """
    Main function to run the Gemini API example.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Please set it to your Gemini API key.")
        return

    prompt = f"Give example payload of response for http request: [{method.upper()}] {url}"
    
    generated_content = generate_gemini_content(api_key, prompt)
    if generated_content:
        # Extract and print just the generated text
        try:
            text = generated_content['candidates'][0]['content']['parts'][0]['text']
            
            json_str = extract_json_from_text(text)
            if json_str:
                try:
                    parsed_json = json.loads(json_str)
                except json.JSONDecodeError:
                    print("\nCould not parse the extracted JSON string.")
            else:
                print("\nNo JSON block found in the generated text.")
        except (KeyError, IndexError) as e:
            print(f"\nCould not extract text from response: {e}")

        return parsed_json

