import React from "react";

interface Props {
  slug: string;
  title: string;
  processedAt: string;
  selected: boolean;
  onSelect: () => void;
}

export function VideoCard({ slug, title, processedAt, selected, onSelect }: Props) {
  return (
    <div
      className={`border-2 p-4 cursor-pointer transition-all duration-200 group ${
        selected 
          ? "border-cyan-500 bg-cyan-900/10 shadow-[0_0_15px_rgba(6,182,212,0.1)]" 
          : "border-zinc-800 hover:border-zinc-600 bg-zinc-900/20"
      }`}
      onClick={onSelect}
      style={{ borderStyle: 'double' }}
    >
      <div className="flex flex-col gap-1">
        <div className={`font-bold transition-colors ${selected ? "text-cyan-400" : "text-zinc-200 group-hover:text-cyan-300"}`}>
          {title}
        </div>
        <div className="text-[10px] text-zinc-500 font-mono uppercase tracking-widest flex items-center gap-2">
          <span className="text-zinc-700 font-black">SLUG:</span> {slug}
        </div>
        <div className="text-[10px] text-zinc-600 font-mono flex items-center gap-2">
          <span className="text-zinc-700 font-black tracking-widest uppercase">DATE:</span> {new Date(processedAt).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
}
