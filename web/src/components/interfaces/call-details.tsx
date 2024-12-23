export interface Transcript {
  date: string;
  time: string;
  user: string;
  content: string;
}

export interface CallDetails {
  id: number;
  user_id: string;
  created_at: string;
  start_time: string;
  end_time: string;
  attendees: string[];
  meeting_link: string;
  type: string;
  transcript: Transcript[];
  summary: string;
  action_items: string[];
}
