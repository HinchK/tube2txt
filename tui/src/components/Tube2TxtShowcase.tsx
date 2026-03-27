import React, { useState, useEffect, useRef } from 'react';

/**
 * Tube2TxtShowcase
 * A standalone React component that showcases tube2txt with a Gridland/TUI aesthetic.
 * Features:
 * - CRT scanline and flicker effect
 * - Simulated CLI terminal flow
 * - TUI-style feature grid
 */

const CRT_STYLES = `
  @keyframes scanline {
    0% { transform: translateY(-100%); }
    100% { transform: translateY(100%); }
  }
  @keyframes flicker {
    0% { opacity: 0.97; }
    5% { opacity: 0.95; }
    10% { opacity: 0.9; }
    15% { opacity: 0.95; }
    30% { opacity: 0.98; }
    45% { opacity: 0.9; }
    50% { opacity: 0.95; }
    55% { opacity: 0.9; }
    70% { opacity: 0.98; }
    85% { opacity: 0.95; }
    90% { opacity: 0.9; }
    100% { opacity: 0.98; }
  }
  .crt-overlay {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
    background-size: 100% 2px, 3px 100%;
    pointer-events: none;
    z-index: 10;
  }
  .crt-scanline {
    position: absolute;
    top: 0; left: 0; right: 0; height: 100px;
    background: linear-gradient(to bottom, rgba(255, 255, 255, 0), rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0));
    animation: scanline 8s linear infinite;
    pointer-events: none;
    z-index: 11;
  }
  .crt-flicker {
    animation: flicker 0.15s infinite;
  }
`;

const TUIBox = ({ title, children, color = 'cyan', className = '' }: any) => {
  const colorMap: any = {
    cyan: 'border-cyan-500 text-cyan-500',
    magenta: 'border-pink-500 text-pink-500',
    green: 'border-emerald-500 text-emerald-500',
    white: 'border-zinc-500 text-zinc-300',
  };

  return (
    <div className={`relative border-2 p-4 bg-zinc-900/50 ${colorMap[color]} ${className}`} style={{ borderStyle: 'double' }}>
      {title && (
        <div className="absolute -top-3 left-4 bg-zinc-950 px-2 text-xs font-bold uppercase tracking-widest">
          {title}
        </div>
      )}
      {children}
    </div>
  );
};

