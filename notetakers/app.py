from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from datetime import datetime
from google_meet.gmeet import join_meet
from agent.cleanup import clean_google_meet_transcript
from agent.summarizer import summarize_transcript
from supabase import create_client, Client

import os
from dotenv import load_dotenv

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
    
    if not transcript:
        return {"summary": "Agent was never accepted into the call", "cleaned_transcript": []}
    
    cleaned_transcript = clean_google_meet_transcript(transcript)
    
    cleaned_transcript_text = '\n'.join([f"{entry['user']} at {entry['time']}: {entry['content']}" for entry in cleaned_transcript])
    
    summary = summarize_transcript(cleaned_transcript_text)
    
    # Calculate duration
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Add to Supabase
    data = {
        "user_id": request.user_id,
        "meet_link": request.meet_link,
        "summary": summary,
        "cleaned_transcript": cleaned_transcript,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration": duration
    }
    response = supabase.table("meet_summaries").insert(data).execute()
    print(response)
    
    return {"summary": summary, "cleaned_transcript": cleaned_transcript}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)