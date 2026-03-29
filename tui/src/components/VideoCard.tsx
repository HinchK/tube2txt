import React from "react";

interface Props {
  slug: string;
  title: string;
  thumbnail_path?: string;
  processedAt: string;
  selected: boolean;
  onSelect: () => void;
}

export function VideoCard({ slug, title, thumbnail_path, processedAt, selected, onSelect }: Props) {
  return (
    <div
      className={`border-2 cursor-pointer transition-all duration-200 group overflow-hidden ${
        selected 
          ? "border-cyan-500 bg-cyan-900/10 shadow-[0_0_15px_rgba(6,182,212,0.1)]" 
          : "border-zinc-800 hover:border-zinc-600 bg-zinc-900/20"
      }`}
      onClick={onSelect}
      style={{ borderStyle: 'double' }}
    >
      <div className="w-full h-32 bg-zinc-900 border-b border-zinc-800 flex items-center justify-center overflow-hidden relative">
        {thumbnail_path ? (
          <img 
            src={thumbnail_path} 
            className="w-full h-full object-cover" 
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
              (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
              (e.target as HTMLImageElement).nextElementSibling?.classList.add('flex');
            }}
          />
        ) : <div className="w-full h-full" />}
        <div className={`${thumbnail_path ? 'hidden' : 'flex'} items-center justify-center w-full h-full text-[10px] text-zinc-700 font-black uppercase tracking-[0.3em] bg-zinc-900`}>No Image</div>
        <div className="absolute bottom-0 left-0 right-0 h-1/2 bg-gradient-to-t from-zinc-950/80 to-transparent"></div>
      </div>
      <div className="flex flex-col gap-1 p-4 relative">
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
