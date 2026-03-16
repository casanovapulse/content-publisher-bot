"""
Dropbox Integration Module with Auto Token Refresh
Uses refresh token to get new access tokens automatically for automation.
"""
import os
import json
import dropbox
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_FOLDER = os.getenv("DROPBOX_FOLDER", "/margot")
LOCAL_INPUT_DIR = os.getenv("LOCAL_INPUT_DIR", "Videos")

PUBLISHED_LOG = "published_videos.json"


def get_published_videos():
    """Get list of already published video names."""
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # Extract video names from the log
                return [item.get('video_name', '') for item in data]
            except json.JSONDecodeError:
                return []
    return []


def get_all_published_data():
    """Get full published data including metadata and publish count."""
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_dropbox_client():
    """Initialize and return Dropbox client with refresh token."""
    if DROPBOX_REFRESH_TOKEN and DROPBOX_APP_KEY and DROPBOX_APP_SECRET:
        dbx = dropbox.Dropbox(
            app_key=DROPBOX_APP_KEY,
            app_secret=DROPBOX_APP_SECRET,
            oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
        )
        print("Dropbox initialized with refresh token (NEVER EXPIRES)")
        return dbx
    elif DROPBOX_ACCESS_TOKEN:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        print("Dropbox initialized with access token (expires in 4 hours)")
        return dbx
    else:
        raise ValueError("No Dropbox credentials found")


def list_dropbox_videos(dbx):
    """List all video files in the Dropbox folder."""
    try:
        entries = dbx.files_list_folder(DROPBOX_FOLDER).entries
        video_extensions = ('.mp4', '.mov', '.avi', '.mkv')
        videos = [
            entry for entry in entries
            if entry.name.lower().endswith(video_extensions)
        ]
        return videos
    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox API error: {e}")
        return []


def download_video(dbx, entry, local_path):
    """Download a video from Dropbox to local storage."""
    try:
        dbx.files_download_to_file(local_path, f"{DROPBOX_FOLDER}/{entry.name}")
        print(f"Downloaded: {entry.name}")
        return True
    except dropbox.exceptions.ApiError as e:
        print(f"Failed to download {entry.name}: {e}")
        return False


def fetch_all_videos_from_dropbox():
    """
    Fetch ALL NEW videos from Dropbox for processing.
    Checks published_videos.json to skip already processed videos.

    If no new videos in Dropbox, returns empty list (pipeline will fallback to local videos).

    Returns:
        List of paths to downloaded videos (can be empty)
    """
    # Ensure local input directory exists
    Path(LOCAL_INPUT_DIR).mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("FETCHING ALL VIDEOS FROM DROPBOX")
    print("=" * 60)

    # Get list of already published videos
    published = get_published_videos()
    print(f"Already published: {len(published)} video(s)")
    if published:
        for vid in published[:3]:  # Show first 3
            print(f"  - {vid}")
        if len(published) > 3:
            print(f"  ... and {len(published) - 3} more")

    try:
        dbx = get_dropbox_client()
    except ValueError as e:
        print(f"Error: {e}")
        return []

    videos = list_dropbox_videos(dbx)

    if not videos:
        print("No videos found in Dropbox folder.")
        return []

    print(f"\nFound {len(videos)} video(s) in Dropbox.")

    # Download all videos NOT in published list
    downloaded = []
    for entry in videos:
        video_name = entry.name

        # Check if already published
        if video_name in published:
            print(f"Skipping {video_name} - already published")
            continue

        # Download this video
        local_path = os.path.join(LOCAL_INPUT_DIR, video_name)
        if download_video(dbx, entry, local_path):
            print(f"✅ Downloaded: {video_name}")
            downloaded.append(local_path)

    if downloaded:
        print(f"\n✅ Total: {len(downloaded)} video(s) downloaded")
    else:
        print("\n⚠️  No new videos in Dropbox. Will fallback to local processed videos.")
    
    return downloaded


def fetch_one_video_from_dropbox():
    """
    Fetch ONE NEW video from Dropbox for processing.
    Checks published_videos.json to skip already processed videos.

    If no new videos in Dropbox, returns None (pipeline will fallback to local videos).

    Returns:
        Path to downloaded video or None
    """
    # Ensure local input directory exists
    Path(LOCAL_INPUT_DIR).mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("FETCHING VIDEO FROM DROPBOX")
    print("=" * 60)

    # Get list of already published videos
    published = get_published_videos()
    print(f"Already published: {len(published)} video(s)")
    if published:
        for vid in published[:3]:  # Show first 3
            print(f"  - {vid}")
        if len(published) > 3:
            print(f"  ... and {len(published) - 3} more")

    try:
        dbx = get_dropbox_client()
    except ValueError as e:
        print(f"Error: {e}")
        return None

    videos = list_dropbox_videos(dbx)

    if not videos:
        print("No videos found in Dropbox folder.")
        return None

    print(f"\nFound {len(videos)} video(s) in Dropbox.")

    # Find first video NOT in published list
    for entry in videos:
        video_name = entry.name

        # Check if already published
        if video_name in published:
            print(f"Skipping {video_name} - already published")
            continue

        # Download this video
        local_path = os.path.join(LOCAL_INPUT_DIR, video_name)
        if download_video(dbx, entry, local_path):
            print(f"\n✅ Selected: {video_name}")
            return local_path

    print("\n⚠️  No new videos in Dropbox. Will fallback to local processed videos.")
    return None


if __name__ == "__main__":
    # Test the Dropbox connection
    fetch_one_video_from_dropbox()
