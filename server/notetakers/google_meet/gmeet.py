import asyncio
import os
import subprocess
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import time
from supabase import create_client, Client
from io import BytesIO
from PIL import Image
from pyvirtualdisplay import Display

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

# Asynchronous function to run shell commands
async def run_command_async(command):
    process = await asyncio.create_subprocess_shell(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout, stderr

# Asynchronous function to handle Google sign-in
async def google_sign_in(email, password, page):
    await page.goto("https://accounts.google.com")
    await page.wait_for_selector('input[type="email"]')
    await page.fill('input[type="email"]', email)
    await capture_and_upload_screenshot(page, "email_entered")
    await page.click('button:has-text("Next")')
    await page.wait_for_selector('input[type="password"]')
    await page.fill('input[type="password"]', password)
    await capture_and_upload_screenshot(page, "password_entered")
    await page.keyboard.press('Enter')
    await page.wait_for_navigation()
    await capture_and_upload_screenshot(page, "login_successful")

# Main function to join a Google Meet
async def join_meet(meet_link, end_time=30):
    print(f"start recorder for {meet_link}")

    # Setup virtual audio drivers
    print("starting virtual audio drivers")
    try:
        if os.uname().sysname == "Darwin":
            print("Ensure BlackHole is installed and configured as the default audio device.")
        else:
            # Check if PulseAudio is running
            pulse_check = subprocess.run(["pulseaudio", "--check"], capture_output=True)
            if pulse_check.returncode != 0:
                print("PulseAudio is not running. Attempting to start it.")
                subprocess.run(["pulseaudio", "--start"], check=True)

            subprocess.check_output(
                'pactl load-module module-null-sink sink_name=DummyOutput sink_properties=device.description="Virtual_Dummy_Output"',
                shell=True,
            )
            subprocess.check_output(
                'pactl load-module module-null-sink sink_name=MicOutput sink_properties=device.description="Virtual_Microphone_Output"',
                shell=True,
            )
            subprocess.check_output(
                "pactl set-default-source MicOutput.monitor", shell=True
            )
            subprocess.check_output("pactl set-default-sink MicOutput", shell=True)
            subprocess.check_output(
                "pactl load-module module-virtual-source source_name=VirtualMic",
                shell=True,
            )
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while setting up virtual audio drivers: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return

    print('here subprocess end')

    # Start virtual display
    display = Display(visible=0, size=(1920, 1080))
    display.start()

    # Launch browser with Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--window-size=1920,1080',
            '--use-fake-ui-for-media-stream',
            '--use-file-for-fake-video-capture=@black.y4m'
        ])
        context = await browser.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36")
        page = await context.new_page()

        # Apply stealth plugin
        await stealth_async(page)

        # Retrieve email and password from environment variables
        email = os.getenv("GMAIL_USER_EMAIL", "")
        password = os.getenv("GMAIL_USER_PASSWORD", "")

        if not email or not password:
            print("No email or password specified")
            return

        # Sign in to Google
        # print("Google Sign in")
        # await google_sign_in(email, password, page)

        # Access the Google Meet link
        await page.goto(meet_link)

        # Grant necessary permissions
        await page.evaluate('''() => {
            navigator.permissions.query = (parameters) => {
                return Promise.resolve({ state: 'granted' });
            };
        }''')

        for i in range(5):
            await capture_and_upload_screenshot(page, f"screenshot_{i+1}")
            await asyncio.sleep(1)
        try:
            await page.wait_for_selector("button:has-text('Join now')", timeout=120000)
            button = await page.query_selector("button:has-text('Join now')")
            await button.click()
        except Exception:
            print("No popup")
        await capture_and_upload_screenshot(page, "after_popup_handling")

        print("Disable microphone")
        try:
            button = await page.wait_for_selector("//div[@aria-label='Turn off microphone']", timeout=10000)
            print("Disabling microphone using Playwright")
            await button.click()
        except Exception:
            print("Microphone button not found using Playwright")
        await capture_and_upload_screenshot(page, "after_microphone_disable")

        print("Disable camera")
        try:
            button = await page.wait_for_selector("//div[@aria-label='Turn off camera']", timeout=10000)
            print("Disabling camera using Playwright")
            await button.click()
        except Exception:
            print("Camera button not found using Playwright")
        await capture_and_upload_screenshot(page, "after_camera_disable")

        # Handle authentication and meeting options
        try:
            input_element = await page.wait_for_selector('.//input[@aria-label="Your name"]', timeout=10000)
            await input_element.fill("Catchflow AI")
        except Exception:
            print("Name input field not found")
        await capture_and_upload_screenshot(page, "after_name_input")

        try:
            join_now_button = await page.wait_for_selector("//span[contains(text(), 'Join now')]/ancestor::button", timeout=10000)
            print(join_now_button)
            await join_now_button.click()
        except Exception:
            print("Join Now button not found")
        await capture_and_upload_screenshot(page, "after_join_now_click")

        # Start capturing the transcript
        print("Start capturing transcript")
        transcript = []
        last_transcript = ""

        start_time = time.time()

        while True and (time.time() - start_time) < (end_time * 60):
            try:
                caption_button = await page.wait_for_selector('//*[@id="yDmH0d"]/c-wiz/div/div/div[34]/div[4]/div[10]/div/div/div[2]/div/div[3]/span/button', timeout=10000)
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
