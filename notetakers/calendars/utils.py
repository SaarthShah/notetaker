
import re

def filter_meeting_events(events):
    """
    Filters events to include only those with valid meeting links.

    Args:
        events (list): A list of event dictionaries.

    Returns:
        list: A list of events that contain a meeting link.
    """

    # Define a regex pattern to match valid meeting URLs
    meeting_url_pattern = re.compile(r'(https?://(?:meet\.google\.com|zoom\.us|teams\.microsoft\.com)/[^\s]+)')

    return [
        event for event in events
        if 'hangoutLink' in event or (
            'description' in event and meeting_url_pattern.search(event['description'])
        )
    ]

def get_meeting_link(event):
    # Check for 'hangoutLink' in the event
    if 'hangoutLink' in event and event['hangoutLink']:
        print("Found hangoutLink:", event['hangoutLink'])
        return event['hangoutLink']
    
    # Define a regex pattern to match valid meeting URLs, allowing optional query parameters
    meeting_url_pattern = re.compile(r'(https?://(?:meet\.google\.com|zoom\.us|teams\.microsoft\.com)/[^\s?]+(?:\?[^\s]*)?)')
    
    # Check for a meeting link in the 'description'
    if 'description' in event:
        match = meeting_url_pattern.search(event['description'])
        if match:
            print("Found link in description:", match.group(0))
            return match.group(0)
    
    # Check for a meeting link in the 'location'
    if 'location' in event:
        match = meeting_url_pattern.search(event['location'])
        if match:
            print("Found link in location:", match.group(0))
            return match.group(0)
    
    # Return an empty string if no meeting link is found
    print("No meeting link found.")
    return ""
