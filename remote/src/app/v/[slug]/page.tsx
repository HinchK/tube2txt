import { Navbar } from '@/components/Navbar';
import { IntelligenceBrief } from '@/components/IntelligenceBrief';
import { DataStream } from '@/components/DataStream';
import { createClient } from '@/utils/supabase/server';
import { notFound } from 'next/navigation';

export const dynamic = 'force-dynamic';

export default async function VideoDetail({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const supabase = await createClient();

  // Fetch video record
  const { data: video } = await supabase
    .from('videos')
    .select('*')
    .eq('slug', slug)
    .single();

  if (!video) {
    notFound();
  }

  // Fetch metadata records (outline, notes, transcript, etc)
  const { data: metadataRow } = await supabase
    .from('metadata')
    .select('*')
    .eq('video_slug', slug)
    .single();

  const bundle = metadataRow ? JSON.parse(metadataRow.content) : {};
  
  const outline = bundle.outline || '';
  const notes = bundle.notes || '';
  const technical = bundle.technical || '';
  const recipe = bundle.recipe || '';
  const clips = bundle.clips || '';
  const segments = bundle.transcript || [];

  const videoId = video.url ? (video.url.match(/(?:v=|\/)([0-9A-Za-z_-]{11}).*/) || [])[1] : '';

  return (
    <div className="min-h-screen flex flex-col relative overflow-x-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/5 via-background to-background -z-10" />
      <Navbar />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-12 flex flex-col md:flex-row gap-8">
        
        {/* Left Column: Picture Box & Details */}
        <div className="md:w-1/3 space-y-6">
          <div className="sticky top-24 space-y-6">
            
            {/* Top-Left Picture Box: YouTube Thumbnail */}
            <div className="border-2 border-primary/30 rounded-lg overflow-hidden relative group shadow-[0_0_20px_rgba(0,255,65,0.1)]">
              <a href={video.url} target="_blank" rel="noreferrer" className="block relative aspect-video">
                {videoId ? (
                  <img 
                    src={`https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`} 
                    alt="Source Preview" 
                    className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-all duration-500 scale-105 group-hover:scale-100"
                  />
                ) : (
                  <div className="w-full h-full bg-background/50 flex items-center justify-center font-sharetech text-textMuted text-xs">
                    NO PREVIEW
                  </div>
                )}
                <div className="absolute inset-0 bg-primary/20 group-hover:bg-transparent transition-colors pointer-events-none" />
                <div className="absolute top-2 left-2 bg-primary text-black px-2 py-0.5 text-[10px] font-orbitron font-bold uppercase tracking-tighter">
                  Source Feed
                </div>
                <div className="absolute bottom-2 right-2 bg-background/90 px-3 py-1 text-[10px] font-sharetech text-primary border border-primary/50 backdrop-blur-sm">
                  NODE.ID: {videoId || 'UNKNOWN'}
                </div>
              </a>
            </div>

            <div className="glass-card p-6 border-white/5">
              <h1 className="text-xl font-orbitron font-bold text-white uppercase mb-4 leading-tight">{video.title}</h1>
              <div className="font-sharetech text-textMuted border-l-2 border-primary pl-3 space-y-1 text-sm">
                <div>STATUS: <span className="text-primary drop-shadow-[0_0_8px_rgba(0,255,65,0.8)]">SYNCHRONIZED</span></div>
                <div>DATE: {new Date(video.date).toLocaleDateString()}</div>
                <div>ORIGIN: <span className="text-accent">YOUTUBE_GRID</span></div>
              </div>
            </div>
            
            {outline && (
              <div className="glass-card p-6 text-sm font-inter border-white/5">
                <h3 className="font-orbitron text-xs text-primary mb-4 uppercase tracking-widest border-b border-white/10 pb-2">Transmission Outline</h3>
                <div className="text-textMuted whitespace-pre-wrap leading-relaxed opacity-80">{outline}</div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Intelligence & Data */}
        <div className="md:w-2/3 space-y-8">
          
          {/* 1. Technical Specifications (Promoted to Top) */}
          {technical && (
            <div className="glass-card p-8 border-white/5 group hover:border-white/10 transition-colors">
              <h2 className="text-xl font-orbitron text-blue-400 mb-6 uppercase border-b border-white/10 pb-4">Technical Specifications</h2>
              <div className="text-textMuted font-inter whitespace-pre-wrap leading-relaxed prose prose-invert max-w-none">
                <IntelligenceBrief content={technical} />
              </div>
            </div>
          )}

          {/* 2. Data Stream (with persisted URL) */}
          {segments.length > 0 && (
            <DataStream videoId={videoId} segments={segments} baseUrl={video.url} />
          )}

          {/* 3. Intelligence Brief (Notes) */}
          {notes && (
            <IntelligenceBrief content={notes} />
          )}

          {/* 4. Additional Content */}
          {[
            { label: 'Operations Manual (Recipe)', content: recipe, color: 'text-orange-400' },
            { label: 'Key Extractions (Clips)', content: clips, color: 'text-purple-400' }
          ].map((section, i) => section.content && (
            <div key={i} className="glass-card p-8 border-white/5 group hover:border-white/10 transition-colors">
              <h2 className={`text-xl font-orbitron ${section.color || 'text-primary'} mb-6 uppercase border-b border-white/10 pb-4`}>{section.label}</h2>
              <div className="text-textMuted font-inter whitespace-pre-wrap leading-relaxed prose prose-invert max-w-none">
                <IntelligenceBrief content={section.content} />
              </div>
            </div>
          ))}

          {(!segments.length && !notes && !technical && !recipe && !clips) && (
            <div className="glass-card p-12 text-center font-sharetech text-textMuted border-dashed border-white/10">
              NO DATA STREAMS CAPTURED FOR THIS NODE.
            </div>
          )}
        </div>
        
      </main>
    </div>
  );
}
