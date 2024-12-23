from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn
from datetime import datetime
from google_meet.gmeet import join_meet
from agent.cleanup import clean_google_meet_transcript
from agent.summarizer import summarize_transcript
from supabase import create_client, Client

import os
import json
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from calendars.google import get_access_token_from_refresh_token, sync_google_calendar_events, sync_google_calendar
from calendars.utils import filter_meeting_events
from calendars.cron import upsert_cron_job

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

@app.post('/gcal-notifications')
async def handle_notification(request: Request):
    try:
        # Extract headers from the request
        headers = request.headers
        channel_id = headers.get('X-Goog-Channel-ID')
        resource_state = headers.get('X-Goog-Resource-State')
        user_id = headers.get('X-Goog-Channel-Token')  # Extract user_id from token

        print("Received notification headers:", headers)

        # # Always create a new txt file for the notification headers
        # with open("notification_headers.txt", "w") as file:
        #     file.write(json.dumps(dict(headers)) + "\n")
        # print("Notification headers written to file.")

        if resource_state not in ['exists', 'sync']:
            print("Resource state is not 'exists'.")
            raise HTTPException(status_code=400, detail="Resource state is not 'exists'")

        if not channel_id:
            print("Channel ID is missing.")
            raise HTTPException(status_code=400, detail="Channel ID is required")

        if not user_id:
            print("User ID is missing in token.")
            raise HTTPException(status_code=400, detail="User ID is required in token")

        # Fetch the Google refresh token and sync token from the 'integrations' table using the user_id
        print(f"Fetching Google tokens for user_id: {user_id}")
        response = supabase.table("integrations").select("google_token", "google_sync_token").eq("user_id", user_id).execute()
        if not response.data:
            print("Google tokens not found for the given user_id.")
            raise HTTPException(status_code=404, detail="Google tokens not found for the given user_id")

        google_refresh_token = response.data[0]['google_token']['refresh_token']
        sync_token = response.data[0].get('google_sync_token')
        print("Google tokens retrieved successfully.")

        # Use the refresh token to get a new access token
        print("Obtaining new access token using the refresh token.")
        access_token = await get_access_token_from_refresh_token(google_refresh_token)
        if not access_token:
            print("Failed to obtain access token.")
            raise HTTPException(status_code=500, detail="Failed to obtain access token")
        print("Access token obtained successfully.")

        # Perform a sync using the sync token
        print("Performing sync using the sync token.")
        events, new_sync_token = await sync_google_calendar_events(access_token, sync_token)
        if new_sync_token:
            supabase.table("integrations").update({"google_sync_token": new_sync_token}).eq("user_id", user_id).execute()
        print("Sync completed successfully.")

        # Filter events with valid meeting links
        meet_events = filter_meeting_events(events)
        
        # Insert or update meet events in the Supabase database
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
                link=os.get_env("SEVER_ENDPOINT")+"/join-meet",
                headers={"Content-Type": "application/json"},
                body=event_data
            )
        
        # Delete any non-meet or canceled events from the Supabase database
        non_meet_event_ids = [event['id'] for event in events if event not in meet_events or event.get('status') == 'cancelled']
        if non_meet_event_ids:
            supabase.table("calevents").delete().in_("event_id", non_meet_event_ids).execute()
        
        print('Events with valid meeting links upserted/updated in Supabase successfully.')

        return JSONResponse({"status": "success"}, status_code=200)
    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Request URL: {request.url}")
        print(f"Request Method: {request.method}")
        print(f"Request Headers: {request.headers}")
        print(f"Request Query Params: {request.query_params}")
        try:
            request_body = await request.body()
            print(f"Request Body (text): {request_body.decode('utf-8')}")
        except Exception as e:
            print(f"Request Body: Unable to read body, error: {e}")
        raise HTTPException(status_code=400, detail="Invalid request")

@app.post("/sync-calendar")
async def sync_calendar(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")

        if not user_id:
            raise HTTPException(status_code=400, detail="Missing user_id")

        # Fetch the Google refresh token from the 'integrations' table using the user_id
        response = supabase.table("integrations").select("google_token").eq("user_id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Google token not found for the given user_id")

        google_refresh_token = response.data[0]['google_token']['refresh_token']

        # Call the sync_google_calendar function
        await sync_google_calendar(google_refresh_token, user_id)

        return JSONResponse({"status": "success"}, status_code=200)

    except Exception as e:
        print(f"An error occurred: {e}")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=400)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)