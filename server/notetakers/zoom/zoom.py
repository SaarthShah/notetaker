import logging
import os
import time
import re
import random
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
    # Remove headless mode
    # options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1920,1080")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_setting_values.notifications": 1
    })
    options.add_argument("--disable-blink-features=AutomationControlled")

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

    # Inject JavaScript to bypass headless detection
    def inject_js(driver):
        js_code = """
        Object.defineProperty(navigator, 'languages', {
            get: function() {
                return ['en-US', 'en'];
            },
        });
        Object.defineProperty(navigator, 'plugins', {
            get: function() {
                return [1, 2, 3, 4, 5];
            },
        });
        const getParameter = WebGLRenderingContext.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Open Source Technology Center';
            }
            if (parameter === 37446) {
                return 'Mesa DRI Intel(R) Ivybridge Mobile ';
            }
            return getParameter(parameter);
        };
        ['height', 'width'].forEach(property => {
            const imageDescriptor = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, property);
            Object.defineProperty(HTMLImageElement.prototype, property, {
                ...imageDescriptor,
                get: function() {
                    if (this.complete && this.naturalHeight == 0) {
                        return 20;
                    }
                    return imageDescriptor.get.apply(this);
                },
            });
        });
        const elementDescriptor = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetHeight');
        Object.defineProperty(HTMLDivElement.prototype, 'offsetHeight', {
            ...elementDescriptor,
            get: function() {
                if (this.id === 'modernizr') {
                    return 1;
                }
                return elementDescriptor.get.apply(this);
            },
        });
        """
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": js_code})

    inject_js(browser)

    try:
        print("Typing...")
        time.sleep(random.uniform(1, 3))  # Random delay
        browser.get('https://zoom.us/signin')
        time.sleep(random.uniform(1, 3))  # Random delay
        browser.find_element(By.ID, 'email').send_keys(usernameStr)
        time.sleep(random.uniform(1, 3))  # Random delay
        browser.find_element(By.ID, 'password').send_keys(passwordStr)
        time.sleep(random.uniform(1, 3))  # Random delay
        browser.find_element(By.XPATH, '//button[@id="js_btn_login"]').click()
        time.sleep(random.uniform(3, 5))  # Random delay
        browser.save_screenshot("pre_login_screenshot.png")
        browser.save_screenshot("post_login_screenshot.png")
        print("Screenshot after login taken")
        time.sleep(random.uniform(3, 5))  # Random delay
        browser.save_screenshot("pre_meeting_screenshot.png")
        print("Screenshot before meeting taken")
        print("Logged In!")
        meeting_number_match = re.search(r'/j/(\d+)', meeting_url)
        if not meeting_number_match:
            print("Invalid meeting URL.")
            return
        meeting_number = meeting_number_match.group(1)
        time.sleep(random.uniform(1, 3))  # Random delay
        browser.get(f'https://app.zoom.us/wc/{meeting_number}/join?fromPWA=1&pwd={password}')
        time.sleep(random.uniform(3, 5))  # Random delay
        browser.save_screenshot("meeting_join_screenshot.png")
        browser.switch_to.frame(browser.find_element(By.TAG_NAME, 'iframe'))
        browser.save_screenshot("before_join_screenshot.png")
        print("Photo before clicking join button taken")
        join_button = browser.find_element(By.XPATH, '//button[contains(@class, "zm-btn")]')
        join_button.click()
        time.sleep(random.uniform(3, 5))  # Random delay
        browser.save_screenshot("after_join_screenshot.png")
        print("Photo after clicking join button taken")
        browser.save_screenshot("meeting_attendance_screenshot.png")
        print("Attending Your Meeting")

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