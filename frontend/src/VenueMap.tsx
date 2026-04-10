import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import type { Venue } from "./types";

// Leaflet のデフォルトアイコンが壊れる問題を修正
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

// 選択中の会場に地図を移動させるコンポーネント
function FlyTo({ venue }: { venue: Venue | null }) {
  const map = useMap();
  useEffect(() => {
    if (venue?.lat && venue?.lng) {
      map.flyTo([venue.lat, venue.lng], 15, { duration: 0.8 });
    }
  }, [venue, map]);
  return null;
}

type Props = {
  venues: Venue[];
  selected: Venue | null;
  onSelect: (venue: Venue) => void;
};

export function VenueMap({ venues, selected, onSelect }: Props) {
  const withCoords = venues.filter((v): v is Venue & { lat: number; lng: number } =>
    v.lat !== null && v.lng !== null
  );

  return (
    <MapContainer
      center={[35.6895, 139.6917]}
      zoom={12}
      className="map-container"
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      <FlyTo venue={selected} />
      {withCoords.map((v) => (
        <Marker
          key={v.place_id || v.name}
          position={[v.lat, v.lng]}
          eventHandlers={{ click: () => onSelect(v) }}
        >
          <Popup>
            <strong>{v.name}</strong>
            <br />
            {v.address}
            {v.capacity !== null && (
              <>
                <br />
                キャパ: {v.capacity.toLocaleString()}人
              </>
            )}
            <br />
            <a
              href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(v.name + " " + v.address)}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              Google マップで開く
            </a>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
