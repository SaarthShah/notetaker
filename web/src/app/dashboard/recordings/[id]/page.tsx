'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { format } from 'date-fns'
import { CallDetails } from '@/components/interfaces/call-details'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { createClient } from '@/app/utils/supabase-browser';
import { FaGoogle, FaMicrosoft, FaVideo } from "react-icons/fa";
import { Skeleton } from "@/components/ui/skeleton";

const getMeetingTypeWithIcon = (type: string) => {
  switch (type) {
    case "gmeet":
      return (
        <span className="flex items-center">
          <FaGoogle className="mr-2 align-middle" /> <span className="align-middle">Google Meet</span>
        </span>
      );
    case "zoom":
      return (
        <span className="flex items-center">
          <FaVideo className="mr-2 align-middle" /> <span className="align-middle">Zoom</span>
        </span>
      );
    case "teams":
      return (
        <span className="flex items-center">
          <FaMicrosoft className="mr-2 align-middle" /> <span className="align-middle">Microsoft Teams</span>
        </span>
      );
    default:
      return type;
  }
};

const generateColorForSpeaker = (speaker: string) => {
  const colors = ['bg-red-200', 'bg-green-200', 'bg-blue-200', 'bg-yellow-200', 'bg-purple-200'];
  let hash = 0;
  for (let i = 0; i < speaker.length; i++) {
    hash = speaker.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
};

export default function CallDetailsPage() {
  const [callDetails, setCallDetails] = useState<CallDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const supabase = createClient();
  const id = window.location.pathname.split('/').pop();
  const router = useRouter();

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
        if (error instanceof Error) {
          console.error('Error fetching call details:', error.message);
          console.error('Stack trace:', error.stack);
        } else {
          console.error('Error fetching call details:', error);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchCallDetails();

  }, [id, supabase, router]);

  if (loading) {
    return (
      <div className='flex w-full'>
        <div className="container mx-auto p-4">
          <Skeleton className="h-full w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className='flex w-full'>
      <div className="container mx-auto p-4">
        {callDetails ? (
          <>
            <button onClick={() => router.back()} className="mb-4 text-blue-500 hover:underline">Back</button>
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
                    {getMeetingTypeWithIcon(callDetails.type)}
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
                  {callDetails.transcript ? (
                    callDetails.type === 'zoom' ? (
                      JSON.parse(callDetails.transcript).results?.channels[0]?.alternatives[0]?.paragraphs?.length > 0 ? (
                        JSON.parse(callDetails.transcript).results.channels[0].alternatives[0].paragraphs.map((paragraph: any, index: number) => (
                          <div key={index} className="mb-4">
                            {paragraph.sentences.map((sentence: any, idx: number) => (
                              <div key={idx} className="flex items-start mb-2">
                                <Avatar className="w-8 h-8 mr-2">
                                  <AvatarFallback>{`S${paragraph.speaker}`}</AvatarFallback>
                                </Avatar>
                                <div className={`${generateColorForSpeaker(`Speaker ${paragraph.speaker}`)} rounded-lg p-3`}>
                                  <p>{sentence.text}</p>
                                  <p className="text-xs mt-1 opacity-70">
                                    {`${new Date(new Date(callDetails.start_time).getTime() + sentence.start * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}`}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        ))
                      ) : (
                        <p className="text-center text-gray-500">No transcript available.</p>
                      )
                    ) : (
                      JSON.parse(callDetails.transcript).map((entry: any, index: number) => (
                        <div key={index} className={`flex mb-4 ${entry.user === 'You' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`flex ${entry.user === 'You' ? 'flex-row-reverse' : 'flex-row'} items-start max-w-[70%]`}>
                            <Avatar className="w-8 h-8 mr-2">
                              <AvatarFallback>{entry.user[0]}</AvatarFallback>
                            </Avatar>
                            <div className={`rounded-lg p-3 ${entry.user === 'You' ? 'bg-blue-500 text-white' : generateColorForSpeaker(entry.user)}`}>
                              <p className="text-sm font-semibold mb-1">{entry.user}</p>
                              <p>{entry.content}</p>
                              <p className="text-xs mt-1 opacity-70">{entry.time}</p>
                            </div>
                          </div>
                        </div>
                      ))
                    )
                  ) : (
                    <p className="text-center text-gray-500">No transcript available.</p>
                  )}
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
                  {JSON.parse(callDetails.summary).action_items.map((item: any, index: number) => (
                    <li key={index} className="mb-2">{item}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </>
        ) : (
          <div></div>
        )}
      </div>
    </div>
  )
}
