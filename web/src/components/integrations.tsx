import React, { useState } from 'react';
import { createClient } from '@/app/utils/supabase-browser';
import { User } from './interfaces/user';

interface CalendarIntegrationProps {
  userInfo: User | null;
}

export function CalendarIntegration({ userInfo }: CalendarIntegrationProps) {
  const [isConnected, setIsConnected] = useState(false);
  const supabase = createClient();

  const handleGoogleCalendarConnect = () => {
    const YOUR_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    const YOUR_REDIRECT_URI = 'http://localhost:3000/api/oauth2callback';

    const oauth2SignIn = () => {
      const oauth2Endpoint = 'https://accounts.google.com/o/oauth2/v2/auth';

      const params: Record<string, string> = {
        'client_id': YOUR_CLIENT_ID || '',
        'redirect_uri': YOUR_REDIRECT_URI,
        'scope': 'https://www.googleapis.com/auth/calendar.events.readonly',
        'include_granted_scopes': 'true',
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent'
      };

      const urlParams = new URLSearchParams(params).toString();
      const oauth2Url = `${oauth2Endpoint}?${urlParams}`;

      window.open(oauth2Url, '_blank'); // Open OAuth provider in a new tab
    };

    oauth2SignIn();
  };

  return (
    <div className="calendar-integration">
      <h2>Integrate Your Calendar</h2>
      <div className="integration-options">
        <button 
          onClick={handleGoogleCalendarConnect} 
          className={`mb-4 px-4 py-2 ${isConnected ? 'bg-green-500' : 'bg-blue-500'} text-white rounded`}
        >
          {isConnected ? 'Connected to Google Calendar' : 'Connect with Google Calendar'}
        </button>
        <button 
          disabled 
          className="mb-4 px-4 py-2 bg-gray-300 text-gray-700 rounded"
        >
          Outlook Calendar (Coming Soon)
        </button>
        <button 
          disabled 
          className="mb-4 px-4 py-2 bg-gray-300 text-gray-700 rounded"
        >
          Apple Calendar (Coming Soon)
        </button>
      </div>
    </div>
  );
}