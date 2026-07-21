"""
Video Processor - Quality Enhancement (Video + Audio)
1. Upscale video to 1080x1920 with quality enhancement
2. Remove watermark (bottom-right corner)
3. ENHANCE AUDIO (normalize volume, improve clarity) - if audio exists
"""
import os
import subprocess
import sys
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

input_dir = "Videos"
output_dir = "Processed_Videos"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)


def process_single_video(video_path):
    if not os.path.exists(video_path):
        print(f"Error: Video not found: {video_path}")
        return None

    filename = os.path.basename(video_path)
    out_path = os.path.join(output_dir, filename)

    if os.path.exists(out_path):
        print(f"Skipping {filename} - already processed")
        return out_path

    cmd_probe = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
        video_path
    ]
    try:
        res = subprocess.check_output(cmd_probe).decode("utf-8").strip()
        width, height = map(int, res.split("x"))
    except Exception as e:
        print(f"Failed to get resolution for {video_path}: {e}")
        return None

    cmd_audio = [
        "ffprobe", "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_type",
        "-of", "csv=p=0",
        video_path
    ]
    try:
        audio_check = subprocess.check_output(cmd_audio).decode("utf-8").strip()
        has_audio = bool(audio_check)
    except:
        has_audio = False

    print(f"Original size: {width}x{height}")
    print(f"Has audio: {'Yes' if has_audio else 'No'}")

    # Get video duration
    cmd_duration = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    try:
        duration = float(subprocess.check_output(cmd_duration).decode("utf-8").strip())
        print(f"Video duration: {duration:.2f} seconds")
    except Exception as e:
        print(f"Failed to get duration: {e}")
        duration = None

    # Loop video if under 10 seconds
    loop_video = duration is not None and duration < 10
    if loop_video:
        print(f"⚠️  Video is under 10 seconds ({duration:.2f}s). Will loop to extend duration.")

    w_delogo = 180
    h_delogo = 80
    x_delogo = 1080 - w_delogo - 5
    y_delogo = 1920 - h_delogo - 5

    print(f"Processing {filename}...")
    print(f"  Upscaling to: 1080x1920")
    print(f"  Removing watermark at: x={x_delogo}, y={y_delogo}, w={w_delogo}, h={h_delogo}")
    if loop_video:
        print(f"  Looping: Video will be doubled (6s + 6s = 12s)")
    print(f"  Video: ENHANCED (sharpen + clarity boost)")
    if has_audio:
        print(f"  Audio: ENHANCED (normalize volume + improve clarity)")
    else:
        print(f"  Audio: No audio in original video")

    if loop_video:
        # Loop video to double the duration using loop filter
        # loop=1: start=0 means play once, then loop once more (total 2x)
        vf_filter = f"[0:v]scale=1080:1920:flags=lanczos,unsharp=5:5:1.0:5:5:0.0,cas=0.7,delogo=x={x_delogo}:y={y_delogo}:w={w_delogo}:h={h_delogo},loop=1:start=0[v]"
    else:
        vf_filter = f"[0:v]scale=1080:1920:flags=lanczos,unsharp=5:5:1.0:5:5:0.0,cas=0.7,delogo=x={x_delogo}:y={y_delogo}:w={w_delogo}:h={h_delogo}[v]"

    if has_audio:
        if loop_video:
            # Loop audio to match video (loop=1 means play twice total)
            af_filter = f"[0:a]loudnorm=I=-16:TP=-1.5:LRA=11,dynaudnorm=50:3:0.5,aloop=1:start=0[a]"
        else:
            af_filter = f"[0:a]loudnorm=I=-16:TP=-1.5:LRA=11,dynaudnorm=50:3:0.5[a]"

        cmd_ffmpeg = [
            "ffmpeg", "-y", "-i", video_path,
            "-filter_complex", f"{vf_filter};{af_filter}",
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264", "-preset", "slow", "-crf", "16",
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            out_path
        ]
    else:
        cmd_ffmpeg = [
            "ffmpeg", "-y", "-i", video_path,
            "-filter_complex", vf_filter,
            "-map", "[v]",
            "-c:v", "libx264", "-preset", "slow", "-crf", "16",
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-an",
            out_path
        ]

    print("  Processing... (enhancement in progress)")
    result = subprocess.run(cmd_ffmpeg, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Saved: {out_path} (ENHANCED)")
        return out_path
    else:
        print(f"❌ Failed to process video")
        print(f"   FFmpeg error output:")
        # Print error in chunks to avoid truncation
        error_lines = result.stderr.split('\n')
        for line in error_lines[:30]:  # Print first 30 lines of error
            if line.strip():
                print(f"   {line}")
        return None


def process_all_videos(video_list=None):
    """
    Process multiple videos.
    
    Args:
        video_list: List of video paths to process. If None, processes all in Videos folder.
    
    Returns:
        List of processed video paths
    """
    processed = []
    
    if video_list:
        # Process specific videos from the list
        for vid_path in video_list:
            result = process_single_video(vid_path)
            if result:
                processed.append(result)
    else:
        # Process all videos in input directory
        videos = [f for f in os.listdir(input_dir) if f.endswith('.mp4')]
        print(f"Found {len(videos)} videos to process.")

        for filename in videos:
            vid_path = os.path.join(input_dir, filename)
            result = process_single_video(vid_path)
            if result:
                processed.append(result)

    if processed:
        print("\n" + "=" * 60)
        print(f"PROCESSING COMPLETE - {len(processed)} VIDEO(S) ENHANCED")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("NO VIDEOS PROCESSED")
        print("=" * 60)
    
    return processed


def main():
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None

    if specific_video:
        result = process_single_video(specific_video)
        if result:
            print("\n" + "=" * 60)
            print("PROCESSING COMPLETE - VIDEO & AUDIO ENHANCED")
            print("=" * 60)
        else:
            sys.exit(1)
    else:
        videos = [f for f in os.listdir(input_dir) if f.endswith('.mp4')]
        print(f"Found {len(videos)} videos to process.")

        for filename in videos:
            vid_path = os.path.join(input_dir, filename)
            process_single_video(vid_path)

        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print("=" * 60)


if __name__ == "__main__":
    main()

