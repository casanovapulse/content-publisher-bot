import os
import requests
import json
import random
import base64
from dotenv import load_dotenv

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
BASE_URL = "https://gen.pollinations.ai"

if not POLLINATIONS_API_KEY:
    print("Warning: POLLINATIONS_API_KEY not found in .env.")

def generate_script():
    history_file = "topic_history.txt"
    past_topics = ""
    past_topics_lower = ""
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            all_history = f.read().strip()
        topics_list = [t.strip() for t in all_history.split(",") if t.strip()]
        past_topics = ", ".join(topics_list[-30:])
        past_topics_lower = past_topics.lower()

    random_seed = random.randint(10000, 99999)

    prompt = f"""
    TASK: Generate a 45-second IELTS vocabulary lesson.
    FOCUS: A RARE, sophisticated "Band 9" vocabulary word or academic phrase.
    RANDOM SEED: {random_seed}
    PREVIOUS TOPICS (STRICTLY FORBIDDEN): {past_topics}

    CRITICAL RULES:
    1. DO NOT include conversational filler like "Absolutely".
    2. Start the spoken script IMMEDIATELY with the hook.
    3. Output EXACTLY 3 hashtags.
    4. Duration: 45-50 seconds.
    5. Be unique. NEVER repeat or use anything similar to previous topics.
    6. The example MUST be SHORT - maximum 10-12 words, one simple sentence.

    JSON STRUCTURE:
    {{
        "display_title": "[PHRASE]",
        "basic_way": "The common way (short phrase)",
        "better_way": "The advanced way (short phrase)",
        "example": "Short example sentence (max 12 words)",
        "full_spoken_script": "Explain the nuance. Direct start.",
        "social_title": "IELTS Band 9: [PHRASE]",
        "social_hashtags": ["#IELTS", "#Vocabulary", "#English"]
    }}
    """

    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
        "Content-Type": "application/json"
    }

    FALLBACK_PHRASES = [
        "To Pivot Strategically", "To Leverage Synergies", "To Navigate Ambiguity",
        "To Cultivate Resilience", "To Articulate Vision", "To Operationalize Concepts",
        "To Democratize Access", "To Contextualize Findings", "To Problematize Assumptions",
        "To Synthesize Perspectives", "To Scrutinize Evidence", "To Substantiate Claims"
    ]

    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            current_seed = random_seed + attempt
            data = {
                "model": "gemini-fast",
                "messages": [
                    {"role": "system", "content": "You are a robotic script generator. You strictly avoid repetition. You never use conversational filler. You provide rare academic language."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": min(0.85 + (attempt * 0.05), 1.0),
                "seed": current_seed
            }

            response = requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            script_data = response.json()['choices'][0]['message']['content']

            if "```json" in script_data:
                script_data = script_data.replace("```json", "").replace("```", "")
            script_data = json.loads(script_data)

            display_title = script_data.get('display_title', '')
            if display_title and display_title.lower() in past_topics_lower:
                if attempt < max_attempts - 1:
                    print(f"Repeat topic '{display_title}', retrying...")
                    continue
                else:
                    fallback = random.choice(FALLBACK_PHRASES)
                    print(f"Using fallback: {fallback}")
                    script_data["display_title"] = fallback
                    script_data["better_way"] = fallback
                    script_data["example"] = f"The ability to {fallback.lower()} is crucial for success."
                    script_data["full_spoken_script"] = (
                        f'"{fallback}" means to {fallback.lower()}. '
                        f"Use this in academic writing or IELTS essays. "
                        f"For example: 'The ability to {fallback.lower()} is crucial for success.'"
                    )
                    script_data["social_title"] = f"IELTS Band 9: {fallback}"

            with open(history_file, "a") as f:
                f.write(f"{script_data.get('display_title')}, ")

            return script_data

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text[:300]}")
            if attempt == max_attempts - 1:
                return None

    return None


def generate_audio_segment(text, filename, output_dir="generated_content"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    audio_path = os.path.join(output_dir, f"{filename}.mp3")

    try:
        import edge_tts
        import asyncio
        print(f"Generating audio via Edge TTS...")
        async def _generate():
            communicate = edge_tts.Communicate(text, voice="en-US-JennyNeural")
            await communicate.save(audio_path)
        asyncio.run(_generate())
        print(f"Generated audio: {audio_path}")
        return audio_path
    except Exception as e:
        print(f"Edge TTS failed ({e}), falling back to Google TTS...")
        try:
            from gtts import gTTS
            print(f"Generating audio via Google TTS...")
            tts = gTTS(text, lang='en', tld='com')
            tts.save(audio_path)
            print(f"Generated audio: {audio_path}")
            return audio_path
        except Exception as e2:
            print(f"Google TTS also failed: {e2}")
            return None


def generate_full_cycle():
    print("Generating IELTS Content Script...")
    script = generate_script()

    if not script:
        print("Failed to generate script.")
        return None

    print(json.dumps(script, indent=2))

    if not os.path.exists("generated_content"):
        os.makedirs("generated_content")

    with open("generated_content/script.json", "w") as f:
        json.dump(script, f, indent=2)

    print("\nGenerating Audio...")
    audio_path = generate_audio_segment(script['full_spoken_script'], "full_audio")

    return {
        "script": script,
        "audio_file": audio_path,
        "images": []
    }


if __name__ == "__main__":
    generate_full_cycle()
