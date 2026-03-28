import React, { useState } from "react";
import { ProcessScreen } from "./screens/ProcessScreen";
import { DashboardScreen } from "./screens/DashboardScreen";
import { SearchScreen } from "./screens/SearchScreen";
import { VideoDetailScreen } from "./screens/VideoDetailScreen";

type Screen = "process" | "dashboard" | "search" | "detail";

export function App() {
  const [screen, setScreen] = useState<Screen>("process");
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState("disconnected");

  const navigateToDetail = (slug: string) => {
    setSelectedSlug(slug);
    setScreen("detail");
  };

  return (
    <div className="flex flex-col w-full min-h-screen bg-zinc-950 text-zinc-300 font-mono">
      {/* Navigation bar */}
      <div className="flex items-center gap-4 px-4 py-3 border-b border-zinc-800 bg-zinc-900/50">
        <span className="text-xl font-black text-cyan-400 tracking-tighter uppercase italic">tube2txt</span>
        <div className="flex gap-2 ml-4">
          {[
            { id: "process", label: "[1] Process" },
            { id: "dashboard", label: "[2] Dashboard" },
            { id: "search", label: "[3] Search" },
          ].map((nav) => (
            <button
              key={nav.id}
              onClick={() => setScreen(nav.id as Screen)}
              className={`px-3 py-1 text-sm font-bold transition-colors ${
                screen === nav.id 
                  ? "bg-cyan-500 text-zinc-950" 
                  : "hover:bg-zinc-800 text-zinc-500"
              }`}
            >
              {nav.label}
            </button>
          ))}
        </div>
        <div className="flex-grow" />
        <div className={`flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest ${
          wsStatus === "connected" ? "text-emerald-500" : "text-amber-500 animate-pulse"
        }`}>
          <div className={`w-2 h-2 rounded-full ${wsStatus === "connected" ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-amber-500"}`} />
          WS: {wsStatus}
        </div>
      </div>

      {/* Screen content */}
      <div className="flex-grow flex flex-col relative overflow-hidden">
        {screen === "process" && <ProcessScreen onWsStatusChange={setWsStatus} />}
        {screen === "dashboard" && <DashboardScreen onSelectVideo={navigateToDetail} />}
        {screen === "search" && <SearchScreen onSelectResult={navigateToDetail} />}
        {screen === "detail" && selectedSlug && (
          <VideoDetailScreen slug={selectedSlug} onBack={() => setScreen("dashboard")} />
        )}
      </div>
    </div>
  );
}
