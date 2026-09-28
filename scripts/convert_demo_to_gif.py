import glob
import os
import shutil
import subprocess
from PIL import Image

INPUT_WEBM = "/config/.gemini/antigravity/brain/60eb1c74-1feb-4763-9e41-6da2d869ec3c/demo_recording.webm"
OUTPUT_GIF = "/config/Desktop/Session1/it-helpdesk-assistant/demo.gif"
FFMPEG_BIN = "/config/.cache/ms-playwright/ffmpeg-1011/ffmpeg-linux"
TEMP_FRAMES_DIR = "/config/Desktop/Session1/it-helpdesk-assistant/scratch_frames"

def convert_webm_to_gif():
    print(f"Extracting frames from {INPUT_WEBM}...")
    if os.path.exists(TEMP_FRAMES_DIR):
        shutil.rmtree(TEMP_FRAMES_DIR)
    os.makedirs(TEMP_FRAMES_DIR, exist_ok=True)

    # 1. Export PNG frames with ffmpeg
    cmd = [
        FFMPEG_BIN,
        "-i", INPUT_WEBM,
        "-vf", "fps=6,scale=640:-1:flags=lanczos",
        "-y",
        os.path.join(TEMP_FRAMES_DIR, "frame_%04d.png")
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("FFmpeg frame extraction output:", res.returncode)

    # 2. Combine PNG frames into looping demo.gif using PIL
    png_files = sorted(glob.glob(os.path.join(TEMP_FRAMES_DIR, "frame_*.png")))
    print(f"Total extracted PNG frames: {len(png_files)}")

    if not png_files:
        raise RuntimeError("No PNG frames extracted by ffmpeg!")

    images = []
    # Sample frames to ensure lightweight GIF size
    for f in png_files:
        img = Image.open(f)
        img = img.convert("P", palette=Image.ADAPTIVE)
        images.append(img)

    print(f"Saving optimized looping GIF to {OUTPUT_GIF}...")
    images[0].save(
        OUTPUT_GIF,
        save_all=True,
        append_images=images[1:],
        optimize=True,
        duration=150,  # 150ms per frame
        loop=0
    )

    # Clean up temp frames
    shutil.rmtree(TEMP_FRAMES_DIR, ignore_errors=True)
    gif_size_mb = os.path.getsize(OUTPUT_GIF) / (1024 * 1024)
    print(f"Successfully generated {OUTPUT_GIF}! Size: {gif_size_mb:.2f} MB")

if __name__ == "__main__":
    convert_webm_to_gif()
