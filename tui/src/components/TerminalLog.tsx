import React from "react";

interface Message {
  type: string;
  step?: string;
  message?: string;
}

export function TerminalLog({ messages }: { messages: Message[] }) {
  return (
    <scrollbox flexGrow={1} borderStyle="single">
      {messages.map((msg, i) => {
        const prefix = msg.type === "error" ? "!" : ">";
        const color = msg.type === "error" ? "red" : msg.type === "complete" ? "green" : "cyan";
        return (
          <text key={i} color={color}>
            {prefix} {msg.message || ""}
          </text>
        );
      })}
      {messages.length === 0 && <text dimColor>Waiting for job...</text>}
    </scrollbox>
  );
}
