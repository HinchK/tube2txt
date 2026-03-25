import React from "react";

interface Props {
  slug: string;
  startTs: string;
  text: string;
  query: string;
  selected: boolean;
  onSelect: () => void;
}

export function SearchResult({ slug, startTs, text, query, selected, onSelect }: Props) {
  return (
    <box
      borderStyle="single"
      borderColor={selected ? "cyan" : undefined}
      paddingX={1}
      onClick={onSelect}
    >
      <box flexDirection="column">
        <text>
          <span bold>{slug}</span> <span color="cyan">[{startTs}]</span>
        </text>
        <text>{text}</text>
      </box>
    </box>
  );
}
