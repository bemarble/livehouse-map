import { useState } from "react";
import { SearchBar } from "./SearchBar";
import { VenueList } from "./VenueList";
import { VenueMap } from "./VenueMap";
import { useVenues } from "./useVenues";
import { ErrorBoundary } from "./ErrorBoundary";
import type { Venue } from "./types";
import "./App.css";

type Mode = "map" | "list";

const DEFAULT_FILTERS = {
  keyword: "",
  prefecture: "",
  capacityMin: "",
  capacityMax: "",
};

export default function App() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [mode, setMode] = useState<Mode>("map");
  const [selected, setSelected] = useState<Venue | null>(null);

  const { venues, prefectures, loading, error } = useVenues(filters);

  const handleSelect = (venue: Venue) => {
    setSelected(venue);
    if (mode === "list") setMode("map");
  };

  return (
    <div className="app">
      <header className="header">
        <h1>ライブハウスマップ</h1>
        <span className="count">{venues.length} 件</span>
      </header>

      <div className="toolbar">
        <SearchBar filters={filters} prefectures={prefectures} onChange={setFilters} />
        <div className="mode-toggle">
          <button
            className={mode === "map" ? "active" : ""}
            onClick={() => setMode("map")}
          >
            地図
          </button>
          <button
            className={mode === "list" ? "active" : ""}
            onClick={() => setMode("list")}
          >
            リスト
          </button>
        </div>
      </div>

      <main className="main">
        {loading && <p className="status">読み込み中...</p>}
        {error && <p className="status error">{error}</p>}

        {!loading && !error && (
          mode === "map" ? (
            <div className="map-layout">
              <aside className="sidebar">
                <VenueList venues={venues} onSelect={handleSelect} selected={selected} />
              </aside>
              <ErrorBoundary>
                <VenueMap venues={venues} selected={selected} onSelect={setSelected} />
              </ErrorBoundary>
            </div>
          ) : (
            <VenueList venues={venues} onSelect={handleSelect} selected={selected} />
          )
        )}
      </main>
    </div>
  );
}
