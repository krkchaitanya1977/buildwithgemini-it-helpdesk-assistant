import os
import imageio
from PIL import Image

INPUT_WEBM = "/config/.gemini/antigravity/brain/60eb1c74-1feb-4763-9e41-6da2d869ec3c/demo_recording.webm"
OUTPUT_GIF = "/config/Desktop/Session1/it-helpdesk-assistant/demo.gif"

def convert_webm():
    print(f"Reading {INPUT_WEBM} with imageio...")
    reader = imageio.get_reader(INPUT_WEBM)
    fps = reader.get_meta_data().get("fps", 25)
    print(f"Video meta FPS: {fps}")

    frames = []
    # Sample every 3rd frame to optimize GIF size
    for i, frame in enumerate(reader):
        if i % 3 == 0:
            img = Image.fromarray(frame)
            img.thumbnail((640, 360))
            img = img.convert("P", palette=Image.ADAPTIVE)
            frames.append(img)

    print(f"Loaded {len(frames)} processed frames. Writing to {OUTPUT_GIF}...")
    frames[0].save(
        OUTPUT_GIF,
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=120,
        loop=0
    )
    
    gif_size_mb = os.path.getsize(OUTPUT_GIF) / (1024 * 1024)
    print(f"Successfully generated {OUTPUT_GIF}! Size: {gif_size_mb:.2f} MB")

if __name__ == "__main__":
    convert_webm()
