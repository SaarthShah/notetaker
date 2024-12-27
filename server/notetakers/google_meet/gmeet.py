import asyncio
import os
import subprocess
from dotenv import load_dotenv
from time import sleep
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, InvalidSelectorException, StaleElementReferenceException
import time

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

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
    sleep(1)
    email_field = driver.find_element(By.NAME, "identifier")
    email_field.send_keys(email)
    sleep(2)
    driver.find_element(By.ID, "identifierNext").click()
    sleep(3)
    password_field = driver.find_element(By.NAME, "Passwd")
    password_field.click()
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)
    sleep(5)

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

    # Configure Chrome options
    options = uc.ChromeOptions()
    options.add_argument("--use-fake-ui-for-media-stream")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-application-cache")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--headless")  # Run Chrome in headless mode
    log_path = "chromedriver.log"

    # Ensure binary location is set as a string
    options.binary_location = "/usr/bin/google-chrome"

    # Initialize Chrome driver
    driver = uc.Chrome(service_log_path=log_path, use_subprocess=False, options=options)
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

    # Handle popups and disable microphone
    try:
        sleep(2)
        driver.find_element(
            By.XPATH,
            "/html/body/div/div[3]/div[2]/div/div/div/div/div[2]/div/div[1]/button",
        ).click()
    except NoSuchElementException:
        print("No popup")

    
    print("Disable microphone")
    sleep(2)

    try:
        # Find the button to turn off the microphone using XPath
        button = driver.find_element(By.XPATH, "//div[@aria-label='Turn off microphone']")
        print("Disabling microphone using Selenium")
        button.click()
    except NoSuchElementException:
        print("Microphone button not found using Selenium")
    sleep(2)

    # Disable camera
    print("Disable camera")
    try:
        # Find the button to turn off the camera using XPath
        button = driver.find_element(By.XPATH, "//div[@aria-label='Turn off camera']")
        print("Disabling camera using Selenium")
        button.click()
    except NoSuchElementException:
        print("Camera button not found using Selenium")
    sleep(2)

    # Handle authentication and meeting options
    try:
        input_element = driver.find_element(By.XPATH, './/input[@aria-label="Your name"]')  # XPath within the div
        input_element.send_keys("Catchflow AI")
    except NoSuchElementException:
        print("Name input field not found")

    try:
        join_now_button = driver.find_element(By.XPATH, "//span[contains(text(), 'Join now')]/ancestor::button")
        print(join_now_button)
        join_now_button.click()
        sleep(2)
    except NoSuchElementException:
        print("Join Now button not found")

    # Start capturing the transcript
    print("Start capturing transcript")
    transcript = []
    last_transcript = ""

    start_time = time.time()

    while True and (time.time() - start_time) < (end_time * 60):
        try:
            caption_button = driver.find_element(By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div/div[34]/div[4]/div[10]/div/div/div[2]/div/div[3]/span/button')
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
            sleep(1)  # Wait for a short period before retrying

    try:
        while (time.time() - start_time) < (end_time * 60):
            sleep(2)
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
            # print(end_time * 60 - (time.time() - start_time))
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
