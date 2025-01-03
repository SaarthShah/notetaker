import logging
import os
import time
from dotenv import load_dotenv
import subprocess
import pwd
import signal

# Load environment variables
load_dotenv()

client_id = os.getenv('ZOOM_CLIENT_ID')
client_secret = os.getenv('ZOOM_CLIENT_SECRET')

# Logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)  # Set to DEBUG to capture more detailed logs

def join_zoom_meeting(meeting_url, end_time):
    logging.debug("join_zoom_meeting function called")
    try:
        # Check if the zoomsdk directory exists
        zoomsdk_path = '/lib/zoomsdk'
        if os.path.isdir(zoomsdk_path):
            logging.info("Starting meeting")
        else:
            raise FileNotFoundError(f"{zoomsdk_path} is not a directory")

        # Get the UID and GID for zoomuser
        zoomuser_info = pwd.getpwnam('zoomuser')
        zoomuser_uid = zoomuser_info.pw_uid
        zoomuser_gid = zoomuser_info.pw_gid

        # Run the command as zoomuser without using sudo
        executable_path = "/app/zoom-sdk/build/zoomsdk"
        command = f'{executable_path} --join-url "{meeting_url}" --client-id {client_id} --client-secret {client_secret}'
        logging.info(f"Running command: {command}")

        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Ensures the output is decoded into text instead of bytes
            bufsize=1,  # Line buffering
            preexec_fn=lambda: os.setgid(zoomuser_gid) or os.setuid(zoomuser_uid)
        )

        logging.info('Process started, waiting for output...')
        start_time = time.time()

        # Read stdout line-by-line in a loop (if you still want real-time logs)
        while True:
            line = process.stdout.readline()
            # If line is empty and the process has ended, break out
            if not line and process.poll() is not None:
                break
            if line.strip():
                logging.info(line.strip())
                if "✅ meeting ended" in line:
                    logging.info("Meeting ended by host. Exiting...")
                    process.send_signal(signal.SIGINT)  # Send Ctrl+C
                    break

            # Check meeting time
            if time.time() - start_time >= end_time * 60:
                logging.info("Meeting time is over. Exiting...")
                process.send_signal(signal.SIGINT)  # Send Ctrl+C
                break

        # Terminate the subprocess
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logging.warning("Process did not terminate in time, killing it.")
                process.kill()
                process.wait()
            logging.info("Subprocess terminated after meeting time ended or host ended the meeting.")

        # Now call process.communicate() to safely read any remaining stderr
        _stdout_final, stderr_final = process.communicate(timeout=5)
        if stderr_final:
            logging.error(f"Error output from process: {stderr_final}")

    except Exception as e:
        logging.error(f"Unexpected error during meeting join: {e}")
    finally:
        logging.info("Exiting the meeting process")

    print('here')
    return ""
