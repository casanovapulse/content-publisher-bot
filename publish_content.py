"""
Multi-Platform Publisher for IELTS Zoom
"""

import os
import json
from pathlib import Path
import datetime

# Import platform-specific uploaders
from upload_to_youtube import upload_to_youtube
from upload_instagram import upload_to_instagram
from upload_tiktok import upload_to_tiktok
from upload_facebook import upload_to_facebook
from upload_threads import upload_to_threads
from upload_twitter import upload_to_twitter
from upload_telegram import upload_to_telegram
from upload_vk import upload_to_vk

def main():
    """Upload video to configured platforms."""
    # Locate video file
    video_file = Path('ielts_short.mp4')
    if not video_file.exists():
        # Fallback to final_videos/ if running locally
        final_dir = Path('final_videos')
        if final_dir.exists():
            files = list(final_dir.glob('*.mp4'))
            if files:
                # Get the most recent video
                video_file = sorted(files, key=os.path.getmtime)[-1]
    
    if not video_file.exists():
        print("❌ No video found (checked ielts_short.mp4 and final_videos/*.mp4)")
        return
        
    print(f"🎬 Processing Video: {video_file}")
    
    # Read metadata from script
    script_file = Path('generated_content/script.json')
    if script_file.exists():
        with open(script_file, 'r') as f:
            script = json.load(f)
        social_title = script.get('social_title', 'IELTS Vocabulary Upgrade')
        hashtags_list = script.get('social_hashtags', ['#IELTS', '#English', '#Speaking'])
    else:
        social_title = f"IELTS Speaking Tip - {datetime.date.today()}"
        hashtags_list = ["#IELTS", "#English", "#Speaking"]

    # Limit to exactly 3 hashtags
    hashtags_str = " ".join(hashtags_list[:3])

    description = f"""{social_title}

Learn the right way to use advanced English vocabulary for your IELTS exam. 🚀

{hashtags_str}"""

    tags = [tag.strip('#') for tag in hashtags_list[:3]]
    
    # --- YouTube ---
    if os.getenv('YT_REFRESH_TOKEN'):
        try:
            print("\n📺 Uploading to YouTube...")
            upload_to_youtube(video_file, social_title, description, tags)
        except Exception as e:
            print(f"❌ YouTube Failed: {e}")
    else:
        print("⏭️  Skipping YouTube (YT_REFRESH_TOKEN missing)")

    # --- Instagram ---
    if os.getenv('IG_ACCESS_TOKEN'):
        try:
            print("\n📸 Uploading to Instagram...")
            upload_to_instagram(video_file, description)
        except Exception as e:
            print(f"❌ Instagram Failed: {e}")
    else:
        print("⏭️  Skipping Instagram (IG_ACCESS_TOKEN missing)")

    # --- Threads ---
    if os.getenv('THREADS_ACCESS_TOKEN') and os.getenv('THREADS_USER_ID'):
        try:
            print("\n🧵 Uploading to Threads...")
            upload_to_threads(video_file, description)
        except Exception as e:
            print(f"❌ Threads Failed: {e}")
    else:
        print("⏭️  Skipping Threads (THREADS keys missing)")

    # --- TikTok ---
    if os.getenv('TIKTOK_ACCESS_TOKEN'):
        try:
            print("\n🎵 Uploading to TikTok...")
            # Note: TikTok logic might need specific adjustment depending on the implementation
            upload_to_tiktok(video_file, social_title, description) 
        except Exception as e:
            print(f"❌ TikTok Failed: {e}")
    else:
        print("⏭️  Skipping TikTok (TIKTOK_ACCESS_TOKEN missing)")
        
    # --- Twitter / X ---
    if os.getenv('TWITTER_API_KEY') and os.getenv('TWITTER_ACCESS_TOKEN'):
        try:
            print("\n🐦 Uploading to Twitter...")
            upload_to_twitter(video_file, description)
        except Exception as e:
            print(f"❌ Twitter Failed: {e}")
    else:
        print("⏭️  Skipping Twitter (Credentials missing)")

    # --- Telegram ---
    if os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('TELEGRAM_CHANNEL_ID'):
        try:
            print("\n✈️ Uploading to Telegram...")
            # Assuming upload_to_telegram takes (file_path, caption)
            upload_to_telegram(video_file, description)
        except Exception as e:
            print(f"❌ Telegram Failed: {e}")
    else:
        print("⏭️  Skipping Telegram (Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID)")

    # --- VK ---
    if os.getenv('VK_ACCESS_TOKEN') and os.getenv('VK_GROUP_ID'):
        try:
            print("\n🇷🇺 Uploading to VK...")
            upload_to_vk(video_file, description, social_title)
        except Exception as e:
            print(f"❌ VK Failed: {e}")
    else:
        print("⏭️  Skipping VK (VK_ACCESS_TOKEN or VK_GROUP_ID missing)")

if __name__ == '__main__':
    main()
