def filter_meeting_events(events):
    return [event for event in events if 'hangoutLink' in event or ('location' in event and any(url in event['location'] for url in ['meet.google.com', 'zoom.us', 'teams.microsoft.com']))]


