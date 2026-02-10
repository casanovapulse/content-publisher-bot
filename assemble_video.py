from moviepy.editor import *
import json
import os
import wave
import sys
import textwrap
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from vosk import Model, KaldiRecognizer

# Ensure Vosk model exists
if not os.path.exists("vosk-model-small-en-us-0.15"):
    print("Vosk model missing! Please run 'python download_model.py' first.")
    sys.exit(1)

def get_font(size, bold=True):
    """Robust font loader for Windows and Linux."""
    # Priority list of fonts
    font_names = [
        "arialbd.ttf" if bold else "arial.ttf",
        "Arial_Bold.ttf" if bold else "Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "DejaVuSans-Bold.ttf"
    ]
    
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except:
            continue
            
    print(f"Warning: No premium fonts found. Falling back to default (size {size} ignored).")
    return ImageFont.load_default()

def transcribe_audio(audio_path):
    """
    Transcribe audio using Vosk and return word-level timestamps.
    Returns: List of {"word": str, "start": float, "end": float}
    """
    # Convert MP3 to WAV mono 16kHz for Vosk
    temp_wav = "temp_vosk.wav"
    
    # Use ffmpeg via MoviePy to convert
    # Alternatively, use pydub but moviepy is already here
    clip = AudioFileClip(audio_path)
    clip.write_audiofile(temp_wav, fps=16000, nbytes=2, codec='pcm_s16le', ffmpeg_params=["-ac", "1"], verbose=False, logger=None)
    
    model = Model("vosk-model-small-en-us-0.15")
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)

    results = []
    
    with wave.open(temp_wav, "rb") as wf:
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                part_res = json.loads(rec.Result())
                if 'result' in part_res:
                    results.extend(part_res['result'])
    
    part_res = json.loads(rec.FinalResult())
    if 'result' in part_res:
        results.extend(part_res['result'])
        
    os.remove(temp_wav)
    return results

def generate_background_image(width=1080, height=1920):
    """Generates a branded background image (Dark Canvas + Yellow Accents)."""
    # Define Brand Colors
    BRAND_YELLOW = (255, 215, 0) # Gold
    BRAND_DARK = (20, 20, 30) # Dark Navy/Black
    
    img = Image.new('RGB', (width, height), color=BRAND_DARK)
    draw = ImageDraw.Draw(img)
    
    # Yellow Header Bar for Branding
    draw.rectangle([(0, 0), (width, 150)], fill=BRAND_YELLOW)
    
    # Add Logo Text in Black on Yellow
    font_logo = get_font(60, bold=True)
    draw.text((50, 45), "IELTS ZOOM", font=font_logo, fill="black", stroke_width=2)
    
    # Bottom Yellow Line for Frame
    draw.rectangle([(0, height-20), (width, height)], fill=BRAND_YELLOW)
    
    save_path = "generated_content/background.jpg"
    if not os.path.exists("generated_content"):
        os.makedirs("generated_content")
    img.save(save_path)
    return save_path

def create_info_panel(text, draw, top_margin, font_size=80, color="white", width=1080):
    """
    Draws wrapped text onto an existing ImageDraw object and returns the next available Y position.
    """
    font = get_font(font_size, bold=True)
        
    margin = 80
    max_w = width - (2 * margin)
    
    # Wrap text
    lines = []
    words = str(text).split()
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) <= max_w:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    
    y = top_margin
    for line in lines:
        # Shadow/Stroke
        for adj in range(-2, 3):
            for adj2 in range(-2, 3):
                draw.text((margin+adj, y+adj2), line, font=font, fill="black")
        draw.text((margin, y), line, font=font, fill=color)
        y += font_size + 15
        
    return y + 40 # Return Y plus some padding for the next element

def create_subtitle_image(text, width=1080, height=250, font_size=90):
    """Creates a subtitle image with yellow text and black stroke."""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    font = get_font(font_size, bold=True)
        
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (width - text_w) // 2
    y = (height - text_h) // 2
    
    stroke = 5
    for adj in range(-stroke, stroke+1):
        for adj2 in range(-stroke, stroke+1):
            draw.text((x+adj, y+adj2), text, font=font, fill="black")
            
    draw.text((x, y), text, font=font, fill="#FFD700") 
    return np.array(img)

def assemble_video():
    script_path = "generated_content/script.json"
    if not os.path.exists(script_path):
        print("Script file not found.")
        return

    with open(script_path, "r") as f:
        script = json.load(f)
        
    audio_path = "generated_content/full_audio.mp3"
    if not os.path.exists(audio_path):
        print("Audio file not found.")
        return
        
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    
    # 1. Background
    bg_path = generate_background_image()
    video_base = ImageClip(bg_path).set_duration(duration)
    
    # 2. Static UI Overlay - Minimalist Approach
    ui_img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ui_img)
    
    y_pos = 250 # Start lower to breathe
    
    # Display Title
    y_pos = create_info_panel(script.get("display_title", ""), draw, y_pos, font_size=90, color="#FFD700")
    y_pos += 80 # Extra space
    
    # Basic vs Better Way
    basic = script.get("basic_way", "")
    better = script.get("better_way", "")
    
    if basic:
        y_pos = create_info_panel(f"Instead of: \"{basic}\"", draw, y_pos, font_size=55, color="white")
    
    y_pos += 40
    if better:
        y_pos = create_info_panel(f"Use: {better}", draw, y_pos, font_size=75, color="#00FFCC") # Highlight Teal
    
    y_pos += 120 # Big gap before example
    
    # Example
    example = script.get("example", "")
    if example:
        create_info_panel(f"Example:\n\"{example}\"", draw, y_pos, font_size=50, color="white")
        
    ui_overlay = ImageClip(np.array(ui_img)).set_duration(duration)
    layers = [video_base, ui_overlay]
    
    # 3. Single-Word Subtitles (High-Impact)
    print(f"Transcribing {duration:.1f}s audio for single-word subtitles...")
    try:
        words = transcribe_audio(audio_path)
        last_end = 0
        for w in words:
            start = w["start"]
            end = w["end"]
            
            # Prevent overlap
            if start < last_end: start = last_end
            if start >= duration: break
            end = min(end, duration)
            if end - start < 0.15: end = start + 0.15
            last_end = end
            
            text = w["word"].upper()
            sub_img = create_subtitle_image(text, font_size=85) # Slightly larger for single word impact
            # Position at 1400 (space from bottom)
            sub_clip = ImageClip(sub_img).set_position(('center', 1400)).set_start(start).set_duration(end-start)
            layers.append(sub_clip)
            
    except Exception as e:
        print(f"Subtitle error: {e}")
        
    # Final Composite
    print("Compositing video...")
    final_video = CompositeVideoClip(layers).set_duration(duration).set_audio(audio_clip)
    
    # Enforce safe duration
    if final_video.duration > 60:
        final_video = final_video.subclip(0, 60)
        
    final_video.write_videofile("ielts_short.mp4", fps=24, codec="libx264", audio_codec="aac", threads=4)
    print(f"✅ Minimalist Video Generated: ielts_short.mp4")

if __name__ == "__main__":
    assemble_video()
