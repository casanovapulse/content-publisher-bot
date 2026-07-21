import time
import os
import shutil
from datetime import datetime
from generate_content import generate_full_cycle
from assemble_video import assemble_video

def run_bot():
    print("Starting IELTS Zoom Automation Bot...")
    
    if not os.path.exists("final_videos"):
        os.makedirs("final_videos")
        
    while True:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"\n[{timestamp}] Starting new content generation cycle...")
        
        try:
            # 1. Generate Content (Script, Audio, Images)
            content = generate_full_cycle()
            
            if content and content.get('script'):
                script = content['script']
                print(f"Generated Topic: {script.get('title', 'Unknown')}")
                
                # Log the idea
                with open("content_idea_log.txt", "a") as f:
                    f.write(f"[{timestamp}] {script.get('title')} - {script.get('hook')}\n")
                
                # 2. Assemble Video
                print("Assembling video...")
                assemble_video()
                
                # 3. Save Final Output
                if os.path.exists("ielts_short.mp4"):
                    final_path = os.path.join("final_videos", f"ielts_short_{timestamp}.mp4")
                    shutil.move("ielts_short.mp4", final_path)
                    print(f"Video saved to: {final_path}")
                else:
                    print("Error: Video file not found after assembly.")
                    
            else:
                print("Content generation failed. Retrying in 5 minutes...")
                time.sleep(300)
                continue
                
        except Exception as e:
            print(f"An error occurred: {e}")
            
        # Wait for next cycle
        interval_seconds = 3600 # Every 1 hour
        print(f"Cycle Complete. Sleeping for {interval_seconds} seconds...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_bot()

