import React from "react";

interface Message {
  type: string;
  step?: string;
  message?: string;
}

export function TerminalLog({ messages }: { messages: Message[] }) {
  return (
    <div className="flex flex-col gap-1">
      {messages.map((msg, i) => {
        const prefix = msg.type === "error" ? "!" : ">";
        const colorClass = 
          msg.type === "error" ? "text-red-500" : 
          msg.type === "complete" ? "text-emerald-500" : 
          "text-cyan-400";
        
        return (
          <div key={i} className={`${colorClass} whitespace-pre-wrap`}>
            <span className="opacity-50 mr-2">{prefix}</span>
            {msg.message || ""}
          </div>
        );
      })}
      {messages.length === 0 && (
        <div className="text-zinc-600 italic">Waiting for job...</div>
      )}
    </div>
  );
}
