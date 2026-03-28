import React from "react";

interface Props {
  slug: string;
  startTs: string;
  text: string;
  query: string;
  selected: boolean;
  onSelect: () => void;
}

export function SearchResult({ slug, startTs, text, query, selected, onSelect }: Props) {
  // Highlight query in text if possible
  const parts = text.split(new RegExp(`(${query})`, 'gi'));

  return (
    <div
      className={`p-3 border cursor-pointer transition-colors ${
        selected 
          ? "bg-cyan-900/20 border-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.1)]" 
          : "bg-zinc-900/50 border-zinc-800 hover:border-zinc-700"
      }`}
      onClick={onSelect}
    >
      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-widest border-b border-zinc-800/50 pb-1 mb-1">
          <span className={selected ? "text-cyan-400 font-bold" : "text-zinc-500"}>{slug}</span>
          <span className="text-zinc-600">OFFSET: {startTs}</span>
        </div>
        <div className={`text-sm ${selected ? "text-zinc-100" : "text-zinc-400"}`}>
          {parts.map((part, i) => (
            part.toLowerCase() === query.toLowerCase() 
              ? <span key={i} className="bg-cyan-500/30 text-cyan-200 px-0.5 rounded-sm font-bold">{part}</span> 
              : <span key={i}>{part}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
