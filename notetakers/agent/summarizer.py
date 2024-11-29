from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

client = OpenAI()

class SummaryEvent(BaseModel):
    summary: str
    action_items: list[str]

def summarize_transcript(transcript, prompt=""):
    completion = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": "Extract a detailed summary and action items from the transcript, do not add things from your end, just observe the transcript to generate summary and next steps" + prompt},
        {"role": "user", "content": transcript}
    ],
        response_format=SummaryEvent,
    )

    event = completion.choices[0].message.parsed
    return {"summary": event.summary,
            "action_items": event.action_items}