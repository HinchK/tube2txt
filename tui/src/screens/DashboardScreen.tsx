import React, { useState } from "react";
import { useVideos } from "../hooks/useVideos";
import { VideoCard } from "../components/VideoCard";

interface Props {
  onSelectVideo: (slug: string) => void;
}

export function DashboardScreen({ onSelectVideo }: Props) {
  const { videos, loading, error } = useVideos();
  const [selectedIdx, setSelectedIdx] = useState(0);

  if (loading) return <text>Loading...</text>;
  if (error) return <text color="red">{error}</text>;
  if (videos.length === 0) {
    return <text dimColor>No videos yet. Press [1] to process your first video.</text>;
  }

  return (
    <box flexDirection="column">
      <text dimColor>{videos.length} video{videos.length !== 1 ? "s" : ""} processed</text>
      <box flexDirection="column" marginTop={1}>
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
      </box>
      <text dimColor>Click to view detail | o: open in browser</text>
    </box>
  );
}
