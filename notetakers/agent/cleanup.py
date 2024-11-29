from datetime import datetime

def clean_google_meet_transcript(transcript):
    """
    Cleans the transcript by removing repeated sentences and buildup from previously spoken content,
    and only considers statements spoken at least 10 seconds apart for each user.

    Args:
    transcript (list): A list of dictionaries with keys: 'personName', 'timeStamp', 'transcriptText'.

    Returns:
    list: A list of dictionaries with keys: 'date', 'time', 'user', 'content'.
    """
    cleaned_statements = []

    # Dictionary to track sentences spoken by each user
    user_sentences = {}
    # Dictionary to track the last timestamp of each user's statement
    last_user_timestamp = {}

    for entry in transcript:
        user = entry['personName']
        timestamp = datetime.strptime(entry['timeStamp'], '%Y-%m-%d %H:%M:%S')
        content = entry['transcriptText'].strip()

        # Check if this user's statement is at least 10 seconds apart
        if user in last_user_timestamp and (timestamp - last_user_timestamp[user]).total_seconds() < 10:
            continue  # Skip this statement if within 10 seconds

        # Split content into sentences
        if isinstance(content, str):
            sentences = [sentence.strip() for sentence in content.split('. ') if sentence.strip()]
        else:
            sentences = []

        # Filter out previously spoken sentences and remove buildup
        new_sentences = []
        if user not in user_sentences:
            user_sentences[user] = set()
        for sentence in sentences:
            if sentence not in user_sentences[user]:
                new_sentences.append(sentence)
                user_sentences[user].add(sentence)

        # Join new sentences to form the cleaned content
        cleaned_content = '. '.join(new_sentences)

        if cleaned_content:  # Add only if there's meaningful new content
            cleaned_statements.append({
                'date': timestamp.strftime('%Y-%m-%d'),
                'time': timestamp.strftime('%H:%M:%S'),
                'user': user.strip(),
                'content': cleaned_content
            })
            # Update the last timestamp for this user
            last_user_timestamp[user] = timestamp

    return cleaned_statements