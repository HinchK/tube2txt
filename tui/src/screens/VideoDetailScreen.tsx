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

  if (loading) return <text>Loading...</text>;
  if (error) return <text color="red">{error}</text>;
  if (!selectedVideo) return <text>Not found</text>;

  const tabs = [
    { name: "Transcript", content: null as string | null },
    ...selectedVideo.ai_files.map((f) => ({ name: f.name, content: f.content })),
  ];

  return (
    <box flexDirection="column" flexGrow={1}>
      {/* Header */}
      <box flexDirection="column" marginBottom={1}>
        <text bold>{selectedVideo.title}</text>
        <text dimColor>{selectedVideo.slug} | {selectedVideo.url} | {selectedVideo.processed_at}</text>
      </box>

      {/* Tabs */}
      <box marginBottom={1}>
        {tabs.map((tab, i) => (
          <text
            key={tab.name}
            inverse={i === activeTab}
            onClick={() => setActiveTab(i)}
          >
            {` ${tab.name} `}
          </text>
        ))}
      </box>

      {/* Content */}
      <scrollbox flexGrow={1} borderStyle="single">
        {activeTab === 0
          ? selectedVideo.segments.map((seg, i) => (
              <text key={i}>
                <span color="cyan">[{seg.start_ts}]</span> {seg.text}
              </text>
            ))
          : <text>{tabs[activeTab]?.content}</text>
        }
      </scrollbox>

      <text dimColor>Tab: switch | o: open in browser | Esc: back</text>
    </box>
  );
}
