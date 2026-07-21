"""
Main Automation Pipeline for GitHub Actions
1. Fetch videos from Dropbox (all available)
2. Process (upscale + remove watermark)
3. Upload ALL videos to social media platforms

SMART FALLBACK: If no new videos in Dropbox, uses ALL existing processed videos
from Processed_Videos folder, posting them one after another in rotation.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()


def run_pipeline():
    """
    Complete automation pipeline:
    Dropbox → Process → Upload to Social Media

    Priority:
    1. If new videos in Dropbox → download ALL, process ALL, upload ALL
    2. If no new videos → fallback to ALL existing processed videos (least published first)
    
    CONTINUOUS MODE: Processes and posts ALL available videos in one run,
    ensuring continuous content until new videos are added.
    """
    print("\n" + "=" * 60)
    print("🚀 STARTING AUTOMATION PIPELINE (CONTINUOUS MODE)")
    print("=" * 60 + "\n")

    # Step 1: Fetch ALL videos from Dropbox
    print("📥 STEP 1: Fetching videos from Dropbox...")
    from dropbox_fetch import fetch_all_videos_from_dropbox

    downloaded_videos = fetch_all_videos_from_dropbox()

    if not downloaded_videos:
        print("\n⚠️  No new videos in Dropbox.")
        print("   Will use ALL existing processed videos from Processed_Videos folder.")
        print("   Posting all videos in rotation (least published first)...\n")
        
        # Post ALL existing processed videos one by one
        from daily_publisher import get_least_published_video
        import glob
        
        PROCESSED_DIR = "Processed_Videos"
        all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))
        if all_videos:
            print(f"📚 Found {len(all_videos)} existing processed videos.")
            print("   Will post each video one by one...\n")
            
            # Keep posting until all videos are published
            for i in range(len(all_videos)):
                vid_path, vid_name = get_least_published_video(all_videos)
                if not vid_path:
                    print("\n⚠️  No more videos to post.")
                    break
                    
                print(f"\n🎬 Posting video {i+1}/{len(all_videos)}: {vid_name}")
                sys.argv = ["daily_publisher.py", vid_path]
                publish_video()
                print(f"✅ Posted: {vid_name}")
                
                # Remove posted video from the list so we don't repeat
                all_videos.remove(vid_path)
        else:
            print("\n❌ No processed videos found in Processed_Videos folder!")
            print("   Please add videos to Dropbox or Processed_Videos folder.")
        return
    else:
        print(f"\n✅ Step 1 complete: {len(downloaded_videos)} video(s) downloaded\n")

    # Step 2: Process ALL videos (upscale + watermark removal)
    print("🎬 STEP 2: Processing videos (upscaling + watermark removal)...")
    from process_videos import process_all_videos

    processed_videos = process_all_videos(downloaded_videos)

    if not processed_videos:
        print("\n❌ No videos to process!")
        # Try fallback to existing processed videos
        from daily_publisher import main as publish_video
        sys.argv = ["daily_publisher.py", "--fallback-all"]
        publish_video()
        return

    print(f"\n✅ Step 2 complete: {len(processed_videos)} video(s) processed\n")

    # Step 3: Upload ALL videos to social media
    print("📤 STEP 3: Uploading ALL videos to social media platforms...")
    print("   Platforms: Instagram, Facebook, Threads, YouTube")
    print(f"   Total videos to post: {len(processed_videos)}")
    print("\n" + "=" * 60 + "\n")

    # Run the daily publisher with ALL processed videos
    from daily_publisher import main as publish_video
    for vid in processed_videos:
        sys.argv = ["daily_publisher.py", vid]
        publish_video()
        print(f"\n✅ Posted: {os.path.basename(vid)}\n")

    print("\n" + "=" * 60)
    print(f"🎉 AUTOMATION PIPELINE COMPLETE - {len(processed_videos)} VIDEO(S) POSTED")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()

