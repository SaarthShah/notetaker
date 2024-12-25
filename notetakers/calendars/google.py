import aiohttp
import json 
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import uuid
from .utils import filter_meeting_events
from .cron import upsert_cron_job

from datetime import datetime

load_dotenv(dotenv_path='@.env')

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load Google OAuth client credentials from environment variables
GOOGLE_CLIENT_ID = os.getenv("NEXT_PUBLIC_GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

async def sync_google_calendar(refresh_token: str, user_id: str):
    try:
        print("Starting sync_google_calendar")
        
        # Step 1: Use the refresh token to get a new access token
        access_token = await get_access_token_from_refresh_token(refresh_token)
        if not access_token:
            raise Exception("Failed to obtain access token")
        print(f"Access token obtained: {access_token}")

        # Step 2: Fetch future calendar events
        events, sync_token = await sync_google_calendar_events(access_token)
        if sync_token:
            supabase.table("integrations").update({"google_sync_token": sync_token}).eq("user_id", user_id).execute()
        if events is None:
            raise Exception("Failed to fetch calendar events: No response from server")
        elif not events:
            print("No future events found")
        else:
            print(f"Fetched {len(events)} events")

            # Step 3: Filter events with valid meeting links
            meet_events = filter_meeting_events(events)
            print(f"Found {len(meet_events)} events with valid meeting links")

            # Step 4: Set up subscriptions for changes in events
            # NOTE: Figure out a way to delete these calendars event handlers once they are created
            try:
                await setup_event_subscriptions(access_token, user_id)
                print("Event subscriptions set up")
            except Exception as e:
                print(f"Failed to set up event subscription, but continuing: {e}")

            # Step 5: Push events to Supabase
            for event in meet_events:
                event_data = {
                    "user_id": user_id,
                    "event_id": event['id'],
                    "summary": event.get('summary', ''),
                    "description": event.get('description', ''),
                    "start_time": event['start']['dateTime'],
                    "end_time": event['end']['dateTime'],
                    "link": event.get('hangoutLink', event.get('location', '')),
                    "attendees": json.dumps([attendee['email'] for attendee in event.get('attendees', [])]),
                }
                supabase.table("calevents").upsert(event_data, on_conflict=["event_id"]).execute()
                await upsert_cron_job(
                    task_id=event['id'],
                    run_time=event['start']['dateTime'],
                    link=os.getenv("SERVER_ENDPOINT")+"/join-meet",
                    headers={"Content-Type": "application/json"},
                    body={
                    "meet_link": event.get('hangoutLink', event.get('location', '')),
                    "end_time": event['end']['dateTime'],
                    "user_id": user_id
                    }
                )
            print('pushed all to supabase')
    except Exception as e:
        print(f"An error occurred: {e}")

async def get_access_token_from_refresh_token(refresh_token: str) -> str:
    print("Getting access token from refresh token")
    url = "https://oauth2.googleapis.com/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as response:
            response_data = await response.json()
            access_token = response_data.get("access_token")
            return access_token

async def fetch_calendar_events(access_token: str) -> list:
    print("Fetching future calendar events")
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={now}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                error_message = await response.text()
                print(f"Failed to fetch events, response status: {response.status}, error: {error_message}")
                return None
            response_data = await response.json()
            return response_data.get("items", [])

async def sync_google_calendar_events(access_token: str, sync_token: str = None):
    print("Starting Google Calendar sync")
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "maxResults": 10000
    }
    
    if sync_token:
        print("Performing incremental sync.")
        params["syncToken"] = sync_token
    else:
        print("Performing full sync from today into the future.")
        today = datetime.utcnow().isoformat() + 'Z'
        params["timeMin"] = today

    page_token = None
    events = []
    while True:
        if page_token:
            params["pageToken"] = page_token

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 410:
                    # Sync token is invalid, perform a full sync
                    print("Invalid sync token, clearing event store and re-syncing.")
                    return await sync_google_calendar_events(access_token)
                elif response.status != 200:
                    error_message = await response.text()
                    print(f"Failed to sync events, response status: {response.status}, error: {error_message}")
                    raise Exception(f"Failed to sync events: {error_message}")

                response_data = await response.json()
                events.extend(response_data.get("items", []))
                page_token = response_data.get("nextPageToken")
                if not page_token:
                    break

    # Store the sync token from the last request to be used during the next execution.
    new_sync_token = response_data.get("nextSyncToken")
    print("Sync complete.")
    return events, new_sync_token


async def setup_event_subscriptions(access_token: str, user_id: str):
    print("Creating a new event subscription")
    unique_channel_id = str(uuid.uuid4())  # Generate a unique channel ID
    watch_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events/watch"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "id": unique_channel_id,
        "type": "web_hook",
        "address": os.getenv('SERVER_ENDPOINT') + "/gcal-notifications",
        "token": user_id
    }

    async with aiohttp.ClientSession() as session:
        # Setting up a new event subscription
        async with session.post(watch_url, headers=headers, json=data) as response:
            response_data = await response.json()
            if response.status != 200:
                error_message = response_data.get("error", {}).get("message", "Unknown error")
                print(f"Failed to create event subscription, response status: {response.status}, error: {error_message}")
                raise Exception(f"Failed to create event subscription: {error_message}")
            else:
                print("Event subscription created successfully")
                print(f"New subscription set for channel ID: {unique_channel_id}")