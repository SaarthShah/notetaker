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

@app.post('/gcal/notifications')
async def handle_notification(request: Request):
    try:
        # Extract the notification data from the request
        notification_data = await request.json()
        print("Received notification:", notification_data)

        # Always create a new txt file for the notification data
        with open("notification_data.txt", "w") as file:
            file.write(json.dumps(notification_data) + "\n")

        # Check the type of change (add, update, delete)
        event_id = notification_data.get('id')
        event_status = notification_data.get('status')
        event_summary = notification_data.get('summary', '')
        event_description = notification_data.get('description', '')
        event_start = notification_data.get('start', {}).get('dateTime')
        event_end = notification_data.get('end', {}).get('dateTime')
        event_link = notification_data.get('hangoutLink', '')
        event_attendees = json.dumps([attendee['email'] for attendee in notification_data.get('attendees', [])])

        if not event_id or not event_status:
            raise HTTPException(status_code=400, detail="Event ID and status are required")

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
            }, on_conflict=["event_id"]).execute()
            print(f"Event {event_id} added/updated in the database.")
        elif event_status == 'cancelled':
            # Delete the event from the database
            response = supabase.table("calevents").delete().eq("event_id", event_id).execute()
            print(f"Event {event_id} deleted from the database.")

        return JSONResponse({"status": "success"}, status_code=200)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)