import logging
import os
import time
from dotenv import load_dotenv
import subprocess

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
    try:
        # Check if the zoomsdk directory exists and list its contents
        zoomsdk_path = '/lib/zoomsdk'
        if os.path.isdir(zoomsdk_path):
            logging.info("Starting meeting")
        else:
            raise FileNotFoundError(f"{zoomsdk_path} is not a directory")

        # Ensure all files in the zoomsdk directory are executable
        for root, dirs, files in os.walk(zoomsdk_path):
            for file in files:
                file_path = os.path.join(root, file)
                subprocess.run(['chmod', '+x', file_path], check=True)

        # Execute the zoomsdk binary with the provided meeting URL
        zoomsdk_binary = os.path.join(zoomsdk_path, 'libmeetingsdk.so')  # Assuming this is the binary to execute
        process = subprocess.Popen(
            [zoomsdk_binary, '--join-url', meeting_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # Ensures the output is decoded into text instead of bytes
        )

        # Stream the output
        try:
            for line in iter(process.stdout.readline, ''):
                logging.info(line.strip())  # Log each line as it becomes available
        except KeyboardInterrupt:
            logging.info("Force Exiting Meeting.")
        finally:
            process.terminate()
            process.wait()

        # Check if the process had any errors
        stderr_output = process.stderr.read()
        if stderr_output:
            logging.error(f"Error output from process: {stderr_output}")

        # Wait for the meeting to end
        time.sleep(end_time * 60)
        logging.info("Meeting time is over. Exiting...")

        # Forcefully terminate the process if it's still running
        if process.poll() is None:  # Check if the process is still running
            process.kill()
            process.wait()
            logging.info("Subprocess forcefully terminated after meeting time ended.")

    except FileNotFoundError as fnf_error:
        logging.error(f"File not found error: {fnf_error}")
    except subprocess.CalledProcessError as cpe_error:
        logging.error(f"Runtime error: Failed to execute zoomsdk binary with error: {cpe_error}")
        if cpe_error.returncode == -11:  # Check for segmentation fault
            logging.error("Segmentation fault occurred while executing the zoomsdk binary.")
    except PermissionError as perm_error:
        logging.error(f"Permission error: {perm_error}")
    except Exception as e:
        logging.error(f"Unexpected error during meeting join: {e}")
    finally:
        logging.info("Exiting the meeting process")

join_zoom_meeting('https://us05web.zoom.us/j/88104465816?pwd=Wj8C91CC4DqUtyyGRAwgjLjgOHDN8I.1','',0.2)
