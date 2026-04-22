-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE IF NOT EXISTS public.videos (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  date timestamp with time zone NOT NULL DEFAULT now(),
  slug text NOT NULL UNIQUE,
  title text,
  CONSTRAINT videos_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.metadata (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  video_slug character varying,
  type text,
  content text,
  vid_id bigint NOT NULL UNIQUE,
  CONSTRAINT metadata_pkey PRIMARY KEY (id),
  CONSTRAINT metadata_vid_id_fkey FOREIGN KEY (vid_id) REFERENCES public.videos(id) ON DELETE CASCADE
);

-- RLS POLICIES
-- Enable RLS
ALTER TABLE public.videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.metadata ENABLE ROW LEVEL SECURITY;

-- Allow anonymous read access to videos
CREATE POLICY "Allow anonymous read access" ON public.videos
  FOR SELECT USING (true);

-- Allow anonymous read access to metadata
CREATE POLICY "Allow anonymous read access" ON public.metadata
  FOR SELECT USING (true);

-- Allow service role full access (already exists by default, but for clarity)
-- Service role bypasses RLS in most cases, but if we wanted explicit policies:
-- CREATE POLICY "Allow service role all access" ON public.videos
--   FOR ALL TO service_role USING (true) WITH CHECK (true);
