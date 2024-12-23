'use client'

import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { CallDetails } from '@/components/interfaces/call-details'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { createClient } from '@/app/utils/supabase-browser';

const meetingTypeIcons = {
  gmeet: '🌐',
  google: '🌐',
  zoom: '🔵',
  teams: '👥'
}

export default function CallDetailsPage() {
  const [callDetails, setCallDetails] = useState<CallDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const supabase = createClient();
  const id = window.location.pathname.split('/').pop();

  useEffect(() => {
    const fetchCallDetails = async () => {
      if (!id) return;

      try {
        setLoading(true);
        const user = await supabase.auth.getUser();

        if (!user.data?.user) {
          throw new Error('User not authenticated');
        }

        const { data, error } = await supabase
          .from('meetings')
          .select('*')
          .eq('id', id)
          .eq('user_id', user.data.user.id)
          .single();

        if (error) {
          throw new Error('Error fetching meeting details');
        }

        setCallDetails(data as CallDetails);
      } catch (error) {
        console.error('Error fetching call details:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCallDetails();
  }, [id, supabase]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!callDetails) {
    return <div>No meeting details found or you do not have access to this meeting.</div>;
  }

  return (
    <div className='flex w-full'>
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Call Details</h1>
        
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Meeting Information</CardTitle>
            <CardDescription>
              {format(new Date(callDetails.start_time), "MMMM d, yyyy 'at' h:mm a")} - 
              {format(new Date(callDetails.end_time), "h:mm a")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p><strong>Attendees:</strong> {JSON.parse(callDetails.attendees).join(', ')}</p>
            <div className="flex items-center mt-2">
              <strong>Meeting Type:</strong> 
              <Badge variant="outline" className="ml-2">
                {meetingTypeIcons[callDetails.type]} {callDetails.type.charAt(0).toUpperCase() + callDetails.type.slice(1)}
              </Badge>
            </div>
            <p className="mt-2"><strong>Meeting Link:</strong> <a href={callDetails.meeting_link} className="text-blue-500 hover:underline">{callDetails.meeting_link}</a></p>
          </CardContent>
        </Card>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Transcript</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px] w-full rounded-md border p-4">
              {JSON.parse(callDetails.transcript).map((entry, index) => (
                <div key={index} className={`flex mb-4 ${entry.user === 'You' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`flex ${entry.user === 'You' ? 'flex-row-reverse' : 'flex-row'} items-start max-w-[70%]`}>
                    <Avatar className="w-8 h-8 mr-2">
                      <AvatarFallback>{entry.user[0]}</AvatarFallback>
                    </Avatar>
                    <div className={`rounded-lg p-3 ${entry.user === 'You' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}>
                      <p className="text-sm font-semibold mb-1">{entry.user}</p>
                      <p>{entry.content}</p>
                      <p className="text-xs mt-1 opacity-70">{entry.time}</p>
                    </div>
                  </div>
                </div>
              ))}
            </ScrollArea>
          </CardContent>
        </Card>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{JSON.parse(callDetails.summary).summary}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Action Items</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc pl-5">
              {JSON.parse(callDetails.summary).action_items.map((item, index) => (
                <li key={index} className="mb-2">{item}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
