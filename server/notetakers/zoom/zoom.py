import logging
import os
import time
import re
from os import execl
from sys import executable
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    options.add_argument("--headless=new")  # Use the new headless mode
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1200,800")
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.media_stream_mic": 2,     # 1:allow, 2:block
        "profile.default_content_setting_values.media_stream_camera": 2,
        "profile.default_content_setting_values.notifications": 2
    })
    options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent detection

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
        time.sleep(2)  # Artificial delay
        browser.get('https://zoom.us/signin')
        time.sleep(1)  # Artificial delay
        browser.find_element(By.ID, 'email').send_keys(usernameStr)
        time.sleep(1)  # Artificial delay
        browser.find_element(By.ID, 'password').send_keys(passwordStr)
        time.sleep(1)  # Artificial delay
        browser.save_screenshot("login_screenshot.png")
        print("Uploading photo...")
        time.sleep(1)  # Artificial delay
        print("Photo uploaded")
        browser.find_element(By.XPATH, '//button[@id="js_btn_login"]').click()
        browser.save_screenshot("pre_login_screenshot.png")
        WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.XPATH, '//div[@id="js_btn_login"]')))
        
        browser.save_screenshot("post_login_screenshot.png")
        print("Screenshot after login taken")
        time.sleep(5)
        browser.save_screenshot("pre_meeting_screenshot.png")
        print("Screenshot before meeting taken")
        print("Logged In!")
        meeting_number_match = re.search(r'/j/(\d+)', meeting_url)
        if not meeting_number_match:
            print("Invalid meeting URL.")
            return
        meeting_number = meeting_number_match.group(1)
        time.sleep(1)  # Artificial delay
        browser.get(f'https://app.zoom.us/wc/{meeting_number}/join?fromPWA=1&pwd={password}')
        time.sleep(5)
        browser.save_screenshot("meeting_join_screenshot.png")
        print("Uploading photo...")
        time.sleep(1)  # Artificial delay
        print("Photo uploaded")
        browser.switch_to.frame(browser.find_element(By.TAG_NAME, 'iframe'))
        browser.save_screenshot("before_join_screenshot.png")
        print("Photo before clicking join button taken")
        join_button = browser.find_element(By.XPATH, '//button[contains(@class, "zm-btn")]')
        join_button.click()
        time.sleep(5)
        browser.save_screenshot("after_join_screenshot.png")
        print("Photo after clicking join button taken")
        browser.save_screenshot("meeting_attendance_screenshot.png")
        print("Uploading photo...")
        time.sleep(1)  # Artificial delay
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