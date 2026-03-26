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
        <footer className="mt-16 border-t border-zinc-900 pt-8 pb-12 text-[10px] text-zinc-700 tracking-[0.2em] uppercase">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6 max-w-4xl mx-auto px-4">
            <div className="flex flex-col items-center md:items-start gap-1">
              <span className="text-zinc-500 font-bold tracking-widest text-zinc-500">CODE NAME: OBSIDIAN PULSE</span>
              <span className="text-[9px] opacity-60">REF: 2026-03-26 // 05:55:48-07:00</span>
            </div>
            
            <div className="text-center italic opacity-40 hover:opacity-100 transition-opacity duration-700">
              [ Built for the terminal-first generation ]
            </div>

            <a 
              href="https://github.com/hinchk/tube2txt" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-zinc-600 hover:text-cyan-500 transition-all duration-300 group lowercase tracking-normal bg-zinc-900/30 px-3 py-1.5 rounded-sm border border-zinc-800/50"
            >
              <svg height="14" viewBox="0 0 16 16" version="1.1" width="14" aria-hidden="true" className="opacity-40 group-hover:opacity-100 transition-opacity"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
              github.com/hinchk/tube2txt
            </a>
          </div>
          <div className="mt-8 text-center opacity-30 text-[8px]">
            &copy; 2026 TUBE2TXT &mdash; ALL RIGHTS RESERVED
          </div>
        </footer>

      </div>
    </div>
  );
}
