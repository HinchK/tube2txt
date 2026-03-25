import React, { useState } from "react";
import { createCliRenderer, createRoot } from "@gridland/core";
import { ProcessScreen } from "./screens/ProcessScreen";
import { DashboardScreen } from "./screens/DashboardScreen";
import { SearchScreen } from "./screens/SearchScreen";
import { VideoDetailScreen } from "./screens/VideoDetailScreen";

type Screen = "process" | "dashboard" | "search" | "detail";

function App() {
  const [screen, setScreen] = useState<Screen>("process");
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState("disconnected");

  const navigateToDetail = (slug: string) => {
    setSelectedSlug(slug);
    setScreen("detail");
  };

  return (
    <box flexDirection="column" width="100%">
      {/* Navigation bar */}
      <box paddingX={1} borderStyle="single">
        <text bold color="cyan">tube2txt</text>
        <text>  </text>
        <text inverse={screen === "process"} onClick={() => setScreen("process")}> [1] Process </text>
        <text inverse={screen === "dashboard"} onClick={() => setScreen("dashboard")}> [2] Dashboard </text>
        <text inverse={screen === "search"} onClick={() => setScreen("search")}> [3] Search </text>
        <box flexGrow={1} />
        <text dimColor>ws: {wsStatus}</text>
      </box>

      {/* Screen content */}
      <box flexGrow={1} padding={1}>
        {screen === "process" && <ProcessScreen onWsStatusChange={setWsStatus} />}
        {screen === "dashboard" && <DashboardScreen onSelectVideo={navigateToDetail} />}
        {screen === "search" && <SearchScreen onSelectResult={navigateToDetail} />}
        {screen === "detail" && selectedSlug && (
          <VideoDetailScreen slug={selectedSlug} onBack={() => setScreen("dashboard")} />
        )}
      </box>
    </box>
  );
}

async function main() {
  const renderer = await createCliRenderer();
  createRoot(renderer).render(<App />);
}

main();
