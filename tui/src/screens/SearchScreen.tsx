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
    <div className="flex flex-col flex-grow p-4 bg-zinc-950 text-zinc-300 font-mono">
      <div className="flex items-center gap-4 mb-6 border-b border-zinc-800 pb-4">
        <span className="text-cyan-400 font-bold uppercase tracking-widest text-xs">Search Intelligence:</span>
        <input 
          className="flex-grow bg-zinc-900 border border-zinc-800 p-2 text-cyan-50 focus:outline-none focus:border-cyan-500"
          value={query} 
          onChange={(e) => setQuery(e.target.value)} 
          placeholder="Type keywords to search across all transcripts..." 
        />
      </div>

      <div className="flex-grow overflow-y-auto">
        {loading && <div className="p-4 text-zinc-500 animate-pulse font-bold">QUERYING FTS5 DATABASE...</div>}
        {error && <div className="p-4 text-red-500 border border-red-900 bg-red-900/10">{error}</div>}

        {!loading && results.length === 0 && query.length >= 2 && (
          <div className="p-8 text-center text-zinc-600 italic border border-zinc-900">
            No matches found for "{query}"
          </div>
        )}

        <div className="flex flex-col gap-2">
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
        </div>
      </div>
    </div>
  );
}
