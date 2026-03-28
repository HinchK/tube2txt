import React, { useState, useEffect } from "react";
import { useVideos } from "../hooks/useVideos";

interface Props {
  slug: string;
  onBack: () => void;
}

export function VideoDetailScreen({ slug, onBack }: Props) {
  const { selectedVideo, loading, error, fetchDetail } = useVideos();
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    fetchDetail(slug);
  }, [slug, fetchDetail]);

  if (loading) return <div className="p-8 text-zinc-500 animate-pulse">Fetching intelligence for {slug}...</div>;
  if (error) return <div className="p-8 text-red-500 border border-red-900 bg-red-900/10 m-4">{error}</div>;
  if (!selectedVideo) return <div className="p-8 text-zinc-600 italic">Video not found in repository.</div>;

  const tabs = [
    { name: "TRANSCRIPT", content: null as string | null },
    ...selectedVideo.ai_files.map((f) => ({ name: f.name.toUpperCase(), content: f.content })),
  ];

  return (
    <div className="flex flex-col flex-grow h-full bg-zinc-950 text-zinc-300 font-mono">
      {/* Header */}
      <div className="p-4 border-b border-zinc-800 bg-zinc-900/30 flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-zinc-100 uppercase tracking-tight">{selectedVideo.title}</h2>
          <button 
            onClick={onBack}
            className="text-[10px] border border-zinc-700 px-2 py-1 hover:bg-zinc-800 transition-colors uppercase tracking-widest text-zinc-500"
          >
            [ESC] BACK TO LIBRARY
          </button>
        </div>
        <div className="flex items-center gap-4 text-[10px] text-zinc-500 overflow-hidden whitespace-nowrap">
          <span className="flex items-center gap-1"><span className="text-zinc-700 font-black">ID:</span> {selectedVideo.slug}</span>
          <span className="flex items-center gap-1"><span className="text-zinc-700 font-black">SRC:</span> {selectedVideo.url}</span>
          <span className="flex items-center gap-1 ml-auto"><span className="text-zinc-700 font-black">DATE:</span> {new Date(selectedVideo.processed_at).toLocaleString()}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex bg-zinc-900/50 border-b border-zinc-800">
        {tabs.map((tab, i) => (
          <button
            key={tab.name}
            onClick={() => setActiveTab(i)}
            className={`px-6 py-2 text-[10px] font-black tracking-[0.2em] transition-all border-r border-zinc-800 ${
              i === activeTab 
                ? "bg-zinc-950 text-cyan-400 border-b-2 border-b-cyan-500" 
                : "text-zinc-600 hover:bg-zinc-800 hover:text-zinc-400"
            }`}
          >
            {tab.name}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-grow overflow-y-auto p-6 bg-zinc-950/50 leading-relaxed">
        {activeTab === 0
          ? (
            <div className="flex flex-col gap-4 max-w-4xl mx-auto">
              {selectedVideo.segments.map((seg, i) => (
                <div key={i} className="flex gap-6 group hover:bg-zinc-900/30 p-2 -m-2 rounded transition-colors">
                  <a 
                    href={`${selectedVideo.url}&t=${seg.seconds}`}
                    target="_blank"
                    className="text-cyan-600 font-bold shrink-0 tabular-nums hover:text-cyan-400 transition-colors"
                  >
                    [{seg.start_ts}]
                  </a>
                  <div className="text-zinc-400 group-hover:text-zinc-200">{seg.text}</div>
                </div>
              ))}
            </div>
          )
          : (
            <div className="max-w-4xl mx-auto prose prose-invert prose-cyan">
              <div className="whitespace-pre-wrap text-zinc-300 font-sans tracking-wide">
                {tabs[activeTab]?.content}
              </div>
            </div>
          )
        }
      </div>

      <div className="p-2 px-4 border-t border-zinc-900 bg-zinc-900/20 text-[9px] text-zinc-700 uppercase tracking-widest flex gap-4">
        <span>MODE: READ-ONLY</span>
        <span>ENCRYPTION: NONE</span>
        <span className="ml-auto opacity-50">TUBE2TXT V3.1.0 // GRIDLAND ENGINE</span>
      </div>
    </div>
  );
}
