import os
import requests
import json
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
BASE_URL = "https://gen.pollinations.ai"

# Ensure API key is present
if not POLLINATIONS_API_KEY:
    print("Warning: POLLINATIONS_API_KEY not found in .env. Using free tier (if applicable) or failing.")
    # Assuming free tier might work for some models, but user has key.

def generate_script():
    """Generates a direct IELTS vocabulary upgrade script with social metadata and history tracking."""
    
    history_file = "topic_history.txt"
    past_topics = ""
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            past_topics = f.read()

    prompt = f"""
    TASK: Generate a 45-second IELTS vocabulary lesson.
    FOCUS: High-end "Band 9" vocabulary or phrases.
    PREVIOUS TOPICS (DO NOT REPEAT): {past_topics}
    
    RULES:
    1. DO NOT include conversational filler like "Absolutely".
    2. Start the spoken script IMMEDIATELY.
    3. Output EXACTLY 3 hashtags.
    4. Duration: 45-50 seconds.
    
    JSON STRUCTURE:
    {{
        "display_title": "UPGRADE: [PHRASE]",
        "basic_way": "The common way",
        "better_way": "The advanced way",
        "example": "Full sentence example",
        "full_spoken_script": "Deep dive explanation and example. Direct start.",
        "social_title": "Hooky Video Title for Youtube/Instagram",
        "social_hashtags": ["#Tag1", "#Tag2", "#Tag3"]
    }}
    """
    
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gemini-fast", 
        "messages": [
            {"role": "system", "content": "You are a robotic script output tool. You strictly follow JSON format. You never repeat past topics. No conversational filler."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        script_data = response.json()['choices'][0]['message']['content']
        
        # Cleanup and Load
        if "```json" in script_data:
            script_data = script_data.replace("```json", "").replace("```", "")
        script_data = json.loads(script_data)
        
        # Log to history
        with open(history_file, "a") as f:
            f.write(f"{script_data.get('display_title')}, ")
            
        return script_data
        
    except Exception as e:
        print(f"Error: {e}")
        return None

import base64

# Define Audio Model Constants for Consistency
TTS_MODEL = "openai-audio"
TTS_VOICE = "alloy" # Options: alloy, echo, fable, onyx, nova, shimmer

def generate_audio_segment(text, filename, output_dir="generated_content"):
    """Generates audio speech for a given text segment using Pollinations AI (OpenAI Audio)."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    url = f"{BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Request audio via modalities (OpenAI 4o-audio style)
    data = {
        "model": TTS_MODEL, 
        "messages": [
            {"role": "user", "content": text}
        ],
        "modalities": ["text", "audio"],
        "audio": {"voice": TTS_VOICE, "format": "mp3"}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            print(f"Error generating audio for {filename}: {response.status_code} {response.text}")
            return None
            
        result = response.json()
        if 'choices' in result and 'audio' in result['choices'][0]['message']:
            audio_data = result['choices'][0]['message']['audio']['data']
            audio_path = os.path.join(output_dir, f"{filename}.mp3")
            with open(audio_path, "wb") as f:
                f.write(base64.b64decode(audio_data))
            print(f"Generated audio: {audio_path}")
            return audio_path
        else:
            print(f"No audio data in response for {filename}")
            return None
            
    except Exception as e:
        print(f"Exception generating audio: {e}")
        return None

def generate_full_cycle():
    """Execute full content generation cycle and return result dictionary."""
    print("Generating IELTS Content Script...")
    script = generate_script()
    
    if not script:
        print("Failed to generate script.")
        return None
        
    print(json.dumps(script, indent=2))
    
    # Save script
    if not os.path.exists("generated_content"):
        os.makedirs("generated_content")
        
    with open("generated_content/script.json", "w") as f:
        json.dump(script, f, indent=2)
        
    print("\nGenerating Single Continuous Audio...")
    audio_path = generate_audio_segment(script['full_spoken_script'], "full_audio")
            
    return {
        "script": script,
        "audio_file": audio_path,
        "images": [] 
    }

if __name__ == "__main__":
    generate_full_cycle()
