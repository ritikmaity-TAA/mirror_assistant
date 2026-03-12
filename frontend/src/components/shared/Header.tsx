'use client';

import React from 'react';
import { useAppContext } from '@/context/app-context';

export const Header: React.FC = () => {
  const { professionalName, professionalRole } = useAppContext();

  return (
    <header className="h-16 bg-white border-b border-gray-100 flex items-center justify-between px-8 sticky top-0 z-10">
      <div className="flex items-center space-x-2">
        <h1 className="text-xl font-bold text-gray-900 tracking-tight italic">Inbox</h1>
        <div className="w-1.5 h-1.5 bg-green-500 rounded-full mt-1 animate-pulse"></div>
      </div>
      <div className="flex items-center space-x-4">
        <button className="text-gray-500 hover:text-gray-700 relative">
          <span>🔔</span>
          <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
        </button>
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <p className="text-sm font-medium text-gray-800">{professionalName}</p>
            <p className="text-xs text-gray-500">{professionalRole}</p>
          </div>
          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center overflow-hidden">
             <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${professionalName}`} alt="Profile" />
          </div>
        </div>
      </div>
    </header>
  );
};