export default function Tube2TxtShowcase() {
  const [step, setStep] = useState(0); // 0: Idle, 1: Typing, 2: Progress, 3: AI Output
  const [typedCommand, setTypedCommand] = useState('');
  const [progress, setProgress] = useState(0);
  const command = 'tube2txt --ai https://youtube.com/watch?v=dQw4w9WgXcQ';
  
  // Terminal Simulation Logic
  useEffect(() => {
    if (step === 0) {
      const timer = setTimeout(() => setStep(1), 1000);
      return () => clearTimeout(timer);
    }
    
    if (step === 1) {
      if (typedCommand.length < command.length) {
        const timer = setTimeout(() => {
          setTypedCommand(command.slice(0, typedCommand.length + 1));
        }, 50 + Math.random() * 50);
        return () => clearTimeout(timer);
      } else {
        const timer = setTimeout(() => setStep(2), 1000);
        return () => clearTimeout(timer);
      }
    }

    if (step === 2) {
      if (progress < 100) {
        const timer = setTimeout(() => {
          setProgress(prev => Math.min(prev + Math.random() * 15, 100));
        }, 150);
        return () => clearTimeout(timer);
      } else {
        const timer = setTimeout(() => setStep(3), 800);
        return () => clearTimeout(timer);
      }
    }
  }, [step, typedCommand, progress]);

  const reset = () => {
    setStep(0);
    setTypedCommand('');
    setProgress(0);
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-400 font-mono p-4 md:p-8 relative overflow-hidden selection:bg-cyan-500/30">
      <style>{CRT_STYLES}</style>
      
      {/* CRT Effects */}
      <div className="crt-overlay" />
      <div className="crt-scanline" />
      
      <div className="max-w-5xl mx-auto crt-flicker relative z-0">
        
        {/* Header */}
        <header className="mb-8 flex justify-between items-center border-b border-zinc-800 pb-4">
          <div>
            <h1 className="text-2xl font-black text-cyan-400 tracking-tighter">TUBE2TXT <span className="text-xs font-normal text-zinc-600">v1.2.0</span></h1>
            <p className="text-xs text-zinc-500">TRANSCRIPTION & AI ANALYSIS ENGINE</p>
          </div>
          <div className="text-right">
            <div className="text-xs text-zinc-500">SYSTEM STATUS: <span className="text-emerald-500">OPERATIONAL</span></div>
            <div className="text-xs text-zinc-600 font-bold uppercase">{new Date().toLocaleDateString()}</div>
          </div>
        </header>

        {/* Main Terminal Area */}
        <TUIBox title="Interactive Demo" color="white" className="mb-8 min-h-[400px]">
          <div className="space-y-4 text-sm md:text-base">
            <div className="flex gap-2">
              <span className="text-emerald-500 font-bold">$</span>
              <span>{typedCommand}<span className={`${step === 1 || step === 0 ? 'animate-pulse' : 'hidden'} bg-cyan-500 w-2 h-5 inline-block align-middle ml-1`} /></span>
            </div>

            {step >= 2 && (
              <div className="space-y-2 animate-in fade-in duration-500">
                <div className="text-zinc-500">[{new Date().toLocaleTimeString()}] <span className="text-cyan-400 font-bold">INFO</span> Initializing pipeline...</div>
                <div className="text-zinc-500">[{new Date().toLocaleTimeString()}] <span className="text-cyan-400 font-bold">INFO</span> Downloading VTT via yt-dlp...</div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-zinc-600 w-20">DOWNLOAD:</span>
                  <div className="flex-grow bg-zinc-800 h-4 border border-zinc-700 relative">
                    <div 
                      className="bg-cyan-500 h-full transition-all duration-200" 
                      style={{ width: `${progress}%` }}
                    />
                    <div className="absolute inset-0 flex justify-center items-center text-[10px] text-white font-bold mix-blend-difference">
                      {Math.floor(progress)}%
                    </div>
                  </div>
                </div>
                {progress === 100 && (
                  <div className="text-zinc-500">[{new Date().toLocaleTimeString()}] <span className="text-cyan-400 font-bold">INFO</span> Processing complete. Invoking Gemini Pro...</div>
                )}
              </div>
            )}

            {step === 3 && (
              <div className="mt-6 border-t border-zinc-800 pt-6 animate-in slide-in-from-bottom-4 duration-700">
                <div className="text-cyan-400 font-bold mb-4 flex justify-between">
                  <span>## AI GENERATED OUTLINE</span>
                  <button onClick={reset} className="text-[10px] border border-cyan-800 px-2 py-0.5 hover:bg-cyan-900/50 transition-colors uppercase">Restart</button>
                </div>
                <div className="space-y-4 text-cyan-300">
                  <div className="pl-4 border-l-2 border-cyan-900">
                    <div className="font-bold flex gap-4">
                      <span className="text-cyan-600">[00:00]</span>
                      <span>Introduction to the Pipeline</span>
                    </div>
                    <p className="text-xs text-cyan-500/80 mt-1 italic">Overview of how Tube2Txt handles massive video datasets with local SQLite indexing.</p>
                  </div>
                  <div className="pl-4 border-l-2 border-cyan-900">
                    <div className="font-bold flex gap-4">
                      <span className="text-cyan-600">[02:45]</span>
                      <span>Gemini Pro Analysis Integration</span>
                    </div>
                    <p className="text-xs text-cyan-500/80 mt-1 italic">Leveraging structured prompts to extract specific metadata and searchable tags.</p>
                  </div>
                  <div className="pl-4 border-l-2 border-cyan-900">
                    <div className="font-bold flex gap-4">
                      <span className="text-cyan-600">[05:12]</span>
                      <span>Exporting to Static HTML</span>
                    </div>
                    <p className="text-xs text-cyan-500/80 mt-1 italic">Demonstrating the local-first philosophy of generating portable, searchable web pages.</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </TUIBox>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <TUIBox title="AI Voice" color="magenta">
            <h3 className="font-bold mb-2">SMART VOICE</h3>
            <p className="text-xs leading-relaxed opacity-80">
              Convert any transcript into naturally segmented sections with AI-generated titles and summaries.
            </p>
          </TUIBox>
          <TUIBox title="Smart Clips" color="green">
            <h3 className="font-bold mb-2">AUTO CLIPPING</h3>
            <p className="text-xs leading-relaxed opacity-80">
              Automatically identify the most valuable 60-second segments for social media or internal review.
            </p>
          </TUIBox>
          <TUIBox title="Global Search" color="cyan">
            <h3 className="font-bold mb-2">FTS5 INDEXING</h3>
            <p className="text-xs leading-relaxed opacity-80">
              Search across thousands of videos instantly using SQLite's Full-Text Search 5 engine.
            </p>
          </TUIBox>
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-[10px] text-zinc-700 tracking-[0.2em] uppercase">
          [ Built for the terminal-first generation ] — (c) 2026 Tube2Txt
        </footer>

      </div>
    </div>
  );
}
