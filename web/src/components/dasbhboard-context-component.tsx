'use client';

import { User } from './interfaces/user';
import { useEffect, useState, useContext } from 'react';
import { createClient } from '@/app/utils/supabase-browser';
import { SidebarTitleContext } from '@/components/sidebar-context';
import { Meetings } from './meetings';

export default function DashboardContextComponent() {
  const [user, setUser] = useState<User | null>(null);
  const supabase = createClient();

  useEffect(() => {
    const fetchUserData = async () => {
      const { data, error } = await supabase.auth.getUser();
      if (!error && data?.user) {
        setUser(data.user as User);
      }
    };

    fetchUserData();
  }, [supabase]);

  const sidebarContext = useContext(SidebarTitleContext);
  if (!sidebarContext) {
    throw new Error("SidebarContext is not available");
  }
  const activeTab = sidebarContext.activeTab; // Read the title from the context

  const renderContent = () => {
    switch (activeTab) {
      case 'meetings':
        return <Meetings/>;
      case 'askai':
        return <p>Ask AI Content</p>;
      case 'integrations':
        return <p>Integrations Content</p>;
      default:
        return <p>Welcome to the Dashboard</p>;
    }
  };

  return (
    <div className='py-5'>
      {renderContent()}
    </div>
  );
}