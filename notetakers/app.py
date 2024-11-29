from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from google_meet.gmeet import join_meet
from agent.cleanup import clean_google_meet_transcript
from agent.summarizer import summarize_transcript

app = FastAPI()

class MeetRequest(BaseModel):
    meet_link: str
    end_time: int

@app.post("/join-meet")
async def join_meet_endpoint(request: MeetRequest):
    if not request.meet_link:
        raise HTTPException(status_code=400, detail="Meet link is required")
    if request.end_time <= 0:
        raise HTTPException(status_code=400, detail="End time must be greater than 0")
    
    transcript = await join_meet(request.meet_link, request.end_time)
    print(transcript)
    
    if not transcript:
        return {"summary": "Agent was never accepted into the call", "cleaned_transcript": []}
    
    cleaned_transcript = clean_google_meet_transcript(transcript)
    print(cleaned_transcript)
    
    cleaned_transcript_text = '\n'.join([f"{entry['user']} at {entry['time']}: {entry['content']}" for entry in cleaned_transcript])
    print(cleaned_transcript_text)
    
    summary = summarize_transcript(cleaned_transcript_text)
    return {"summary": summary, "cleaned_transcript": cleaned_transcript}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)