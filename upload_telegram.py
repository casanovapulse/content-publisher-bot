"""
Upload video to Telegram channel
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def upload_to_telegram(video_path, caption):
    """
    Upload video to Telegram channel
    
    Args:
        video_path: Path to video file
        caption: Caption for the video
    
    Returns:
        dict: Response from Telegram API
    """
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
    
    if not bot_token or not channel_id:
        raise ValueError("Missing Telegram credentials. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID in .env")
    
    # Telegram API endpoint
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    
    # Prepare the video file
    with open(video_path, 'rb') as f:
        print(f"Uploading to Telegram channel: {channel_id}")
        
        # Note: requests.post() behavior with 'files' and 'data' arguments
        # If 'data' is a dict, it will be sent as multipart/form-data with values as text fields
        resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendVideo",
            data={'chat_id': channel_id, 'caption': caption},
            files={'video': f}
        )
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get('ok'):
                print(f"✅ Successfully uploaded to Telegram!")
                return result
            else:
                raise Exception(f"Telegram API error: {result.get('description')}")
        else:
            raise Exception(f"HTTP {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    pass
