import React from "react";

interface Props {
  slug: string;
  title: string;
  processedAt: string;
  selected: boolean;
  onSelect: () => void;
}

export function VideoCard({ slug, title, processedAt, selected, onSelect }: Props) {
  return (
    <box
      borderStyle="single"
      borderColor={selected ? "cyan" : undefined}
      paddingX={1}
      onClick={onSelect}
    >
      <box flexDirection="column" flexGrow={1}>
        <text bold>{title}</text>
        <text dimColor>{slug} | {processedAt}</text>
      </box>
    </box>
  );
}
