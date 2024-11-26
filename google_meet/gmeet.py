import asyncio
import os
import subprocess
import click
from dotenv import load_dotenv
from time import sleep
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, InvalidSelectorException
import time
import uuid

# Load environment variables
load_dotenv()

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
            subprocess.check_output(
                "sudo rm -rf /var/run/pulse /var/lib/pulse /root/.config/pulse", shell=True
            )
            subprocess.check_output(
                "sudo pulseaudio -D --verbose --exit-idle-time=-1 --system --disallow-exit  >> /dev/null 2>&1",
                shell=True,
            )
            subprocess.check_output(
                'sudo pactl load-module module-null-sink sink_name=DummyOutput sink_properties=device.description="Virtual_Dummy_Output"',
                shell=True,
            )
            subprocess.check_output(
                'sudo pactl load-module module-null-sink sink_name=MicOutput sink_properties=device.description="Virtual_Microphone_Output"',
                shell=True,
            )
            subprocess.check_output(
                "sudo pactl set-default-source MicOutput.monitor", shell=True
            )
            subprocess.check_output("sudo pactl set-default-sink MicOutput", shell=True)
            subprocess.check_output(
                "sudo pactl load-module module-virtual-source source_name=VirtualMic",
                shell=True,
            )
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while setting up virtual audio drivers: {e}")
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
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    log_path = "chromedriver.log"

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
    await google_sign_in(email, password, driver)

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
        print("Try to dismiss missing mic")
        sleep(2)
        mic_element = driver.find_element(By.CLASS_NAME, "VfPpkd-vQzf8d")
        if mic_element:
            print('mic is missing')
    except NoSuchElementException:
        print("No missing mic element found")

    try:
        print("Allow Microphone")
        driver.find_element(
            By.XPATH,
            "/html/body/div/div[3]/div[2]/div/div/div/div/div[2]/div/div[1]/button",
        ).click()
        sleep(2)
    except NoSuchElementException:
        print("No Allow Microphone popup")

    try:
        time.sleep(2)
        print("Try to disable microphone")
        try:
            element = driver.find_element(
                By.XPATH,
                '//*[@id="yDmH0d"]/c-wiz/div/div/div[35]/div[3]/div/div[2]/div[4]/div/div/div[1]/div[1]/div/div[7]/div[1]/div/div/div[1]'
            )
        except NoSuchElementException:
            element = driver.find_element(
                By.XPATH,
                '//*[@id="yDmH0d"]/c-wiz/div/div/div[35]/div[4]/div/div[2]/div[4]/div/div/div[1]/div[1]/div/div[7]/div[1]/div/div/div[1]'
            )
        driver.execute_script("arguments[0].click();", element)
    except (NoSuchElementException, InvalidSelectorException) as e:
        print(f"Error disabling microphone: {e}")

    sleep(2)

    # Disable camera
    print("Disable camera")
    try:
        try:
            driver.find_element(
                By.XPATH,
                '//*[@id="yDmH0d"]/c-wiz/div/div/div[35]/div[3]/div/div[2]/div[4]/div/div/div[1]/div[1]/div/div[7]/div[2]/div/div[1]'
            ).click()
        except NoSuchElementException:
            driver.find_element(
                By.XPATH,
                '//*[@id="yDmH0d"]/c-wiz/div/div/div[35]/div[4]/div/div[2]/div[4]/div/div/div[1]/div[1]/div/div[7]/div[2]/div/div[1]'
            ).click()
        sleep(2)
    except NoSuchElementException:
        print("Cannot disable camera: No such element")
    except Exception as e:
        print(f"Cannot disable camera: {e}")

    # Handle authentication and meeting options
    try:
        driver.find_element(
            By.XPATH,
            '//*[@id="yDmH0d"]/c-wiz/div/div/div[14]/div[3]/div/div[2]/div[4]/div/div/div[2]/div[1]/div[1]/div[3]/label/input',
        ).click()
        sleep(2)
        driver.find_element(
            By.XPATH,
            '//*[@id="yDmH0d"]/c-wiz/div/div/div[14]/div[3]/div/div[2]/div[4]/div/div/div[2]/div[1]/div[1]/div[3]/label/input',
        ).send_keys("TEST")
        sleep(5)
        driver.find_element(
            By.XPATH,
            '//*[@id="yDmH0d"]/c-wiz/div/div/div[14]/div[3]/div/div[2]/div[4]/div/div/div[2]/div[1]/div[2]/div[1]/div[1]/button/span',
        ).click()
        sleep(5)
    except NoSuchElementException:
        print("authentification already done")
        sleep(5)
        print(driver.title)
        try:
            driver.find_element(
                By.XPATH,
                '//*[@id="yDmH0d"]/c-wiz/div/div/div[35]/div[4]/div/div[2]/div[4]/div/div/div[2]/div[1]/div[2]/div[1]/div/div/button'
            ).click()
        except NoSuchElementException:
            try:
                driver.find_element(
                    By.XPATH,
                    '//*[@id="yDmH0d"]/c-wiz/div/div/div[35]/div[3]/div/div[2]/div[4]/div/div/div[2]/div[1]/div[2]/div[1]/div/div/button'
                ).click()
            except NoSuchElementException:
                print("Neither button is present")
        sleep(5)

    # Start capturing the transcript
    print("Start capturing transcript")
    transcript = []

    start_time = time.time()

    time.sleep(1)

    while True and (time.time() - start_time) < (end_time * 60):
        try:
            caption_button = driver.find_element(By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div/div[34]/div[4]/div[10]/div/div/div[2]/div/div[3]/span/button')
            # Check if the button is not enabled by checking the aria-pressed attribute
            print(caption_button)
            if caption_button.get_attribute("aria-pressed") == "false":
                caption_button.click()
            break  # Exit the loop if the button is found and clicked
        except NoSuchElementException:
            print("Captions button not found. Retrying...")
            sleep(1)  # Wait for a short period before retrying

    try:
        while (time.time() - start_time) < (end_time * 60):
            sleep(2)
            transcript_elements = driver.find_elements(By.CSS_SELECTOR, ".a4cQT .nMcdL")
            for element in transcript_elements:
                person_name = element.find_element(By.CLASS_NAME, "KcIKyf").text
                transcript_text = element.find_element(By.CLASS_NAME, "bh44bd").text
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                transcript.append({
                    "personName": person_name,
                    "timeStamp": timestamp,
                    "transcriptText": transcript_text
                })
            print(transcript)
            print(end_time * 60 - (time.time() - start_time))
    except Exception as e:
        print(f"An error occurred while capturing the transcript: {e}")

    print("Done capturing transcript")

    # Save the transcript to a file
    transcript_dir = "transcripts"
    os.makedirs(transcript_dir, exist_ok=True)
    transcript_file = os.path.join(transcript_dir, f"{uuid.uuid4()}.txt")
    with open(transcript_file, "w") as f:
        for entry in transcript:
            f.write(f"{entry['timeStamp']} - {entry['personName']}: {entry['transcriptText']}\n")
    print(f"Transcript saved to {transcript_file}")

    # Close the Google Meet tab after capturing
    driver.close()
    print("Closed the Google Meet tab")
    print("- End of work")

# Entry point for the script
if __name__ == "__main__":
    meet_link = "https://meet.google.com/srr-zhkv-ydv"
    end_time = 3
    end_time = int(end_time) if end_time else 30
    click.echo("starting google meet recorder...")
    asyncio.run(join_meet(meet_link, end_time))
    click.echo("finished recording google meet.")