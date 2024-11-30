import React, { useState, useEffect, useRef } from 'react';
import { createClient } from '@/app/utils/supabase-browser';
import { User } from './interfaces/user';
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FaGoogle, FaApple, FaMicrosoft, FaRegCalendarAlt } from 'react-icons/fa';

interface CalendarIntegrationProps {
  userInfo: User | null;
}

export function CalendarIntegration({ userInfo }: CalendarIntegrationProps) {
  const [isConnected, setIsConnected] = useState(false);
  const cachedDataRef = useRef<any>(null);
  const supabase = createClient();

  useEffect(() => {
    const checkGoogleIntegration = async () => {
      if (userInfo) {
        if (cachedDataRef.current) {
          setIsConnected(cachedDataRef.current.google_token && cachedDataRef.current.google_token.refresh_token);
        } else {
          const { data, error } = await supabase
            .from('integrations')
            .select('google_token')
            .eq('user_id', userInfo.id)
            .single();

          if (error) {
            console.error('Error fetching integration data:', error);
          } else if (data) {
            cachedDataRef.current = data;
            setIsConnected(data.google_token && data.google_token.refresh_token);
          }
        }
      }
    };

    checkGoogleIntegration();
  }, [userInfo, supabase]);

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
    <div className="flex flex-col items-center min-h-screen h-full px-6">
      <div className="w-full max-w-6xl mx-auto">
        <div className="text-left mb-8">
          <h1 className="text-2xl font-bold">Integrate Your Calendar</h1>
          <p className="text-gray-600">Connect your calendar to manage events seamlessly.</p>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <Card className="flex items-center space-x-4 rounded-md border p-4 bg-white shadow-sm">
            <FaGoogle size={24} />
            <div className="flex-1 space-y-1">
              <p className="text-sm font-medium leading-none">
                Google Calendar
              </p>
              <p className="text-sm text-muted-foreground">
                {isConnected ? 'Connected to Google Calendar' : 'Not connected'}
              </p>
            </div>
            <Button
              onClick={handleGoogleCalendarConnect}
              disabled={isConnected}
              className={isConnected ? 'bg-green-500' : 'bg-blue-500'}
            >
              {isConnected ? 'Connected' : 'Connect'}
            </Button>
          </Card>
          <Card className="flex items-center space-x-4 rounded-md border p-4 bg-white shadow-sm">
            <FaMicrosoft size={24} />
            <div className="flex-1 space-y-1">
              <p className="text-sm font-medium leading-none">
                Outlook Calendar
              </p>
              <p className="text-sm text-muted-foreground">
                Integration available soon.
              </p>
            </div>
            <Button disabled className="bg-gray-300 text-gray-700">
              Coming Soon
            </Button>
          </Card>
          <Card className="flex items-center space-x-4 rounded-md border p-4 bg-white shadow-sm">
            <FaApple size={24} />
            <div className="flex-1 space-y-1">
              <p className="text-sm font-medium leading-none">
                Apple Calendar
              </p>
              <p className="text-sm text-muted-foreground">
                Integration available soon.
              </p>
            </div>
            <Button disabled className="bg-gray-300 text-gray-700">
              Coming Soon
            </Button>
          </Card>
          <Card className="flex items-center space-x-4 rounded-md border p-4 bg-white shadow-sm">
            <FaRegCalendarAlt size={24} />
            <div className="flex-1 space-y-1">
              <p className="text-sm font-medium leading-none">
                Notion Calendar
              </p>
              <p className="text-sm text-muted-foreground">
                Integration available soon.
              </p>
            </div>
            <Button disabled className="bg-gray-300 text-gray-700">
              Coming Soon
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
}