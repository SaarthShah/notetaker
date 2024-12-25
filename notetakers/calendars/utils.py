
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