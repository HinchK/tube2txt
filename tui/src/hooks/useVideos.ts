import { useState, useEffect, useCallback } from "react";

const API_BASE = "http://localhost:8000";

interface Video {
  slug: string;
  url: string;
  title: string;
  processed_at: string;
}

interface VideoDetail extends Video {
  segments: Array<{ start_ts: string; seconds: number; text: string }>;
  ai_files: Array<{ name: string; content: string }>;
}

interface UseVideosReturn {
  videos: Video[];
  selectedVideo: VideoDetail | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  fetchDetail: (slug: string) => Promise<void>;
}

export function useVideos(): UseVideosReturn {
  const [videos, setVideos] = useState<Video[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<VideoDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchVideos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/videos`);
      setVideos(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch videos");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDetail = useCallback(async (slug: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/videos/${slug}`);
      if (!res.ok) throw new Error("Video not found");
      setSelectedVideo(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch video");
      setSelectedVideo(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchVideos();
  }, [fetchVideos]);

  return { videos, selectedVideo, loading, error, refetch: fetchVideos, fetchDetail };
}
