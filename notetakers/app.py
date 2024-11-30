from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from datetime import datetime
from google_meet.gmeet import join_meet
from agent.cleanup import clean_google_meet_transcript
from agent.summarizer import summarize_transcript
from supabase import create_client, Client
import aiohttp

import os
import json
from dotenv import load_dotenv
from flask import request, jsonify

load_dotenv()

app = FastAPI()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class MeetRequest(BaseModel):
    meet_link: str
    end_time: int
    user_id: str

@app.post("/join-meet")
async def join_meet_endpoint(request: MeetRequest):
    if not request.meet_link:
        raise HTTPException(status_code=400, detail="Meet link is required")
    if request.end_time <= 0:
        raise HTTPException(status_code=400, detail="End time must be greater than 0")
    
    start_time = datetime.now()
    transcript = await join_meet(request.meet_link, request.end_time)

    # Calculate duration
    end_time = datetime.now()
    
    if not transcript:
        return {"summary": "Agent was never accepted into the call", "cleaned_transcript": []}
    
    cleaned_transcript = clean_google_meet_transcript(transcript)
    
    cleaned_transcript_text = '\n'.join([f"{entry['user']} at {entry['time']}: {entry['content']}" for entry in cleaned_transcript])
    
    summary = summarize_transcript(cleaned_transcript_text)
    

    # Add to Supabase
    data = {
        "user_id": request.user_id,
        "meeting_link": request.meet_link,
        "summary": json.dumps(summary),
        "transcript": json.dumps(cleaned_transcript),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "attendees": json.dumps(list(set([entry['user'] for entry in cleaned_transcript]))),
        "type":"gmeet"
    }
    response = supabase.table("meetings").insert(data).execute()
    print(response)
    
    return {"summary": summary, "cleaned_transcript": cleaned_transcript}

async def sync_google_calendar(refresh_token: str, user_id: str):
    # Step 1: Use the refresh token to get a new access token
    access_token = await get_access_token_from_refresh_token(refresh_token)

    # Step 2: Fetch all calendar events
    events = await fetch_calendar_events(access_token)

    # Step 3: Filter events with Google Meet links
    meet_events = [event for event in events if 'hangoutLink' in event]

    # Step 4: Set up subscriptions for changes in events
    await setup_event_subscriptions(access_token, user_id)

    # Step 5: Push events to Supabase
    for event in meet_events:
        event_data = {
            "user_id": user_id,
            "event_id": event['id'],
            "summary": event.get('summary', ''),
            "description": event.get('description', ''),
            "start_time": event['start']['dateTime'],
            "end_time": event['end']['dateTime'],
            "meet_link": event['hangoutLink'],
            "attendees": json.dumps([attendee['email'] for attendee in event.get('attendees', [])]),
        }
        response = supabase.table("calendar_events").insert(event_data).execute()
        print(response)

async def get_access_token_from_refresh_token(refresh_token: str) -> str:
    url = "https://oauth2.googleapis.com/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET",
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as response:
            response_data = await response.json()
            return response_data.get("access_token")

async def fetch_calendar_events(access_token: str) -> list:
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response_data = await response.json()
            return response_data.get("items", [])

async def setup_event_subscriptions(access_token: str, user_id: str):
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events/watch"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "id": f"channel-{user_id}",
        "type": "web_hook",
        "address": "https://yourdomain.com/notifications"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status != 200:
                raise Exception("Failed to set up event subscription")

@app.route('/gcal/notifications', methods=['POST'])
def handle_notification():
    # Extract the notification data from the request
    notification_data = request.json
    print("Received notification:", notification_data)

    # Check the type of change (add, update, delete)
    event_id = notification_data.get('id')
    event_status = notification_data.get('status')
    event_summary = notification_data.get('summary', '')
    event_description = notification_data.get('description', '')
    event_start = notification_data.get('start', {}).get('dateTime')
    event_end = notification_data.get('end', {}).get('dateTime')
    event_link = notification_data.get('hangoutLink', '')
    event_attendees = json.dumps([attendee['email'] for attendee in notification_data.get('attendees', [])])

    if event_status == 'confirmed':
        # Add or update the event in the database
        response = supabase.table("calevents").upsert({
            "event_id": event_id,
            "summary": event_summary,
            "description": event_description,
            "start_time": event_start,
            "end_time": event_end,
            "link": event_link,
            "attendees": event_attendees
        }).execute()
        print(f"Event {event_id} added/updated in the database.")
    elif event_status == 'cancelled':
        # Delete the event from the database
        response = supabase.table("calevents").delete().eq("event_id", event_id).execute()
        print(f"Event {event_id} deleted from the database.")

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)