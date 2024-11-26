import asyncio
import os
import subprocess
import click
import datetime
from dotenv import load_dotenv
from time import sleep

import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

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
    sleep(10)
    missing_mic = False

    try:
        print("Try to dismiss missing mic")
        sleep(2)
        mic_element = driver.find_element(By.CLASS_NAME, "VfPpkd-vQzf8d")
        if mic_element:
            print('mic is missing')
            missing_mic = True
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
        print("Try to disable microphone")
        driver.find_element(
            By.XPATH,
            '//*[@id="yDmH0d"]/c-wiz/div/div/div[35]/div[3]/div/div[2]/div[4]/div/div/div[1]/div[1]/div/div[7]/div[1]/div/div/div[1]',
        ).click()
    except NoSuchElementException:
        print("No microphone to disable")

    sleep(2)

    # Disable camera
    print("Disable camera")
    if not missing_mic:
        driver.find_element(
            By.XPATH,
            '//*[@id="yDmH0d"]/c-wiz/div/div/div[35]/div[3]/div/div[2]/div[4]/div/div/div[1]/div[1]/div/div[7]/div[2]/div/div[1]',
        ).click()
        sleep(2)
    else:
        print("assuming missing mic = missing camera")

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
        sleep(2)
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

    # Monitor meeting status and handle full screen
    now = datetime.datetime.now()
    max_time = now + datetime.timedelta(minutes=5)
    joined = False

    while now < max_time and not joined:
        sleep(5)

        try:
            driver.find_element(
                By.XPATH,
                "/html/body/div[1]/div[3]/span/div[2]/div/div/div[2]/div[1]/button",
            ).click()
        except NoSuchElementException:
            print("No popup in meeting")

        print("Try to click expand options")
        elements = driver.find_elements(By.CLASS_NAME, "VfPpkd-Bz112c-LgbsSe")
        expand_options = False
        for element in elements:
            if element.get_attribute("aria-label") == "More options":
                try:
                    element.click()
                    expand_options = True
                    print("Expand options clicked")
                except Exception as e:
                    print(f"Not able to click expand options: {e}")

        sleep(2)
        print("Try to move to full screen")

        if expand_options:
            li_elements = driver.find_elements(
                By.CLASS_NAME, "V4jiNc.VfPpkd-StrnGf-rymPhb-ibnC6b"
            )
            for li_element in li_elements:
                txt = li_element.text.strip().lower()
                if "fullscreen" in txt:
                    li_element.click()
                    print("Full Screen clicked")
                    joined = True
                    break
                elif "minimize" in txt or "close_fullscreen" in txt:
                    joined = True
                    break

    # Start recording the meeting
    duration = end_time * 60
    print("Start recording")
    if os.uname().sysname == "Darwin":
        record_command = f"ffmpeg -y -video_size 1920x1080 -framerate 30 -f avfoundation -i 1:0 -t {duration} -c:a libmp3lame -q:a 2 recordings/output.mp3"
    else:
        record_command = f"ffmpeg -y -video_size 1920x1080 -framerate 30 -f x11grab -i :99 -f pulse -i default -t {duration} -c:a libmp3lame -q:a 2 recordings/output.mp3"

    await asyncio.gather(
        run_command_async(record_command),
    )

    print("Done recording")
    print("- End of work")

# Entry point for the script
if __name__ == "__main__":
    meet_link = "https://meet.google.com/few-upps-rgn"
    end_time = 3
    end_time = int(end_time) if end_time else 30
    click.echo("starting google meet recorder...")
    asyncio.run(join_meet(meet_link, end_time))
    click.echo("finished recording google meet.")