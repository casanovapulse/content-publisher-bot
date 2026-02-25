"""
Multi-Platform Publisher for IELTS Zoom
"""

import os
import json
from pathlib import Path
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    
    # Store results for final summary
    results = {}

    # --- YouTube ---
    if os.getenv('YT_REFRESH_TOKEN'):
        try:
            print("\n📺 Uploading to YouTube...")
            upload_to_youtube(video_file, social_title, description, tags)
            results['YouTube'] = "✅ Success"
        except Exception as e:
            print(f"❌ YouTube Failed: {e}")
            results['YouTube'] = f"❌ Failed: {str(e)[:50]}..."
    else:
        results['YouTube'] = "⏭️  Skipped (Missing Token)"

    # --- Instagram ---
    if os.getenv('INSTAGRAM_ACCESS_TOKEN'):
        try:
            print("\n📸 Uploading to Instagram Reels...")
            upload_to_instagram(video_file, description)
            
            print("\n📸 Uploading to Instagram Story...")
            upload_to_instagram(video_file, description, is_story=True)
            results['Instagram'] = "✅ Success (Reel + Story)"
        except Exception as e:
            print(f"❌ Instagram Failed: {e}")
            results['Instagram'] = f"❌ Failed: {str(e)[:50]}..."
    else:
        results['Instagram'] = "⏭️  Skipped (Missing Token)"

    # --- Facebook ---
    if os.getenv('FACEBOOK_ACCESS_TOKEN') and os.getenv('FACEBOOK_PAGE_ID'):
        try:
            print("\n📘 Uploading to Facebook...")
            upload_to_facebook(video_file, description)
            results['Facebook'] = "✅ Success"
        except Exception as e:
            print(f"❌ Facebook Failed: {e}")
            results['Facebook'] = f"❌ Failed: {str(e)[:50]}..."
    else:
        results['Facebook'] = "⏭️  Skipped (Missing Token)"

    # --- Threads ---
    if os.getenv('THREADS_ACCESS_TOKEN') and os.getenv('THREADS_USER_ID'):
        try:
            print("\n🧵 Uploading to Threads...")
            upload_to_threads(video_file, description)
            results['Threads'] = "✅ Success"
        except Exception as e:
            print(f"❌ Threads Failed: {e}")
            results['Threads'] = f"❌ Failed: {str(e)[:50]}..."
    else:
        results['Threads'] = "⏭️  Skipped (Missing Token)"

    # --- TikTok ---
    if os.getenv('TIKTOK_ACCESS_TOKEN'):
        try:
            print("\n🎵 Uploading to TikTok...")
            tiktok_result = upload_to_tiktok(video_file, social_title, description) 
            if tiktok_result:
                results['TikTok'] = "✅ Success"
            else:
                results['TikTok'] = "❌ Failed (Check logs)"
        except Exception as e:
            print(f"❌ TikTok Failed: {e}")
            results['TikTok'] = f"❌ Failed: {str(e)[:50]}..."
    else:
        results['TikTok'] = "⏭️  Skipped (Missing Token)"
        
    # --- Twitter / X ---
    twitter_vars = ['TWITTER_API_KEY', 'TWITTER_API_SECRET', 'TWITTER_ACCESS_TOKEN', 'TWITTER_ACCESS_SECRET']
    if all(os.getenv(var) for var in twitter_vars):
        try:
            print("\n🐦 Uploading to Twitter...")
            upload_to_twitter(video_file, description)
            results['Twitter/X'] = "✅ Success"
        except Exception as e:
            print(f"❌ Twitter Failed: {e}")
            results['Twitter/X'] = f"❌ Failed: {str(e)[:50]}..."
    else:
        results['Twitter/X'] = "⏭️  Skipped (Missing Credentials)"

    # --- Telegram ---
    if os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('TELEGRAM_CHANNEL_ID'):
        try:
            print("\n✈️ Uploading to Telegram...")
            upload_to_telegram(video_file, description)
            results['Telegram'] = "✅ Success"
        except Exception as e:
            print(f"❌ Telegram Failed: {e}")
            results['Telegram'] = f"❌ Failed: {str(e)[:50]}..."
    else:
        results['Telegram'] = "⏭️  Skipped (Missing Token)"

    # --- VK ---
    if os.getenv('VK_ACCESS_TOKEN') and os.getenv('VK_GROUP_ID'):
        try:
            print("\n🇷🇺 Uploading to VK...")
            upload_to_vk(video_file, description, social_title)
            results['VK'] = "✅ Success"
        except Exception as e:
            print(f"❌ VK Failed: {e}")
            results['VK'] = f"❌ Failed: {str(e)[:50]}..."
    else:
        results['VK'] = "⏭️  Skipped (Missing Token)"

    # --- Final Summary ---
    print("\n" + "="*40)
    print("📢 FINAL PUBLISHING SUMMARY")
    print("="*40)
    for platform, status in results.items():
        print(f"{platform:<12} : {status}")
    print("="*40)

if __name__ == '__main__':
    main()
