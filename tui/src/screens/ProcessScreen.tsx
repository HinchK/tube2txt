import React, { useState } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { TerminalLog } from "../components/TerminalLog";

const MODES = [
  { label: "outline", value: "outline" },
  { label: "notes", value: "notes" },
  { label: "recipe", value: "recipe" },
  { label: "technical", value: "technical" },
  { label: "clips", value: "clips" },
];
const WS_URL = "ws://localhost:8000/ws/process";

interface Props {
  onWsStatusChange: (status: string) => void;
}

export function ProcessScreen({ onWsStatusChange }: Props) {
  const [url, setUrl] = useState("");
  const [slug, setSlug] = useState("");
  const [modeIdx, setModeIdx] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const { send, messages, status, clearMessages } = useWebSocket(WS_URL);

  React.useEffect(() => onWsStatusChange(status), [status, onWsStatusChange]);

  React.useEffect(() => {
    const last = messages[messages.length - 1];
    if (last?.type === "complete" || last?.type === "error") {
      setIsRunning(false);
    }
  }, [messages]);

  const startJob = () => {
    if (!url || !slug || isRunning) return;
    clearMessages();
    setIsRunning(true);
    send({ action: "start", slug, url, ai: true, mode: MODES[modeIdx].value });
  };

  return (
    <box flexDirection="column" flexGrow={1}>
      <box flexDirection="column" gap={1}>
        <box>
          <text>URL:  </text>
          <input value={url} onChange={setUrl} placeholder="https://youtube.com/watch?v=..." />
        </box>
        <box>
          <text>Slug: </text>
          <input value={slug} onChange={setSlug} placeholder="my-video" />
        </box>
        <box>
          <text>Mode: </text>
          <select options={MODES} onChange={(idx) => setModeIdx(idx)} />
        </box>
        <box>
          <text
            bold
            color={isRunning ? "gray" : "green"}
            onClick={isRunning ? undefined : startJob}
          >
            {isRunning ? "[ Processing... ]" : "[ Start Processing ]"}
          </text>
        </box>
      </box>
      <box marginTop={1} flexGrow={1}>
        <TerminalLog messages={messages} />
      </box>
    </box>
  );
}
