import React, { useState, useEffect, useContext } from 'react';
import { SidebarTitleContext } from '@/components/sidebar-context';
import { createClient } from '@/app/utils/supabase-browser';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type Meeting = {
  id: number;
  created_at: string;
  user_id: string;
  transcript: Record<string, any>;
  start_time: string;
  end_time: string;
  attendees: Record<string, any>;
  summary: string; // Changed to string to match ReactNode requirements
  meeting_link: string;
  type: string;
};

export function Meetings() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [meetingsPerPage] = useState(10);
  const sidebarContext = useContext(SidebarTitleContext);

  const fetchMeetings = async () => {
    try {
      const cachedMeetings = localStorage.getItem('meetings');
      if (cachedMeetings) {
        setMeetings(JSON.parse(cachedMeetings));
        setLoading(false);
        return;
      }

      const supabase = await createClient();
      const { data, error } = await supabase
        .from('meetings')
        .select('*');

      if (error) {
        throw new Error('Error fetching meetings from Supabase');
      }

      setMeetings(data as Meeting[]);
      localStorage.setItem('meetings', JSON.stringify(data));
    } catch (error) {
      console.error('Error fetching meetings:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMeetings();
  }, []);

  if (!sidebarContext) {
    throw new Error("SidebarContext is not available");
  }

  const { activeTab } = sidebarContext;

  if (loading) {
    return <div>Loading...</div>;
  }

  // Pagination logic
  const indexOfLastMeeting = currentPage * meetingsPerPage;
  const indexOfFirstMeeting = indexOfLastMeeting - meetingsPerPage;
  const currentMeetings = meetings.slice(indexOfFirstMeeting, indexOfLastMeeting);

  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

  return (
    <div>
      {activeTab === 'meetings' && (
        <div>
          <button 
            onClick={fetchMeetings} 
            className="mb-4 px-4 py-2 bg-green-500 text-white rounded"
          >
            Refresh
          </button>
          <Table>
            <TableCaption>A list of your recent meetings.</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">Type</TableHead>
                <TableHead>Summary</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {currentMeetings.map((meeting) => (
                <TableRow key={meeting.id}>
                  <TableCell className="font-medium">{meeting.type}</TableCell>
                  <TableCell>{meeting.summary}</TableCell>
                  <TableCell className="text-right">{new Date(meeting.start_time).toLocaleDateString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <div className="flex justify-center mt-4">
            {Array.from({ length: Math.ceil(meetings.length / meetingsPerPage) }, (_, index) => (
              <button
                key={index + 1}
                onClick={() => paginate(index + 1)}
                className={`px-3 py-1 mx-1 ${currentPage === index + 1 ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
              >
                {index + 1}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
