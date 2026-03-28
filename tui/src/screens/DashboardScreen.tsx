import React, { useState } from "react";
import { useVideos } from "../hooks/useVideos";
import { VideoCard } from "../components/VideoCard";

interface Props {
  onSelectVideo: (slug: string) => void;
}

export function DashboardScreen({ onSelectVideo }: Props) {
  const { videos, loading, error } = useVideos();
  const [selectedIdx, setSelectedIdx] = useState(0);

  if (loading) return <div className="p-8 text-zinc-500 animate-pulse">Loading library...</div>;
  if (error) return <div className="p-8 text-red-500 border border-red-900 bg-red-900/10 m-4">{error}</div>;
  
  if (videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center flex-grow p-12 text-zinc-600 border-2 border-dashed border-zinc-800 m-4">
        <span className="text-xl mb-2 font-bold opacity-50">NO VIDEOS PROCESSED</span>
        <span className="text-sm">Click [1] Process to begin your first job.</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-grow p-4 gap-4 overflow-y-auto">
      <div className="text-[10px] uppercase font-black tracking-widest text-zinc-600 mb-2">
        {videos.length} video{videos.length !== 1 ? "s" : ""} in database
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {videos.map((v, i) => (
          <VideoCard
            key={v.slug}
            slug={v.slug}
            title={v.title}
            processedAt={v.processed_at}
            selected={i === selectedIdx}
            onSelect={() => onSelectVideo(v.slug)}
          />
        ))}
      </div>
      <div className="mt-auto pt-4 border-t border-zinc-900 text-[10px] text-zinc-700 uppercase tracking-tighter">
        Click a card to view transcripts and AI content
      </div>
    </div>
  );
}
