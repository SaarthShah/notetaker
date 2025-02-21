"use client";
import useSWR from 'swr';
import { useState, useContext } from "react";
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
  Spinner,
} from "@nextui-org/react";
import { ChevronRight, RefreshCw } from "lucide-react";
import { SidebarTitleContext } from "@/components/sidebar-context";
import { createClient } from "@/app/utils/supabase-browser";
import { FaGoogle, FaMicrosoft, FaVideo } from "react-icons/fa";
import { useRouter } from "next/navigation";

const ITEMS_PER_PAGE = 10;

const fetcher = async () => {
  const supabase = await createClient();
  const user = await supabase.auth.getUser();

  if (!user.data?.user) {
    throw new Error("User not authenticated");
  }

  const { data, error } = await supabase
    .from("meetings")
    .select("*")
    .eq("user_id", user.data.user.id);

  if (error) {
    throw new Error("Error fetching meetings from Supabase");
  }

  return data;
};

export function Meetings() {
  const { data: meetings, error } = useSWR('meetings', fetcher);
  const [currentPage, setCurrentPage] = useState(1);
  const sidebarContext = useContext(SidebarTitleContext);
  const router = useRouter();

  if (!sidebarContext) {
    throw new Error("SidebarContext is not available");
  }

  const { activeTab } = sidebarContext;

  if (error) return <div>Error loading meetings</div>;
  if (!meetings) return (
    <div className="flex justify-center items-center h-full">
      <Spinner size="lg" />
    </div>
  );

  // Sort meetings by start_time in descending order
  const sortedMeetings = [...meetings].sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime());

  const paginatedData = sortedMeetings.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

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

  return (
    <div className="w-full">
      {activeTab === "meetings" && (
        <div className="w-full">
          <div className="flex justify-between items-center mb-8">
            <div className="text-left">
              <h1 className="text-2xl font-bold">Meetings</h1>
              <p className="text-gray-600">We've got your meeting notes covered with Catchflow.</p>
            </div>
            <Button
              isIconOnly
              variant="light"
              onClick={() => useSWR.mutate('meetings')}
            >
              <RefreshCw className="w-5 h-5" />
            </Button>
          </div>
          <Table
            bgcolor="white"
            className="w-full h-full [&>*:nth-child(1)]:h-full [&>*:nth-child(1)]:shadow-none"
            aria-label="Meetings table"
            radius="none"
            fullWidth={true}
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
              <TableColumn className="w-[12rem] text-left">Date</TableColumn>
              <TableColumn className="w-[12rem] text-left">Time</TableColumn>
              <TableColumn className="w-[12rem] text-left">Attendees</TableColumn>
              <TableColumn className="w-[24rem] text-left">Summary</TableColumn>
              <TableColumn className="w-[24rem] text-left">Meeting Link</TableColumn>
              <TableColumn className="w-[12rem] text-left">Type</TableColumn>
              <TableColumn className="w-[12rem] text-left">Duration</TableColumn>
              <TableColumn className="w-[8rem] text-left">Details</TableColumn>
            </TableHeader>
            <TableBody
              isLoading={!meetings} // Use loading state to show loading content
              loadingContent={<div>Loading...</div>}
              className=""
            >
              {paginatedData.map((meeting) => {
                const startTime = new Date(meeting.start_time);
                const endTime = new Date(meeting.end_time);
                const duration = Math.round((endTime.getTime() - startTime.getTime()) / 60000);
                return (
                  <TableRow
                    key={meeting.id}
                    className="cursor-pointer hover:bg-muted"
                    onClick={() => router.push(`/dashboard/recordings/${meeting.id}`)}
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
                      {JSON.parse(meeting.attendees).length} attendees
                    </TableCell>
                    <TableCell>{JSON.parse(meeting.summary).summary.slice(0, 50)}...</TableCell>
                    <TableCell>{meeting.meeting_link}</TableCell>
                    <TableCell>{getMeetingTypeWithIcon(meeting.type)}</TableCell>
                    <TableCell>{duration} mins</TableCell>
                    <TableCell>
                      <Button isIconOnly variant="light">
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
