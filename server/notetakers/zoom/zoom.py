import logging
import os
import time
import re
from os import execl
from sys import executable
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium_stealth import stealth

# Load environment variables
load_dotenv()

usernameStr = os.getenv("ZOOM_USERNAME")
passwordStr = os.getenv("ZOOM_PASSWORD")
k = 0
audio = k

# Logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

def join_zoom_meeting(meeting_url, password, end_time):
    options = uc.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1200,800")
    options.add_argument("user-agent='User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'")
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.media_stream_mic": 2,     # 1:allow, 2:block
        "profile.default_content_setting_values.media_stream_camera": 2,
        "profile.default_content_setting_values.notifications": 2
    })

    browser = uc.Chrome(options=options)

    # Apply Selenium Stealth
    stealth(browser,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    try:
        print("Typing...")
        time.sleep(2)  # Artificial delay
        browser.get('https://zoom.us/signin')
        time.sleep(1)  # Artificial delay
        browser.find_element(By.ID, 'email').send_keys(usernameStr)
        time.sleep(1)  # Artificial delay
        browser.find_element(By.ID, 'password').send_keys(passwordStr)
        time.sleep(1)  # Artificial delay
        browser.save_screenshot("ss.png")
        print("Uploading photo...")
        time.sleep(1)  # Artificial delay
        print("Photo uploaded")
        os.remove('ss.png')
        browser.find_element(By.XPATH, '//button[@id="js_btn_login"]').click()
        time.sleep(20)
        print("Logged In!")
        meeting_number_match = re.search(r'/j/(\d+)', meeting_url)
        if not meeting_number_match:
            print("Invalid meeting URL.")
            return
        meeting_number = meeting_number_match.group(1)
        time.sleep(1)  # Artificial delay
        browser.get(f'https://zoom.us/wc/join/{meeting_number}?action=join&pwd={password}')
        time.sleep(5)
        browser.save_screenshot("ss.png")
        print("Uploading photo...")
        time.sleep(1)  # Artificial delay
        print("Photo uploaded")
        os.remove('ss.png')
        browser.find_element(By.XPATH, '//*[@id="joinBtn"]').click()
        time.sleep(5)
        browser.save_screenshot("ss.png")
        print("Uploading photo...")
        time.sleep(1)  # Artificial delay
        print("Attending Your Meeting")
        os.remove('ss.png')

        # Wait for the meeting to end
        time.sleep(end_time * 60)
        print("Meeting time is over. Exiting...")
        browser.quit()

    except Exception as e:
        print("Error Occurred Please Check")
        logging.error(f"Error during meeting join: {e}")
        browser.quit()
        execl(executable, executable, "zoom.py")
    logging.info("Success")