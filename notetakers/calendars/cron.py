import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

def upsert_cron_job(task_id, run_time, link, headers, body):
    """
    Schedules or updates a cron job with the given task details.

    If the run_time is not provided, the task is scheduled to run 5 minutes from the current time.

    Args:
        task_id (str): Unique identifier for the task.
        run_time (str): The time at which the task should be executed, in 'YYYY-MM-DD HH:MM:SS' format.
        link (str): The URL to which the task will send a POST request.
        headers (dict): HTTP headers to include in the POST request.
        body (dict): JSON body to include in the POST request.

    Raises:
        ValueError: If the CRON_URL environment variable is not set.
        Exception: If the task scheduling request fails.

    Returns:
        None
    """
    # Calculate the run time 5 minutes from now if not provided
    if not run_time:
        run_time = (datetime.utcnow() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')

    # Define the task details
    task_data = {
        "task_id": task_id,
        "run_time": run_time,
        "link": link,
        "headers": headers,
        "body": body
    }

    # Get the CRON_URL from environment variables
    cron_url = os.getenv("CRON_URL")

    if not cron_url:
        raise ValueError("CRON_URL environment variable is not set")

    # Schedule the task
    response = requests.post(f"{cron_url}/schedule-task", json=task_data)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to schedule task: {response.status_code} - {response.text}")

    # Print the response
    print(response.json())


def delete_cron_job(task_id):
    """
    Deletes a cron job with the given task ID.

    Args:
        task_id (str): Unique identifier for the task to be deleted.

    Raises:
        ValueError: If the CRON_URL environment variable is not set.
        Exception: If the task deletion request fails.

    Returns:
        None
    """
    # Get the CRON_URL from environment variables
    cron_url = os.getenv("CRON_URL")

    if not cron_url:
        raise ValueError("CRON_URL environment variable is not set")

    # Send a request to delete the task
    response = requests.delete(f"{cron_url}/delete-task", params={"task_id": task_id})

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to delete task: {response.status_code} - {response.text}")

    # Print the response
    print(response.json())