'use client';

import { Calendar, Home, Inbox, Search, Settings, User2, ChevronUp, MessageSquare, Zap } from "lucide-react"
import { Sidebar, SidebarHeader, SidebarContent, SidebarFooter, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarGroup, SidebarGroupLabel, SidebarGroupContent } from "@/components/ui/sidebar"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"
import LogoutButton from '@/components/logout-button'
import { redirect } from 'next/navigation'
import { createClient } from '@/app/utils/supabase-browser'
import { useContext, useEffect, useState } from 'react';
import { SidebarTitleContext } from '@/components/sidebar-context';

// Menu items.
const items = [
  {
    title: "Meetings",
    icon: Calendar,
    value:"meetings"
  },
  {
    title: "Integrations",
    icon: Zap,
    value:"integrations"
  },
  {
    title: "Ask AI",
    icon: MessageSquare,
    value:"askai"
  }
]

export function AppSidebar() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const fetchUser = async () => {
      const supabase = await createClient();
      const { data, error } = await supabase.auth.getUser();
      if (error || !data?.user) {
        redirect('/auth/login');
      } else {
        setUser(data.user);
      }
    };

    fetchUser();
  }, []);

  const sidebarContext = useContext(SidebarTitleContext);
  if (!sidebarContext) {
    throw new Error("SidebarContext is not available");
  }
  const { setActiveTab } = sidebarContext;

  if (!user) {
    return null; // or a loading spinner
  }

  return (
    <Sidebar>
      <SidebarHeader>
        <div className="text-center font-bold text-lg">Catchflow</div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <div onClick={() => { setActiveTab(item.value); }}>
                      <item.icon />
                      <span>{item.title}</span>
                    </div>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton>
                  <User2 /> {user.email}
                  <ChevronUp className="ml-auto" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                side="top"
                className="w-[--radix-popper-anchor-width]"
              >
                <DropdownMenuItem>
                  <span>Account</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <span>Billing</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <LogoutButton />
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  )
}
