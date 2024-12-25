import aiohttp
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from dateutil import parser
import pytz

load_dotenv(dotenv_path='@.env')

async def upsert_cron_job(task_id, run_time, link, headers, body):
    """
    Schedules or updates a cron job with the given task details.

    If the run_time is not provided, the task is scheduled to run 5 minutes from the current time.

    Args:
        task_id (str): Unique identifier for the task.
        run_time (str): The time at which the task should be executed, in ISO 8601 format.
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
    print(run_time)
    if not run_time:
        run_time = (datetime.utcnow() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
    else:
        # Attempt to parse the run_time and convert to UTC format
        try:
            # Parse the run_time using dateutil.parser
            parsed_time = parser.isoparse(run_time)
            # Convert to UTC
            run_time_utc = parsed_time.astimezone(pytz.utc)
            run_time = run_time_utc.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError("Invalid run_time format. Expected ISO 8601 format.")

    # Define the task details
    task_data = {
        "task_id": task_id,
        "run_time": run_time,
        "link": link,
        "headers": headers,
        "body": body
    }

    # Get the CRON_URL from environment variables
    cron_url = os.environ.get("CRON_URL")

    if not cron_url:
        raise ValueError("CRON_URL environment variable is not set")

    # Schedule the task
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{cron_url}/schedule-task", json=task_data) as response:
            # Check if the request was successful
            if response.status != 200:
                error_detail = await response.text()
                raise Exception(f"Failed to schedule task: {response.status} - {error_detail}")

            # Print the response
            print(await response.json())


async def delete_cron_job(task_id):
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
    cron_url = os.environ.get("CRON_URL")

    if not cron_url:
        raise ValueError("CRON_URL environment variable is not set")

    # Send a request to delete the task
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{cron_url}/delete-task", params={"task_id": task_id}) as response:
            # Check if the request was successful
            if response.status != 200:
                error_detail = await response.text()
                raise Exception(f"Failed to delete task: {response.status} - {error_detail}")

            # Print the response
            print(await response.json())