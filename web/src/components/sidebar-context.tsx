'use client'

import React, { createContext, useState, ReactNode } from 'react';

interface SidebarContextType {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const SidebarTitleContext = createContext<SidebarContextType | undefined>(undefined);

export const SidebarContextProvider = ({ children }: { children: ReactNode }) => {
  const [activeTab, setActiveTab] = useState("meetings");

  return (
    <SidebarTitleContext.Provider value={{ activeTab, setActiveTab }}>
      {children}
    </SidebarTitleContext.Provider>
  );
};