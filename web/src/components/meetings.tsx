"use client";
import { useState, useEffect, useContext } from "react";
import {
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Pagination,
  Button,
  Badge,
} from "@nextui-org/react";
import { ChevronRight } from "lucide-react";
import { SidebarTitleContext } from "@/components/sidebar-context";
import { createClient } from "@/app/utils/supabase-browser";

type Meeting = {
  id: number;
  created_at: string;
  user_id: string;
  transcript: Record<string, any>;
  start_time: string;
  end_time: string;
  attendees: Record<string, any>;
  summary: Record<string, any>;
  meeting_link: string;
  type: string;
};

const ITEMS_PER_PAGE = 10;

export function Meetings() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const sidebarContext = useContext(SidebarTitleContext);

  const fetchMeetings = async () => {
    try {
      const cachedMeetings = localStorage.getItem("meetings");
      if (cachedMeetings) {
        setMeetings(JSON.parse(cachedMeetings));
        setLoading(false);
        return;
      }

      const supabase = await createClient();
      const { data, error } = await supabase.from("meetings").select("*");

      if (error) {
        throw new Error("Error fetching meetings from Supabase");
      }

      setMeetings(data as Meeting[]);
      localStorage.setItem("meetings", JSON.stringify(data));
    } catch (error) {
      console.error("Error fetching meetings:", error);
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

  const paginatedData = meetings.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  return (
    <div>
      {activeTab === "meetings" && (
        <div>
          <button
            onClick={fetchMeetings}
            className="mb-4 px-4 py-2 bg-green-500 text-white rounded"
          >
            Refresh
          </button>
          <Table
            bgcolor="white"
            className="w-full h-full [&>*:nth-child(1)]:h-full [&>*:nth-child(1)]:shadow-none"
            aria-label="Meetings table"
            radius="none"
            isCompact
            bottomContent={
              meetings && (
                <div className="flex justify-end place-self-end">
                  <Pagination
                    isCompact
                    total={Math.ceil(meetings.length / ITEMS_PER_PAGE)}
                    page={currentPage}
                    onChange={setCurrentPage}
                  />
                </div>
              )
            }
          >
            <TableHeader className="h-10">
              <TableColumn className="w-32 text-left">Date</TableColumn>
              <TableColumn className="w-32 text-left">Time</TableColumn>
              <TableColumn className="w-32 text-left">Attendees</TableColumn>
              <TableColumn className="w-48 text-left">Summary</TableColumn>
              <TableColumn className="w-48 text-left">Meeting Link</TableColumn>
              <TableColumn className="w-32 text-left">Type</TableColumn>
              <TableColumn className="w-16 text-left">Details</TableColumn>
            </TableHeader>
            <TableBody
              isLoading={!meetings}
              loadingContent={<div>Loading...</div>}
              className=""
            >
              {paginatedData.map((meeting) => (
                <TableRow
                  key={meeting.id}
                  className="cursor-pointer hover:bg-muted"
                  onClick={() => {
                    window.location.href = meeting.meeting_link;
                  }}
                >
                  <TableCell>
                    {new Date(meeting.created_at).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })}
                  </TableCell>
                  <TableCell>
                    {new Date(meeting.created_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </TableCell>
                  <TableCell>
                    {Object.keys(meeting.attendees).length} attendees
                  </TableCell>
                  <TableCell>{meeting.summary.summary}</TableCell>
                  <TableCell>
                    <a
                      href={meeting.meeting_link}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Link
                    </a>
                  </TableCell>
                  <TableCell>{meeting.type}</TableCell>
                  <TableCell>
                    <Button isIconOnly variant="light">
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
