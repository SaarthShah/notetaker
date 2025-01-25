import asyncio
import os
import random
import subprocess
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from pyvirtualdisplay import Display
from fastapi import HTTPException
from supabase import create_client, Client
import time

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Function to set up virtual audio devices
def setup_virtual_audio_devices():
    try:
        print("Setting up virtual audio devices...")
        subprocess.check_output('pactl load-module module-null-sink sink_name=CustomOutput', shell=True)
        subprocess.check_output('pactl load-module module-null-sink sink_name=CustomMicOutput', shell=True)
        subprocess.check_output('pactl set-default-source CustomMicOutput.monitor', shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error setting up virtual audio: {e}")
        raise HTTPException(status_code=500, detail="Failed to set up virtual audio devices.")

# Function to upload image to Supabase
def upload_image_to_supabase(image, filename):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    # Convert BytesIO to bytes for upload
    response = supabase.storage.from_('screenshots').upload(filename, buffer.getvalue(), {"content-type": "image/png"})
    return response

# Function to capture and upload a screenshot
async def capture_and_upload_screenshot(page, step_name):
    screenshot = await page.screenshot(type='png')
    image = Image.open(BytesIO(screenshot))
    upload_image_to_supabase(image, f"{step_name}_{int(time.time())}.png")

# Google sign-in function
async def google_sign_in(email, password, page):
    await page.goto("https://accounts.google.com")
    await page.fill('input[type="email"]', email)
    await capture_and_upload_screenshot(page, "email_entered")
    await page.keyboard.press("Enter")
    await page.wait_for_selector('input[type="password"]')
    await page.fill('input[type="password"]', password)
    await capture_and_upload_screenshot(page, "password_entered")
    await page.keyboard.press("Enter")
    await page.wait_for_load_state('networkidle')
    await capture_and_upload_screenshot(page, "login_successful")

# Main function to join a Google Meet
async def join_meet(meet_link, end_time=30):
    print(f"Starting recorder for {meet_link}")
    setup_virtual_audio_devices()

    # Virtual display for headless environment
    display = Display(visible=0, size=(1920, 1080))
    display.start()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--window-size=1920x1080",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-application-cache",
                "--disable-dev-shm-usage"
            ]
        )

        context = await browser.new_context(
            user_agent=random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
                "(KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
            ]),
            locale="en-US",
            timezone_id="America/Los_Angeles"
        )

        page = await context.new_page()

        # Add stealth-like script
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 4 });
            Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
        """)
        # Sign in to Google
        email = os.getenv("GMAIL_USER_EMAIL", "")
        password = os.getenv("GMAIL_USER_PASSWORD", "")
        if not email or not password:
            print("No email or password specified")
            raise HTTPException(status_code=500, detail="Email or password not specified")
        
        # await google_sign_in(email, password, page)

        # Retry logic for joining the meeting
        max_retries = 5
        for attempt in range(max_retries):
            try:
                await page.goto(meet_link)
                print(f"Opened meet link: {meet_link}")
                await capture_and_upload_screenshot(page, "meet_opened")

                # Join Google Meet
                got_it_button = await page.wait_for_selector("button.UywwFc-LgbsSe.UywwFc-LgbsSe-OWXEXe-dgl2Hf.IMT1Gf", timeout=10000)
                await got_it_button.click()
                await capture_and_upload_screenshot(page, "after_got_it_clicked")

                # Locate the name input field
                name_input_selector = 'div.qdOxv-fmcmS-yrriRe.qdOxv-fmcmS-yrriRe-OWXEXe-INsAgc.qdOxv-fmcmS-yrriRe-OWXEXe-di8rgd-V67aGc input[type="text"]'
                name_input = await page.wait_for_selector(name_input_selector, timeout=10000)
                await name_input.fill("Catchflow AI")
                await capture_and_upload_screenshot(page, "entered_name")

                try:
                    button = await page.wait_for_selector("//div[@aria-label='Turn off microphone']", timeout=10000)
                    print("Disabling microphone using Playwright")
                    await button.click()
                except Exception:
                    print("Microphone button not found using Playwright")
                    continue
                await capture_and_upload_screenshot(page, "after_microphone_disable")
                await page.wait_for_timeout(random.randint(1000, 3000))

                print("Disable camera")
                try:
                    button = await page.wait_for_selector("//div[@aria-label='Turn off camera']", timeout=10000)
                    print("Disabling camera using Playwright")
                    await button.click()
                except Exception:
                    print("Camera button not found using Playwright")
                    continue
                await capture_and_upload_screenshot(page, "after_camera_disable")
                await page.wait_for_timeout(random.randint(1000, 3000))

                try:
                    join_now_button = await page.wait_for_selector("//span[contains(text(), 'Join now')]/ancestor::button", timeout=10000)
                    print(join_now_button)
                    await join_now_button.click()
                except Exception:
                    print("Join Now button not found")
                await capture_and_upload_screenshot(page, "after_join_now_click")
                break

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    await asyncio.sleep(5)  # Wait before retrying
                else:
                    raise HTTPException(status_code=500, detail="Failed to join meeting after multiple attempts.")

        # Start capturing the transcript
        print("Start capturing transcript")
        transcript = []
        last_transcript = ""

        start_time = time.time()

        while True and (time.time() - start_time) < (end_time * 60):
            try:
                caption_button = await page.wait_for_selector('button[aria-label="Turn on captions"]', timeout=10000)
                # Check if the button is not enabled by checking the aria-pressed attribute
                print(caption_button)
                aria_pressed = await page.evaluate('(button) => button.getAttribute("aria-pressed")', caption_button)
                if aria_pressed == "false":
                    await caption_button.click()
                break  # Exit the loop if the button is found and clicked
            except Exception:
                try:
                    waiting_text = await page.query_selector('//*[contains(text(), "Asking to be let in")]')
                    if waiting_text:
                        print("Waiting to be let in")
                except Exception:
                    print("Captions button not found. Retrying...")
                await asyncio.sleep(1)  # Wait for a short period before retrying
        await capture_and_upload_screenshot(page, "after_captions_button")

        try:
            while (time.time() - start_time) < (end_time * 60):
                await asyncio.sleep(2)
                transcript_elements = await page.query_selector_all(".a4cQT .nMcdL")
                for element in transcript_elements:
                    try:
                        person_name = await page.evaluate('(element) => element.querySelector(".KcIKyf").innerText', element)
                        transcript_text = await page.evaluate('(element) => element.querySelector(".bh44bd").innerText', element)
                        if transcript_text != last_transcript:
                            last_transcript = transcript_text
                            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                            transcript.append({
                                "personName": person_name,
                                "timeStamp": timestamp,
                                "transcriptText": transcript_text
                            })
                            print(f"New transcript: {transcript_text}")
                    except Exception as e:
                        print(f"An error occurred while processing transcript element: {e}")
        except Exception as e:
            print(f"An error occurred while capturing the transcript: {e}")

        print("Done capturing transcript")

        # Return the transcript instead of saving to a file
        print("Returning the captured transcript")

        # Close the Google Meet window after capturing
        await browser.close()
        display.stop()
        print("Closed the Google Meet window")
        print("- End of work")

        return transcript
