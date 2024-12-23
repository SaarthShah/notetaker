"use client"

import * as React from "react"
import { Calendar, MessageSquare, Zap, ChevronUp } from "lucide-react"
import { Sidebar, SidebarHeader, SidebarContent, SidebarFooter, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarGroup, SidebarGroupContent, useSidebar } from "@/components/ui/sidebar"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"
import LogoutButton from '@/components/logout-button'
import { redirect } from 'next/navigation'
import { createClient } from '@/app/utils/supabase-browser'
import { useContext, useEffect, useState } from 'react';
import { SidebarTitleContext } from '@/components/sidebar-context'
import { NavUser } from "@/components/nav-user"

// Menu items.
const items = [
  {
    title: "Meetings",
    icon: Calendar,
    value: "meetings"
  },
  {
    title: "Integrations",
    icon: Zap,
    value: "integrations"
  },
  {
    title: "Ask AI",
    icon: MessageSquare,
    value: "askai"
  }
]

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
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
  const { activeTab, setActiveTab } = sidebarContext;
  const { setOpen } = useSidebar();

  if (!user) {
    return null; // or a loading spinner
  }

  return (
    <Sidebar
      collapsible="icon"
      className="overflow-hidden [&>[data-sidebar=sidebar]]:flex-row"
      {...props}
    >
      <Sidebar
        collapsible="none"
        className="!w-[calc(var(--sidebar-width-icon)_+_1px)] border-r"
      >
        <SidebarHeader>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton size="lg" asChild className="md:h-8 md:p-0">
                <a href="/dashboard">
                  <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                    <span className="text-2xl font-bold">C</span>
                  </div>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-semibold">Catchflow</span>
                  </div>
                </a>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupContent className="px-1.5 md:px-0">
              <SidebarMenu>
                {items.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      tooltip={{
                        children: item.title,
                        hidden: false,
                      }}
                      onClick={() => {
                        setActiveTab(item.value);
                        setOpen(true);
                      }}
                      isActive={activeTab === item.value}
                      className="px-2.5 md:px-2"
                    >
                      <item.icon />
                      <span>{item.title}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
        <SidebarFooter>
          <NavUser user={{ ...user, avatar: user.avatar, name: user.name, email: user.email }} />
        </SidebarFooter>
      </Sidebar>
    </Sidebar>
  )
}
