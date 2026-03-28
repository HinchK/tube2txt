import React, { useState } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { TerminalLog } from "../components/TerminalLog";

const WS_URL = `ws://${window.location.hostname}:8000/ws/process`;

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
    <div className="flex flex-col flex-grow h-full bg-zinc-950 p-4 text-zinc-300 font-mono">
      <div className="flex flex-col gap-4 mb-6">
        <div className="flex items-center gap-2">
          <span className="text-cyan-400 font-bold">Command or URL:</span>
          <input 
            className="flex-grow bg-zinc-900 border border-zinc-800 p-2 text-cyan-50 focus:outline-none focus:border-cyan-500"
            value={command} 
            onChange={(e) => setCommand(e.target.value)} 
            placeholder='https://... OR tube2txt my-vid "https://..." --ai' 
          />
        </div>
        <div>
          <button
            className={`px-4 py-2 font-bold uppercase tracking-widest border ${
              isRunning 
                ? "border-zinc-700 text-zinc-600 cursor-not-allowed" 
                : "border-emerald-500 text-emerald-500 hover:bg-emerald-900/20"
            }`}
            onClick={isRunning ? undefined : startJob}
            disabled={isRunning}
          >
            {isRunning ? "[ Processing... ]" : "[ Start Processing ]"}
          </button>
        </div>
      </div>
      <div className="flex-grow overflow-hidden flex flex-col border border-zinc-800 bg-zinc-900/50">
        <div className="bg-zinc-800 px-2 py-1 text-[10px] uppercase font-bold tracking-tighter text-zinc-500">
          Terminal Output
        </div>
        <div className="flex-grow overflow-y-auto p-4">
          <TerminalLog messages={messages} />
        </div>
      </div>
    </div>
  );
}
