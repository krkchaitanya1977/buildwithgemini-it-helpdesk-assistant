import asyncio
import os
import shutil
import time
from playwright.async_api import async_playwright
from google.cloud import storage

GCS_BUCKET_NAME = "it-helpdesk-assets-qwiklabs-gcp-01-16b444c9d053"
ARTIFACT_DIR = "/config/.gemini/antigravity/brain/60eb1c74-1feb-4763-9e41-6da2d869ec3c"
FRONTEND_URL = "https://it-helpdesk-frontend-750528364862.us-east1.run.app"

async def record_demo():
    print(f"Starting demo recording against {FRONTEND_URL}...")
    temp_video_dir = os.path.join(ARTIFACT_DIR, "scratch", "video_temp")
    os.makedirs(temp_video_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=temp_video_dir,
            record_video_size={"width": 1280, "height": 720}
        )
        page = await context.new_page()

        print("Navigating to frontend...")
        await page.goto(FRONTEND_URL, wait_until="networkidle")
        await asyncio.sleep(2)

        # 1. Prompt 1: Check live system status (app strength)
        prompt1 = "Check live status for VPN and Okta SSO"
        print(f"Submitting Prompt 1: '{prompt1}'")
        await page.fill("#input", prompt1)
        await asyncio.sleep(1)
        await page.click("button.send-btn")
        
        # Wait for agent response to populate
        print("Waiting for response to Prompt 1...")
        await page.wait_for_selector(".msg.agent", timeout=60000)
        await asyncio.sleep(6)

        # 2. Prompt 2: Richer prompt showing tool calls, database lookup, and image generation
        prompt2 = "Generate a technical IT setup diagram for Wi-Fi and list open IT tickets in Firestore."
        print(f"Submitting Prompt 2: '{prompt2}'")
        await page.fill("#input", prompt2)
        await asyncio.sleep(1)
        await page.click("button.send-btn")

        print("Waiting for response to Prompt 2...")
        await asyncio.sleep(25)

        print("Closing browser context to finalize video recording...")
        video_path = await page.video.path()
        await context.close()
        await browser.close()

    print(f"Recorded video saved locally at: {video_path}")

    # Copy video to artifact directory
    final_video_name = "demo_recording.webm"
    final_artifact_path = os.path.join(ARTIFACT_DIR, final_video_name)
    shutil.copy(video_path, final_artifact_path)
    print(f"Saved artifact to: {final_artifact_path}")

    # Upload to Cloud Storage bucket for public link
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(final_video_name)
        blob.upload_from_filename(final_artifact_path, content_type="video/webm")
        gcs_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{final_video_name}"
        print(f"Uploaded demo video to GCS: {gcs_url}")
    except Exception as e:
        print(f"GCS Upload Notice: {e}")

if __name__ == "__main__":
    asyncio.run(record_demo())
