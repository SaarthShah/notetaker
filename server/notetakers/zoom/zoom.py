import logging
import os
import time
from dotenv import load_dotenv
import subprocess
import pwd

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

        try:
            start_time = time.time()
            for line in iter(process.stdout.readline, ''):
                if line.strip():  # Check if the line is not empty
                    logging.info(line.strip())  # Log each line as it becomes available
                    if "✅ meeting ended" in line:
                        logging.info("Meeting ended by host. Exiting...")
                        break
                else:
                    logging.debug("No output from zoomsdk process.")
                
                # Check if the meeting time has elapsed
                if (time.time() - start_time) >= (end_time * 60):
                    logging.info("Meeting time is over. Exiting...")
                    break

        except KeyboardInterrupt:
            logging.info("Force Exiting Meeting.")
        finally:
            # Ensure the process is terminated
            if process.poll() is None:  # Check if the process is still running
                process.terminate()
                try:
                    process.wait(timeout=10)  # Wait for the process to terminate
                except subprocess.TimeoutExpired:
                    logging.warning("Process did not terminate in time, killing it.")
                    process.kill()
                    process.wait()
                logging.info("Subprocess terminated after meeting time ended or host ended the meeting.")

        # Check if the process had any errors
        stderr_output = process.stderr.read()
        if stderr_output:
            logging.error(f"Error output from process: {stderr_output}")

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
    print('here')
    return ""
