import type { Venue } from "./types";

type Props = {
  venues: Venue[];
  onSelect: (venue: Venue) => void;
  selected: Venue | null;
};

export function VenueList({ venues, onSelect, selected }: Props) {
  if (venues.length === 0) {
    return <p className="empty">該当する会場が見つかりませんでした</p>;
  }

  return (
    <ul className="venue-list">
      {venues.map((v) => (
        <li
          key={v.place_id || v.name}
          className={`venue-item ${selected?.name === v.name ? "selected" : ""}`}
          onClick={() => onSelect(v)}
        >
          <div className="venue-name">{v.name}</div>
          <div className="venue-meta">
            <span className="venue-address">{v.address}</span>
            {v.capacity !== null && (
              <span className="venue-capacity">キャパ {v.capacity.toLocaleString()}人</span>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}
