import React, { useState } from "react";
import { useSearch } from "../hooks/useSearch";
import { SearchResult } from "../components/SearchResult";

interface Props {
  onSelectResult: (slug: string) => void;
}

export function SearchScreen({ onSelectResult }: Props) {
  const [query, setQuery] = useState("");
  const { results, loading, error } = useSearch(query);
  const [selectedIdx, setSelectedIdx] = useState(0);

  return (
    <box flexDirection="column" flexGrow={1}>
      <box>
        <text>Search: </text>
        <input value={query} onChange={setQuery} placeholder="Search transcripts..." />
      </box>

      {loading && <text dimColor>Searching...</text>}
      {error && <text color="red">{error}</text>}

      {!loading && results.length === 0 && query.length >= 2 && (
        <text dimColor>No results.</text>
      )}

      <box flexDirection="column" marginTop={1}>
        {results.map((r, i) => (
          <SearchResult
            key={`${r.slug}-${r.start_ts}`}
            slug={r.slug}
            startTs={r.start_ts}
            text={r.text}
            query={query}
            selected={i === selectedIdx}
            onSelect={() => onSelectResult(r.slug)}
          />
        ))}
      </box>
    </box>
  );
}
