"""
Instagram Reels Upload - Direct Resumable Upload via Meta API
Uses rupload.facebook.com for direct binary upload (no URL hosting needed)
"""

import os
import json
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def upload_to_instagram(video_path, caption, is_story=False):
    """
    Upload video to Instagram via resumable upload (direct binary).
    No external URL hosting needed.
    """
    media_type = 'STORIES' if is_story else 'REELS'
    
    print("\n" + "=" * 60)
    print(f"📸 INSTAGRAM {media_type} UPLOAD STARTING")
    print("=" * 60)
    
    # Get credentials
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN') or os.getenv('FACEBOOK_ACCESS_TOKEN')
    user_id = os.getenv('INSTAGRAM_ACCOUNT_ID') or os.getenv('IG_USER_ID')
    
    def mask(s): return f"{s[:10]}...{s[-4:]}" if s and len(s) > 10 else ("PLACEHOLDER" if s == "***" else "MISSING")
    print(f"[instagram] User ID Provided: {user_id}")
    print(f"[instagram] Access Token: {mask(access_token)}")

    if not access_token:
        raise ValueError("❌ INSTAGRAM_ACCESS_TOKEN not set")
    
    if not user_id:
        raise ValueError("❌ INSTAGRAM_ACCOUNT_ID not set")
    
    print(f"[instagram] ✅ Credentials loaded")
    
    # Check video file
    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        raise FileNotFoundError(f"❌ Video file not found: {video_path}")
    
    file_size_mb = video_path_obj.stat().st_size / (1024 * 1024)
    print(f"[instagram] ✅ Video file found: {video_path}")
    print(f"[instagram] Video size: {file_size_mb:.2f} MB")
    
    # Limit caption
    caption_limited = caption[:2200] if len(caption) > 2200 else caption
    print(f"[instagram] Caption length: {len(caption_limited)} characters")
    
    try:
        # Step 1: Start resumable upload session
        print(f"[instagram] 📤 Step 1: Starting resumable upload session...")
        
        start_url = f"https://graph.facebook.com/v21.0/{user_id}/media"
        start_params = {
            'upload_type': 'resumable',
            'access_token': access_token,
            'media_type': media_type
        }
        if not is_story:
            start_params['caption'] = caption_limited
        
        start_response = requests.post(start_url, params=start_params, timeout=30)
        
        if start_response.status_code != 200:
            error_data = start_response.json() if start_response.text else {}
            error_msg = error_data.get('error', {}).get('message', '')
            error_code = error_data.get('error', {}).get('code', '')
            print(f"[instagram] ❌ Resumable upload init failed: [{error_code}] {error_msg}")
            print(f"[instagram] Full response: {start_response.text[:500]}")
            
            # Fallback: try without upload_type
            print(f"[instagram] 🔄 Trying standard upload...")
            std_params = {
                'access_token': access_token,
                'media_type': media_type
            }
            if not is_story:
                std_params['caption'] = caption_limited
            start_response = requests.post(start_url, params=std_params, timeout=30)
            
            if start_response.status_code != 200:
                err2 = start_response.json().get('error', {}).get('message', '')
                raise Exception(f"Upload init failed: {err2}")
            
            # Standard upload returns container ID directly
            container_id = start_response.json().get('id')
            print(f"[instagram] ✅ Standard container created: {container_id}")
            
            # For standard upload, we need a video_url. Use tmpfiles fallback
            print(f"[instagram] ⚠️ Standard upload needs video_url, trying fallback...")
            raise Exception("Need to use video_url - not supported without upload_type=resumable")
        
        # Resumable upload returns upload_url for binary upload
        start_data = start_response.json()
        upload_url = start_data.get('upload_url')
        container_id = start_data.get('id')
        
        if not upload_url:
            raise Exception(f"No upload_url in response: {start_data}")
        
        print(f"[instagram] ✅ Upload session started")
        print(f"[instagram] Upload URL: {upload_url[:50]}...")
        print(f"[instagram] Container ID: {container_id}")
        
        # Step 2: Upload video binary to rupload.facebook.com
        print(f"[instagram] 🚀 Step 2: Uploading video binary ({file_size_mb:.2f} MB)...")
        
        with open(video_path_obj, 'rb') as video_file:
            upload_response = requests.post(
                upload_url,
                data=video_file.read(),
                headers={
                    'Authorization': f'OAuth {access_token}',
                    'Content-Type': 'application/octet-stream',
                    'Content-Length': str(video_path_obj.stat().st_size)
                },
                timeout=300
            )
        
        if upload_response.status_code != 200:
            print(f"[instagram] ❌ Binary upload failed: HTTP {upload_response.status_code}")
            print(f"[instagram] Response: {upload_response.text[:300]}")
            raise Exception(f"Binary upload failed: HTTP {upload_response.status_code}")
        
        print(f"[instagram] ✅ Video uploaded to Meta servers!")
        
        # Step 3: Publish immediately (no polling needed!)
        print(f"[instagram] 📤 Step 3: Publishing to Instagram...")
        
        publish_url = f"https://graph.facebook.com/v21.0/{user_id}/media_publish"
        publish_params = {
            'creation_id': container_id,
            'access_token': access_token
        }
        
        publish_response = requests.post(publish_url, params=publish_params, timeout=60)
        
        if publish_response.status_code != 200:
            error_data = publish_response.json() if publish_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"[instagram] ❌ Publish failed: {error_msg}")
            
            # Try with instagram endpoint
            print(f"[instagram] 🔄 Retrying with Instagram endpoint...")
            pub_url2 = f"https://graph.instagram.com/v21.0/{user_id}/media_publish"
            publish_response = requests.post(pub_url2, params=publish_params, timeout=60)
            
            if publish_response.status_code != 200:
                err2 = publish_response.json().get('error', {}).get('message', '')
                raise Exception(f"Publish failed after retries: {err2}")
        
        media_id = publish_response.json().get('id')
        
        print(f"[instagram] ✅ SUCCESS! Video published to Instagram!")
        print(f"[instagram] Media ID: {media_id}")
        print(f"[instagram] Check your Instagram profile to see the post!")
        print("=" * 60)
        
        return {
            'id': media_id,
            'platform': 'instagram',
            'status': 'success'
        }
        
    except Exception as e:
        print(f"[instagram] ❌ ERROR!")
        print(f"[instagram] {str(e)}")
        print("=" * 60)
        raise


if __name__ == '__main__':
    video_file = Path('ielts_short.mp4')
    if video_file.exists():
        try:
            result = upload_to_instagram(str(video_file), "Test upload #Test")
            print(f"\n✅ Success! Result: {result}")
        except Exception as e:
            print(f"\n❌ Failed: {e}")
    else:
        print(f"❌ Video not found: {video_file}")