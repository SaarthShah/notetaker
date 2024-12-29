import os
import time
import json
import requests
import asyncio
import websockets
from base64 import b64encode
from flask import Flask, jsonify, request
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import jwt

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Helper function to get Zoom API access token
def get_zoom_api_access_token():
    try:
        base_64 = b64encode(f"{os.getenv('CLIENT_ID')}:{os.getenv('CLIENT_SECRET')}".encode()).decode()
        response = requests.post(
            f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={os.getenv('ACCOUNT_ID')}",
            headers={"Authorization": f"Basic {base_64}"}
        )
        response.raise_for_status()
        return response.json().get('access_token')
    except requests.RequestException as e:
        print(e)

# Helper function to make Zoom API requests
def make_zoom_api_request(method, endpoint, data=None):
    try:
        token = get_zoom_api_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.request(method, endpoint, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error: {e}")

# Route to generate SDK signature
@app.route('/api/zoom/msig', methods=['POST'])
def generate_sdk_signature():
    iat = int(time.time()) - 30
    exp = iat + 60 * 60 * 2
    payload = {
        "sdkKey": os.getenv("ZOOM_MSDK_KEY"),
        "mn": request.json.get('meetingNumber'),
        "role": request.json.get('role'),
        "iat": iat,
        "exp": exp,
        "tokenExp": exp
    }
    signature = jwt.encode(payload, os.getenv("ZOOM_MSDK_SECRET"), algorithm="HS256")
    return jsonify({"signature": signature})

# Route to get meeting details
@app.route('/api/zoom/mnum', methods=['GET'])
def get_meeting_details():
    try:
        meeting_number = request.args.get('meetingNumber')
        meeting_details = make_zoom_api_request("GET", f"https://api.zoom.us/v2/meetings/{meeting_number}")
        return jsonify(meeting_details)
    except Exception as e:
        return str(e), 400

# Route to get host ZAK token
@app.route('/api/zoom/hzak', methods=['GET'])
def get_host_zak_token():
    try:
        token = make_zoom_api_request("GET", "https://api.zoom.us/v2/users/me/token?type=zak")
        return jsonify({"token": token})
    except Exception as e:
        return str(e), 400

# WebSocket handler
async def websocket_handler():
    uri = "ws://your.websocket.server"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"module": "heartbeat"}))
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print("Received data:", data)
            await asyncio.sleep(30)
            await websocket.send(json.dumps({"module": "heartbeat"}))

# Function to click join meeting button using Selenium
def join_zoom_meeting(meeting_link, meeting_password):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--use-fake-ui-for-media-stream")
    service = Service('/path/to/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(meeting_link)
        driver.implicitly_wait(10)
        
        # Enter the meeting password
        password_input = driver.find_element(By.ID, "password")
        password_input.send_keys(meeting_password)
        
        # Click the join button
        join_button = driver.find_element(By.CSS_SELECTOR, "button")
        join_button.click()
        
        # Wait for the audio button to appear and click it
        time.sleep(2)
        audio_button = driver.find_element(By.CSS_SELECTOR, ".join-audio-by-voip__join-btn")
        audio_button.click()
    finally:
        driver.quit()

# Main entry point
if __name__ == '__main__':
    port = int(os.getenv("PORT", 30015))
    app.run(port=port)
    asyncio.run(websocket_handler())