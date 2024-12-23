def filter_meeting_events(events):
    """
    Filters events to include only those with valid meeting links.

    Args:
        events (list): A list of event dictionaries.

    Returns:
        list: A list of events that contain a meeting link.
    """
    valid_urls = ['meet.google.com', 'zoom.us', 'teams.microsoft.com']
    return [
        event for event in events
        if 'hangoutLink' in event or (
            'location' in event and any(url in event['location'] for url in valid_urls)
        )
    ]