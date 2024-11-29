from pydantic import BaseModel
from openai import OpenAI

client = OpenAI()

class SummaryEvent(BaseModel):
    summary: str
    action_items: list[str]

def summarize_transcript(transcript, prompt=""):
    completion = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": "Extract a detailed summary and action items from the transcript" + prompt},
        {"role": "user", "content": transcript}
    ],
        response_format=SummaryEvent,
    )

    event = completion.choices[0].message.parsed
    return {"summary": event.summary,
            "action_items": event.action_items}