from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from google_meet.gmeet import join_meet

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
    await join_meet(request.meet_link, request.end_time)
    return {"message": "Meeting joined and transcript captured successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)