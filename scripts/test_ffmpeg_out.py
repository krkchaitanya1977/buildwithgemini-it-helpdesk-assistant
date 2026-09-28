import os
import subprocess

INPUT_WEBM = "/config/.gemini/antigravity/brain/60eb1c74-1feb-4763-9e41-6da2d869ec3c/demo_recording.webm"
FFMPEG_BIN = "/config/.cache/ms-playwright/ffmpeg-1011/ffmpeg-linux"

cmd = [FFMPEG_BIN, "-i", INPUT_WEBM, "-y", "/tmp/out.webm"]
res = subprocess.run(cmd, capture_output=True, text=True)
print("Return code:", res.returncode)
print("STDERR:\n", res.stderr)
