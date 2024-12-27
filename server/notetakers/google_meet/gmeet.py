import asyncio
import os
import subprocess
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from supabase import create_client, Client
from io import BytesIO
from PIL import Image
from selenium_stealth import stealth

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Asynchronous function to run shell commands
async def run_command_async(command):
    process = await asyncio.create_subprocess_shell(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout, stderr

# Asynchronous function to handle Google sign-in
async def google_sign_in(email, password, driver):
    driver.get("https://accounts.google.com")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "identifier")))
    email_field = driver.find_element(By.NAME, "identifier")
    email_field.send_keys(email)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "identifierNext"))).click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "Passwd")))
    password_field = driver.find_element(By.NAME, "Passwd")
    password_field.click()
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)
    WebDriverWait(driver, 10).until(EC.url_contains("myaccount.google.com"))

def create_chrome_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--headless")  # Headless mode
    options.add_argument("--window-size=1920x1080")  # Set window size   
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--use-fake-ui-for-media-stream")
    options.add_argument("--use-file-for-fake-video-capture=@black.y4m")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36")

    # Ensure the correct path to the ChromeDriver
    service = Service('/path/to/chromedriver')
    
    # Create the Chrome driver
    driver = uc.Chrome(service=service, options=options)
    
    # Apply Selenium Stealth
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    
    return driver

# Function to upload image to Supabase
def upload_image_to_supabase(image, filename):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    # Convert BytesIO to bytes for upload
    response = supabase.storage.from_('screenshots').upload(filename, buffer.getvalue(), {"content-type": "image/png"})
    return response

# Function to capture and upload a screenshot
def capture_and_upload_screenshot(driver, step_name):
    screenshot = driver.get_screenshot_as_png()
    image = Image.open(BytesIO(screenshot))
    upload_image_to_supabase(image, f"{step_name}_{int(time.time())}.png")

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

    # Initialize Chrome driver
    driver = create_chrome_driver()
    driver.set_window_size(1920, 1080)

    # Retrieve email and password from environment variables
    print('here')
    email = os.getenv("GMAIL_USER_EMAIL", "")
    password = os.getenv("GMAIL_USER_PASSWORD", "")

    if not email or not password:
        print("No email or password specified")
        return

    # Sign in to Google
    print("Google Sign in")
    # await google_sign_in(email, password, driver)

    # Access the Google Meet link
    driver.get(meet_link)

    # Grant necessary permissions
    driver.execute_cdp_cmd(
        "Browser.grantPermissions",
        {
            "origin": meet_link,
            "permissions": [
                "geolocation",
                "audioCapture",
                "displayCapture",
                "videoCapture",
                "videoCapturePanTiltZoom",
            ],
        },
    )

    for i in range(5):
        capture_and_upload_screenshot(driver, f"screenshot_{i+1}")
        time.sleep(1)
    try:
        WebDriverWait(driver, 120).until(EC.element_to_be_clickable(
            (By.XPATH, "/html/body/div/div[3]/div[2]/div/div/div/div/div[2]/div/div[1]/button")
        )).click()
    except NoSuchElementException:
        print("No popup")
    capture_and_upload_screenshot(driver, "after_popup_handling")

    print("Disable microphone")
    try:
        # Find the button to turn off the microphone using XPath
        button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@aria-label='Turn off microphone']")
        ))
        print("Disabling microphone using Selenium")
        button.click()
    except NoSuchElementException:
        print("Microphone button not found using Selenium")
    capture_and_upload_screenshot(driver, "after_microphone_disable")

    print("Disable camera")
    try:
        # Find the button to turn off the camera using XPath
        button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@aria-label='Turn off camera']")
        ))
        print("Disabling camera using Selenium")
        button.click()
    except NoSuchElementException:
        print("Camera button not found using Selenium")
    capture_and_upload_screenshot(driver, "after_camera_disable")

    # Handle authentication and meeting options
    try:
        input_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, './/input[@aria-label="Your name"]')
        ))
        input_element.send_keys("Catchflow AI")
    except NoSuchElementException:
        print("Name input field not found")
    capture_and_upload_screenshot(driver, "after_name_input")

    try:
        join_now_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//span[contains(text(), 'Join now')]/ancestor::button")
        ))
        print(join_now_button)
        join_now_button.click()
    except NoSuchElementException:
        print("Join Now button not found")
    capture_and_upload_screenshot(driver, "after_join_now_click")

    # Start capturing the transcript
    print("Start capturing transcript")
    transcript = []
    last_transcript = ""

    start_time = time.time()

    while True and (time.time() - start_time) < (end_time * 60):
        try:
            caption_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div/div[34]/div[4]/div[10]/div/div/div[2]/div/div[3]/span/button')
            ))
            # Check if the button is not enabled by checking the aria-pressed attribute
            print(caption_button)
            if caption_button.get_attribute("aria-pressed") == "false":
                caption_button.click()
            break  # Exit the loop if the button is found and clicked
        except NoSuchElementException:
            try:
                waiting_text = driver.find_element(By.XPATH, '//*[contains(text(), "Asking to be let in")]')
                if waiting_text:
                    print("Waiting to be let in")
            except NoSuchElementException:
                print("Captions button not found. Retrying...")
            time.sleep(1)  # Wait for a short period before retrying
    capture_and_upload_screenshot(driver, "after_captions_button")

    try:
        while (time.time() - start_time) < (end_time * 60):
            time.sleep(2)
            transcript_elements = driver.find_elements(By.CSS_SELECTOR, ".a4cQT .nMcdL")
            for element in transcript_elements:
                try:
                    person_name = element.find_element(By.CLASS_NAME, "KcIKyf").text
                    transcript_text = element.find_element(By.CLASS_NAME, "bh44bd").text
                    if transcript_text != last_transcript:
                        last_transcript = transcript_text
                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                        transcript.append({
                            "personName": person_name,
                            "timeStamp": timestamp,
                            "transcriptText": transcript_text
                        })
                        print(f"New transcript: {transcript_text}")
                except StaleElementReferenceException:
                    print("Stale element reference exception caught, skipping this element.")
    except Exception as e:
        print(f"An error occurred while capturing the transcript: {e}")

    print("Done capturing transcript")

    # Return the transcript instead of saving to a file
    print("Returning the captured transcript")

    # Close the Google Meet window after capturing
    driver.quit()
    print("Closed the Google Meet window")
    print("- End of work")

    return transcript
