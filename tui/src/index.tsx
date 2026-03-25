import React, { useState } from "react";
import { Box, Text } from "@opentui/react";
import { render } from "@gridland/core";
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
    <Box flexDirection="column" width="100%">
      {/* Navigation bar */}
      <Box paddingX={1} borderStyle="single" borderBottom>
        <Text bold color="cyan">tube2txt</Text>
        <Text>  </Text>
        <Text inverse={screen === "process"} onClick={() => setScreen("process")}> [1] Process </Text>
        <Text inverse={screen === "dashboard"} onClick={() => setScreen("dashboard")}> [2] Dashboard </Text>
        <Text inverse={screen === "search"} onClick={() => setScreen("search")}> [3] Search </Text>
        <Box flexGrow={1} />
        <Text dimColor>ws: {wsStatus}</Text>
      </Box>

      {/* Screen content */}
      <Box flexGrow={1} padding={1}>
        {screen === "process" && <ProcessScreen onWsStatusChange={setWsStatus} />}
        {screen === "dashboard" && <DashboardScreen onSelectVideo={navigateToDetail} />}
        {screen === "search" && <SearchScreen onSelectResult={navigateToDetail} />}
        {screen === "detail" && selectedSlug && (
          <VideoDetailScreen slug={selectedSlug} onBack={() => setScreen("dashboard")} />
        )}
      </Box>
    </Box>
  );
}

render(<App />);
