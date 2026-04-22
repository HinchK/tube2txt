'use client';

import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, Database } from 'lucide-react';
import { TimestampLink } from './TimestampLink';

interface DataStreamProps {
  videoId: string;
  segments: any[];
  baseUrl?: string;
}

export function DataStream({ videoId, segments, baseUrl }: DataStreamProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Listen for hash changes to auto-expand
  useEffect(() => {
    const handleHashChange = () => {
      if (window.location.hash.startsWith('#t-')) {
        setIsOpen(true);
        // Small delay to ensure the DOM is updated before scrolling
        setTimeout(() => {
          const id = window.location.hash.substring(1);
          const element = document.getElementById(id);
          if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            element.classList.add('highlight-pulse');
            setTimeout(() => element.classList.remove('highlight-pulse'), 2000);
          }
        }, 100);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    // Check initial hash
    if (window.location.hash.startsWith('#t-')) {
      handleHashChange();
    }
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  return (
    <div className="glass-card border-accent/20 overflow-hidden transition-all duration-500">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-6 flex items-center justify-between group hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <Database className={`text-accent transition-transform duration-500 ${isOpen ? 'rotate-180' : ''}`} size={24} />
          <h2 className="text-xl font-orbitron text-accent uppercase tracking-widest">Data Stream</h2>
        </div>
        <div className="flex items-center gap-2 font-sharetech text-textMuted text-sm uppercase">
          {isOpen ? 'Close Stream' : 'Expand Stream'}
          {isOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </div>
      </button>

      <div className={`transition-all duration-500 ease-in-out ${isOpen ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'} overflow-y-auto`}>
        <div className="p-8 pt-0 space-y-4">
          <div className="h-px bg-white/10 mb-6" />
          <div className="grid gap-4">
            {segments.map((seg, i) => (
              <div 
                key={i} 
                id={`t-${seg.seconds}`}
                className="flex gap-4 items-start p-2 rounded hover:bg-white/5 transition-colors scroll-mt-24"
              >
                <TimestampLink videoId={videoId} seconds={seg.seconds} text={seg.text} baseUrl={baseUrl} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
