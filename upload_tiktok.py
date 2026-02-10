"""
TikTok Upload

TikTok Content Posting API for uploading videos.
Requires: TikTok Developer account + OAuth
"""

import os
import requests

def upload_to_tiktok(video_file, title, description):
    """Upload video to TikTok."""
    
    access_token = os.getenv('TIKTOK_ACCESS_TOKEN')
    
    if not access_token:
        raise ValueError("Missing TIKTOK_ACCESS_TOKEN")

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    print(f"[tiktok] Uploading: {video_file}")
    
    # 1. Init
    init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
    init_body = {
        "post_info": {
            "title": title[:150],
            "description": description[:1000],
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
            "video_cover_timestamp_ms": 1000
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": os.path.getsize(video_file),
            "chunk_size": os.path.getsize(video_file),
            "total_chunk_count": 1
        }
    }
    
    resp = requests.post(init_url, headers=headers, json=init_body)
    
    if resp.status_code != 200:
        print(f"[tiktok] Init failed: {resp.text}")
        return None
        
    data = resp.json().get('data')
    if not data:
        print("[tiktok] No data in init response")
        return None
        
    upload_url = data['upload_url']
    publish_id = data['publish_id']
    
    # 2. Upload
    with open(video_file, 'rb') as f:
        requests.put(upload_url, data=f, headers={'Content-Type': 'video/mp4'})
        
    print(f"[tiktok] ✅ Uploaded! Publish ID: {publish_id}")
    return {'id': publish_id}

# Note: TikTok official API is restrictive. 
# Consider using `tiktok-uploader` (Selenium based) for personal accounts.
