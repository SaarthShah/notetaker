import aiohttp
import json 
from supabase import create_client, Client
import uuid
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

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
        events = await fetch_calendar_events(access_token)
        if events is None:
            raise Exception("Failed to fetch calendar events: No response from server")
        elif not events:
            print("No future events found")
        else:
            print(f"Fetched {len(events)} events")

            # Step 3: Filter events with valid meeting links
            meet_events = [event for event in events if 'hangoutLink' in event or 'location' in event and any(url in event['location'] for url in ['meet.google.com', 'zoom.us', 'teams.microsoft.com'])]
            print(f"Found {len(meet_events)} events with valid meeting links")

            # Step 4: Set up subscriptions for changes in events
            await setup_event_subscriptions(access_token, user_id)
            print("Event subscriptions set up")

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

async def setup_event_subscriptions(access_token: str, user_id: str):
    print("Setting up event subscriptions")
    unique_channel_id = f"channel-{user_id}-{uuid.uuid4()}"  # Generate a unique channel ID
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events/watch"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "id": unique_channel_id,
        "type": "web_hook",
        "address": "https://b2ce-2601-644-8000-5020-ac92-7955-944b-c447.ngrok-free.app/gcal/notifications"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            response_data = await response.json()
            if response.status != 200:
                error_message = response_data.get("error", {}).get("message", "Unknown error")
                print(f"Failed to set up event subscription, response status: {response.status}, error: {error_message}")
                raise Exception(f"Failed to set up event subscription: {error_message}")
            else:
                print("Event subscription set up successfully")

# Commented out the direct call to the async function
if __name__ == "__main__":
    import asyncio
    asyncio.run(sync_google_calendar('1//06gVSfDNTDylGCgYIARAAGAYSNwF-L9IrGdh3BgDbd0C0Ysb9A58q5d6FUm9lkhyzWEA0IOyv1DGwoUIiVBmaHwsqa05PFp2q1KE', 'b63143f6-ce59-465f-b166-4fe7139cd381'))