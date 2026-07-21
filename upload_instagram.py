"""
Instagram Reels Upload - Using tmpfiles.org for Public URL
Uploads video to tmpfiles.org, then uses URL for Instagram API
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
    Upload video to Instagram via temporary public URL.
    Can be a Reel or a Story.
    """
    media_type = 'STORIES' if is_story else 'REELS'
    
    print("\n" + "=" * 60)
    print(f"📸 INSTAGRAM {media_type} UPLOAD STARTING")
    print("=" * 60)
    
    # Get credentials with fallbacks
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN') or os.getenv('FACEBOOK_ACCESS_TOKEN')
    user_id = os.getenv('INSTAGRAM_ACCOUNT_ID') or os.getenv('IG_USER_ID')
    
    # Debug info (masked)
    def mask(s): return f"{s[:10]}...{s[-4:]}" if s and len(s) > 10 else ("PLACEHOLDER" if s == "***" else "MISSING")
    print(f"[instagram] User ID Provided: {user_id}")
    print(f"[instagram] Access Token: {mask(access_token)}")

    if not access_token:
        raise ValueError("❌ INSTAGRAM_ACCESS_TOKEN not set")
    
    # AUTO-DETECTION: If token is IGAA (Personal/Standard), the ID might be different
    if access_token.startswith('IGAA'):
        print("[instagram] 🔍 Detected 'IGAA' token (Instagram Basic/Standard API)")
        print("[instagram] Fetching correct ID for this token...")
        try:
            # Use graph.facebook.com instead of graph.instagram.com for better compatibility
            me_resp = requests.get(f"https://graph.facebook.com/me?fields=id,username&access_token={access_token}", timeout=10)
            if me_resp.status_code == 200:
                me_data = me_resp.json()
                detected_id = me_data.get('id')
                if detected_id and detected_id != user_id:
                    print(f"[instagram] ⚠️  ID Mismatch! Provided: {user_id}, Detected: {detected_id}")
                    print(f"[instagram] 🔄 Using detected ID: {detected_id}")
                    user_id = detected_id
            else:
                print(f"[instagram] ⚠️  Could not verify token: {me_resp.text}")
        except Exception as e:
            print(f"[instagram] ⚠️  Error during ID verification: {e}")

    if not user_id:
        raise ValueError("❌ INSTAGRAM_ACCOUNT_ID not set")
    
    print(f"[instagram] ✅ Credentials loaded")
    
    # Check video file
    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        error_msg = f"❌ Video file not found: {video_path}"
        print(f"[instagram] {error_msg}")
        raise FileNotFoundError(error_msg)
    
    file_size_mb = video_path_obj.stat().st_size / (1024 * 1024)
    print(f"[instagram] ✅ Video file found: {video_path}")
    print(f"[instagram] Video size: {file_size_mb:.2f} MB")
    
    # Limit caption
    caption_limited = caption[:2200] if len(caption) > 2200 else caption
    print(f"[instagram] Caption length: {len(caption_limited)} characters")
    
    try:
        # Step 1: Upload to a temporary hosting service to get a public URL
        # Instagram Graph API requires video_url parameter for media creation
        print(f"[instagram] 📤 Step 1: Uploading video to temporary hosting...")
        
        # Try multiple temporary hosting services for reliability
        video_url = None
        hosting_services = [
            {
                'name': 'tmpfiles.org',
                'url': 'https://tmpfiles.org/api/v1/upload',
                'parse': lambda r: r.json().get('data', {}).get('url', '').replace('tmpfiles.org/', 'tmpfiles.org/dl/')
            },
        ]
        
        # Upload to hosting
        for service in hosting_services:
            try:
                with open(video_path_obj, 'rb') as video_file:
                    files = {'file': ('video.mp4', video_file, 'video/mp4')}
                    resp = requests.post(service['url'], files=files, timeout=180)
                
                if resp.status_code == 200:
                    parsed_url = service['parse'](resp)
                    if parsed_url:
                        video_url = parsed_url
                        print(f"[instagram] ✅ Uploaded via {service['name']}: {video_url}")
                        break
            except Exception as e:
                print(f"[instagram] ⚠️ {service['name']} failed: {e}")
                continue
        
        if not video_url:
            # Last resort: try file.io
            try:
                with open(video_path_obj, 'rb') as video_file:
                    resp = requests.post('https://file.io', files={'file': video_file}, timeout=180)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('success'):
                        video_url = data['link']
                        print(f"[instagram] ✅ Uploaded via file.io: {video_url}")
            except Exception as e:
                print(f"[instagram] ⚠️ file.io failed: {e}")
        
        if not video_url:
            raise Exception("Failed to upload video to any temporary hosting service")
        
        # Step 2: Create Instagram container with video URL
        # Try creating container with retry logic
        print(f"[instagram] 📦 Step 2: Creating Instagram {media_type} container...")
        
        container_id = None
        container_url = f"https://graph.facebook.com/v21.0/{user_id}/media"
        
        for attempt in range(3):
            with open(video_path_obj, 'rb') as video_file:
                files = {'file': ('video.mp4', video_file, 'video/mp4')}
                temp_resp = requests.post('https://tmpfiles.org/api/v1/upload', files=files, timeout=180)
            
            if temp_resp.status_code == 200:
                new_url = temp_resp.json().get('data', {}).get('url', '').replace('tmpfiles.org/', 'tmpfiles.org/dl/')
                if new_url:
                    video_url = new_url
            
            container_params = {
                'media_type': media_type,
                'video_url': video_url,
                'access_token': access_token
            }
            
            if not is_story:
                container_params['caption'] = caption_limited
                container_params['share_to_feed'] = 'false'
            
            container_response = requests.post(container_url, params=container_params, timeout=60)
            
            if container_response.status_code == 200:
                container_id = container_response.json().get('id')
                print(f"[instagram] ✅ Container created (attempt {attempt+1}): {container_id}")
                break
            else:
                error_msg = container_response.json().get('error', {}).get('message', 'Unknown error')
                print(f"[instagram] ⚠️ Container attempt {attempt+1} failed: {error_msg}")
                if attempt < 2:
                    import random
                    time.sleep(5 + random.randint(1, 5))
        
        if not container_id:
            # Final fallback: try graph.instagram.com endpoint
            print(f"[instagram] 🔄 Trying Instagram Graph API endpoint as last resort...")
            insta_url = f"https://graph.instagram.com/v21.0/{user_id}/media"
            
            with open(video_path_obj, 'rb') as video_file:
                files = {'file': ('video.mp4', video_file, 'video/mp4')}
                temp_resp = requests.post('https://tmpfiles.org/api/v1/upload', files=files, timeout=180)
            
            if temp_resp.status_code == 200:
                video_url = temp_resp.json().get('data', {}).get('url', '').replace('tmpfiles.org/', 'tmpfiles.org/dl/')
            
            insta_params = {
                'media_type': media_type,
                'video_url': video_url,
                'access_token': access_token,
                'caption': caption_limited
            }
            container_response = requests.post(insta_url, params=insta_params, timeout=60)
            
            if container_response.status_code == 200:
                container_id = container_response.json().get('id')
                print(f"[instagram] ✅ Container created via Instagram API: {container_id}")
            else:
                err = container_response.json().get('error', {}).get('message', 'Unknown')
                raise Exception(f"Failed to create Instagram container. Error: {err}")
        
        print(f"[instagram] ✅ Container created: {container_id}")
        
        # Step 3: Wait for processing with retry logic
        # Instagram sometimes gives ERROR on first try but works on retry with fresh upload
        max_processing_attempts = 2
        processing_success = False
        
        for processing_attempt in range(max_processing_attempts):
            print(f"[instagram] ⏳ Step 3: Checking video processing status (attempt {processing_attempt+1})...")
            max_wait = 180
            waited = 0
            poll_interval = 15
            status_check_broken = False
            
            while waited < max_wait:
                    status_url = f"https://graph.facebook.com/v21.0/{container_id}"
                    status_params = {
                        'fields': 'status_code',
                        'access_token': access_token
                    }
                    
                    try:
                        status_response = requests.get(status_url, params=status_params, timeout=(10, 20))
                    except Exception:
                        status_response = None
                    
                    if not status_response or status_response.status_code != 200:
                        try:
                            status_url = f"https://graph.instagram.com/v21.0/{container_id}"
                            status_response = requests.get(status_url, params=status_params, timeout=(10, 20))
                        except Exception:
                            pass
                    
                    status_data = status_response.json() if status_response else {}
                    status_code = status_data.get('status_code', 'UNKNOWN')
                    
                    is_auth_error = False
                    if status_data and 'error' in status_data:
                        error_code = status_data['error'].get('code', 0)
                        error_subcode = status_data['error'].get('error_subcode', 0)
                        error_message = status_data['error'].get('message', '')
                        print(f"[instagram] Status check error: code={error_code}, subcode={error_subcode}, msg={error_message}")
                        if error_subcode == 33 or error_code == 100:
                            is_auth_error = True
                            if not status_check_broken:
                                print(f"[instagram] Status endpoint not accessible (auth issue). Using fixed 60s delay.")
                                status_check_broken = True
                    
                    if is_auth_error:
                        waited += poll_interval
                        if waited >= 60:
                            print(f"[instagram] Auth error persisted, proceeding to publish after {waited}s")
                            break
                        time.sleep(poll_interval)
                        continue
                    
                    print(f"[instagram] Status: {status_code} (waited {waited}s)")
                    
                    if status_code == 'FINISHED':
                        print(f"[instagram] ✅ Video processing complete!")
                        processing_success = True
                        break
                    elif status_code == 'ERROR':
                        error_msg = status_data.get('error_message', '')
                        if not error_msg:
                            error_msg = status_data.get('error', {}).get('message', '')
                        if not error_msg:
                            error_msg = status_data.get('status_detail', '')
                        if not error_msg:
                            error_msg = 'Video processing failed (no details from Instagram API)'
                        print(f"[instagram] ❌ {error_msg}")
                        print(f"[instagram] Full status response: {json.dumps(status_data, indent=2)[:500]}")
                        
                        if processing_attempt < max_processing_attempts - 1:
                            print(f"[instagram] 🔄 Retrying with a fresh container...")
                            time.sleep(5)
                            with open(video_path_obj, 'rb') as vf:
                                tf = {'file': ('video.mp4', vf, 'video/mp4')}
                                new_temp = requests.post('https://tmpfiles.org/api/v1/upload', files=tf, timeout=180)
                            if new_temp.status_code == 200:
                                new_url = new_temp.json().get('data', {}).get('url', '').replace('tmpfiles.org/', 'tmpfiles.org/dl/')
                                new_params = {
                                    'media_type': media_type,
                                    'video_url': new_url,
                                    'access_token': access_token,
                                    'caption': caption_limited
                                }
                                if not is_story:
                                    new_params['share_to_feed'] = 'false'
                                retry_resp = requests.post(container_url, params=new_params, timeout=60)
                                if retry_resp.status_code == 200:
                                    container_id = retry_resp.json().get('id')
                                    print(f"[instagram] ✅ New container created: {container_id}")
                                    break  # Break inner while, outer for will retry
                                else:
                                    err = retry_resp.json().get('error', {}).get('message', '')
                                    print(f"[instagram] ⚠️ Retry container failed: {err}")
                        if processing_attempt >= max_processing_attempts - 1:
                            raise Exception(error_msg)
                        break  # Break while to retry from outer for loop
                    elif status_code == 'UNKNOWN' and waited >= 120:
                        print(f"[instagram] Still UNKNOWN after {waited}s, publishing anyway...")
                        break
                    
                    time.sleep(poll_interval)
                    waited += poll_interval
        
        if not processing_success and waited >= max_wait:
            print(f"[instagram] Max wait reached, attempting to publish anyway...")
            processing_success = True
        
        if not processing_success:
            raise Exception("Instagram video processing failed after all retries")
        
        # Step 4: Publish
        print(f"[instagram] 📤 Step 4: Publishing to Instagram... (Adding 5s buffer)")
        time.sleep(5) # Small buffer because IG sometimes says FINISHED before it's actually ready
        
        # Use graph.facebook.com as primary endpoint for publishing
        publish_url = f"https://graph.facebook.com/v21.0/{user_id}/media_publish"
        publish_params = {
            'creation_id': container_id,
            'access_token': access_token
        }
        
        # Robust Retry Logic for Publishing
        max_publish_retries = 3
        publish_response = None
        
        for attempt in range(max_publish_retries):
            publish_response = requests.post(publish_url, params=publish_params, timeout=60)
            
            if publish_response.status_code == 200:
                break
            else:
                print(f"[instagram] ⚠️ Publish attempt {attempt+1} failed. Retrying...")
                time.sleep(10)
            
            # Fallback to instagram.com if facebook.com consistently fails
            if attempt == max_publish_retries - 1:
                publish_url = f"https://graph.instagram.com/v21.0/{user_id}/media_publish"
                publish_response = requests.post(publish_url, params=publish_params, timeout=60)
        
        if not publish_response or publish_response.status_code != 200:
            error_data = publish_response.json() if publish_response and publish_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"[instagram] ❌ Publish failed after retries: {error_msg}")
            raise Exception(f"Instagram Publish Error: {error_msg}")
        
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
            result = upload_to_instagram(str(video_file), "IELTS Band 9 Upgrade! #IELTS #English")
            print(f"\n✅ Success! Result: {result}")
        except Exception as e:
            print(f"\n❌ Failed: {e}")
    else:
        print(f"❌ Video not found: {video_file}")

