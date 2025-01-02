import logging
import os
import time
from dotenv import load_dotenv
import subprocess
import pwd

# Load environment variables
load_dotenv()

usernameStr = os.getenv("ZOOM_USERNAME")
passwordStr = os.getenv("ZOOM_PASSWORD")

# Logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)  # Set to DEBUG to capture more detailed logs

def join_zoom_meeting(meeting_url, password, end_time):
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
        command = f'/lib/zoomsdk --join-url "{meeting_url}"'
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

        # Stream the output to a text file
        output_file_path = "zoomsdk_output.txt"
        with open(output_file_path, "w") as output_file:
            try:
                for line in iter(process.stdout.readline, ''):
                    if line.strip():  # Check if the line is not empty
                        logging.info(line.strip())  # Log each line as it becomes available
                        output_file.write(line)  # Write each line to the file
                    else:
                        logging.debug("No output from zoomsdk process.")
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
