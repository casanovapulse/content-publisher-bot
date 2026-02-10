# IELTS Zoom Automation Bot

This bot automatically generates engaging IELTS preparation content (YouTube Shorts / Instagram Reels) using AI.

## Features
- **Script Generation**: Creates high-yield educational scripts (Vocabulary, Grammar, Idioms) optimized for short-form video (45-50s).
- **Audio Generation**: Uses Pollinations AI (OpenAI Audio) for natural voiceovers.
- **Visuals**: Uses branded static backgrounds with dynamic text overlays for clear readability.
- **Video Assembly**: Stitches audio and text overlays into vertical (9:16) videos.
- **Multi-Platform Publishing**: Automatically uploads to YouTube Shorts, Instagram Reels, TikTok, Threads, Twitter, and Telegram.

## Setup
1. Ensure `.env` is configured with `POLLINATIONS_API_KEY` and all social media credentials (see `publish_content.py` for required keys).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the bot:
   ```bash
   python bot.py
   ```

## Configuration
- Modify `generate_content.py` to change prompt topics or models.
- Modify `assemble_video.py` to change video layout or text overlay styles.

## Output
Generated videos are saved in `final_videos/` with a timestamp.
Intermediate files are in `generated_content/`.

## Continuous Operation
Run `python bot.py` to start the continuous loop. It generates a new video every 4 hours (configurable in `bot.py`).
