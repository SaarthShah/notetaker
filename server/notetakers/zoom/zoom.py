import logging
import os
import time
from dotenv import load_dotenv
import subprocess
import pwd
import signal
import uuid
import requests

# Load environment variables
load_dotenv()

client_id = os.getenv('ZOOM_CLIENT_ID')
client_secret = os.getenv('ZOOM_CLIENT_SECRET')
deepgram_api_key = os.getenv('DEEPGRAM')

# Logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)  # Set to DEBUG to capture more detailed logs

def join_zoom_meeting(meeting_url, end_time):
    logging.debug("join_zoom_meeting function called")
    transcript = ""
    try:
        # Check if the zoomsdk directory exists
        zoomsdk_path = '/lib/zoomsdk'
        if os.path.isdir(zoomsdk_path):
            logging.info("Starting meeting")
        else:
            raise FileNotFoundError(f"{zoomsdk_path} is not a directory")

        # Get the UID and GID for zoomuser
        zoomuser_info = pwd.getpwnam('root')
        zoomuser_uid = zoomuser_info.pw_uid
        zoomuser_gid = zoomuser_info.pw_gid

        # Generate a random UUID for the raw audio file
        audio_uuid = str(uuid.uuid4())
        audio_file = f"meeting-audio-{audio_uuid}.pcm"
        audio_file_path = os.path.join("/app/out", audio_file)
        logging.info(f"Generated audio file name: {audio_file}")

        # Run the command as zoomuser without using sudo
        executable_path = "/app/build/zoomsdk"
        output_dir = "/app/out"
        if not os.path.exists(output_dir):
            logging.info(f"Creating output directory: {output_dir}")
            os.makedirs(output_dir, exist_ok=True)
        command = [
            executable_path,
            "--leave-time", str(end_time),
            "--client-id", client_id,
            "--client-secret", client_secret,
            "--join-url", meeting_url,
            "RawAudio",
            "--file", audio_file,
            # "--dir", output_dir
        ]
        logging.info(f"Running command: {' '.join(command)}")

        # Print the current directory from which the Zoom SDK is being called
        current_directory = os.getcwd()
        logging.info(f"Current directory: {current_directory}")

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            bufsize=0,
            preexec_fn=lambda: os.setgid(zoomuser_gid) or os.setuid(zoomuser_uid)
        )

        logging.info('Process started, waiting for output...')
        start_time = time.time()
        last_time_check = start_time

        # Read stdout line-by-line in a loop (if you still want real-time logs)
        while True:
            line = process.stdout.readline()
            # If line is empty and the process has ended, break out
            if not line and process.poll() is not None:
                break
            if line.strip():
                try:
                    decoded_line = line.decode('utf-8').strip()
                    logging.info(decoded_line)
                    if "✅ meeting ended" in decoded_line:
                        logging.info("Meeting ended by host. Exiting...")
                        process.send_signal(signal.SIGINT)  # Send Ctrl+C
                        break
                except UnicodeDecodeError:
                    # Ignore decoding errors
                    pass

            # Print time left every 10 seconds
            current_time = time.time()
            if current_time - last_time_check >= 10:
                time_left = end_time * 60 - (current_time - start_time)
                if time_left > 0:
                    logging.info(f"Time left: {int(time_left // 60)} minutes and {int(time_left % 60)} seconds")
                last_time_check = current_time

            # Check meeting time
            if current_time - start_time >= end_time * 60:
                logging.info("Meeting time is over. Exiting...")
                process.send_signal(signal.SIGINT)  # Send Ctrl+C
                break

        # Terminate the subprocess
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                logging.warning("Process did not terminate in time, killing it.")
                process.kill()
                process.wait()
            logging.info("Subprocess terminated after meeting time ended or host ended the meeting.")

        # Now call process.communicate() to safely read any remaining stderr
        _stdout_final, stderr_final = process.communicate(timeout=20)
        if stderr_final:
            try:
                logging.error(f"Error output from process: {stderr_final.decode('utf-8')}")
            except UnicodeDecodeError:
                # Ignore decoding errors
                pass

        # Use Deepgram to generate the transcript
        if os.path.exists(audio_file_path):
            logging.info("Sending audio file to Deepgram for transcription")
            with open(audio_file_path, 'rb') as audio:
                url = "https://api.deepgram.com/v1/listen"
                headers = {
                    'Authorization': f'Token {deepgram_api_key}',
                    'Content-Type': 'audio/wav'  # Ensure the correct audio type is specified
                }
                try:
                    response = requests.post(url, headers=headers, data=audio)
                    response.raise_for_status()  # Raise an error for bad responses
                    transcript_data = response.json()
                    transcript = transcript_data.get('results', {}).get('channels', [{}])[0].get('alternatives', [{}])[0].get('transcript', '')
                    logging.info(f"Transcript: {transcript}")
                except requests.exceptions.HTTPError as http_err:
                    logging.error(f"HTTP error occurred: {http_err} - {response.text}")
                except Exception as err:
                    logging.error(f"An error occurred while getting transcript from Deepgram: {err}")

    except Exception as e:
        logging.error(f"Unexpected error during meeting join: {e}")
    finally:
        logging.info("Exiting the meeting process")

    return transcript
