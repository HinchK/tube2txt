'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Info } from 'lucide-react';

interface IntelligenceBriefProps {
  content: string;
}

export function IntelligenceBrief({ content }: IntelligenceBriefProps) {
  // Custom renderer for text to find timestamps [HH:MM:SS] or [MM:SS]
  const renderText = (text: string) => {
    const timestampRegex = /\[(\d{1,2}:)?(\d{1,2}:\d{2})\]/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = timestampRegex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }

      const timestamp = match[0];
      const timeStr = timestamp.slice(1, -1);
      const timeParts = timeStr.split(':').map(Number);
      let seconds = 0;
      if (timeParts.length === 3) {
        seconds = timeParts[0] * 3600 + timeParts[1] * 60 + timeParts[2];
      } else if (timeParts.length === 2) {
        seconds = timeParts[0] * 60 + timeParts[1];
      }

      parts.push(
        <a
          key={match.index}
          href={`#t-${seconds}`}
          className="text-primary hover:text-white underline decoration-dotted transition-colors cursor-pointer"
          onClick={(e) => {
            // Hash change will be handled by DataStream component
          }}
        >
          {timestamp}
        </a>
      );

      lastIndex = timestampRegex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts;
  };

  return (
    <div className="glass-card p-8 border-primary/20 relative group overflow-hidden">
      <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-30 transition-opacity">
        <Info size={120} className="text-primary" />
      </div>
      
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center border border-primary/30">
          <Info className="text-primary" size={20} />
        </div>
        <h2 className="text-2xl font-orbitron text-primary uppercase tracking-tighter">Intelligence Brief</h2>
      </div>

      <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-p:text-textMuted prose-headings:font-orbitron prose-headings:text-white prose-a:text-primary">
        <ReactMarkdown
          components={{
            p: ({ children }) => {
              if (typeof children === 'string') {
                return <p>{renderText(children)}</p>;
              }
              // If children is an array, we need to process each part
              const processed = React.Children.map(children, child => {
                if (typeof child === 'string') return renderText(child);
                return child;
              });
              return <p>{processed}</p>;
            },
            li: ({ children }) => {
              const processed = React.Children.map(children, child => {
                if (typeof child === 'string') return renderText(child);
                return child;
              });
              return <li>{processed}</li>;
            }
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}
