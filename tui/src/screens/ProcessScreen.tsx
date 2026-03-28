import React, { useState } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { TerminalLog } from "../components/TerminalLog";

const WS_URL = "ws://localhost:8000/ws/process";

interface Props {
  onWsStatusChange: (status: string) => void;
}

export function ProcessScreen({ onWsStatusChange }: Props) {
  const [command, setCommand] = useState("");
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
    if (!command || isRunning) return;
    clearMessages();
    setIsRunning(true);
    
    let finalCommand = command.trim();
    if (finalCommand.startsWith("http") && !finalCommand.includes(" ")) {
      finalCommand = `tube2txt hub "${finalCommand}" --ai --mode recipe`;
    }
    
    send({ action: "start", command: finalCommand });
  };

  return (
    <box flexDirection="column" flexGrow={1}>
      <box flexDirection="column" gap={1}>
        <box>
          <text>Command or URL: </text>
          <input 
            value={command} 
            onChange={setCommand} 
            placeholder='https://... OR tube2txt my-vid "https://..." --ai' 
          />
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
