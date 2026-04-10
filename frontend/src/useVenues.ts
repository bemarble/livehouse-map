import { useState, useEffect, useMemo } from "react";
import type { Venue } from "./types";

type Filters = {
  keyword: string;
  prefecture: string;
  capacityMin: string;
  capacityMax: string;
};

export function useVenues(filters: Filters) {
  const [venues, setVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/venues.json")
      .then((r) => {
        if (!r.ok) throw new Error(`venues.json の読み込みに失敗しました (${r.status})`);
        return r.json() as Promise<Venue[]>;
      })
      .then((data) => {
        setVenues(data);
        setLoading(false);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "不明なエラー");
        setLoading(false);
      });
  }, []);

  const prefectures = useMemo(
    () => Array.from(new Set(venues.map((v) => v.prefecture).filter(Boolean))).sort(),
    [venues]
  );

  const filtered = useMemo(() => {
    const kw = filters.keyword.trim().toLowerCase();
    const capMin = filters.capacityMin === "" ? null : Number(filters.capacityMin);
    const capMax = filters.capacityMax === "" ? null : Number(filters.capacityMax);

    return venues.filter((v) => {
      if (kw && !v.name.toLowerCase().includes(kw) && !v.address.toLowerCase().includes(kw)) {
        return false;
      }
      if (filters.prefecture && v.prefecture !== filters.prefecture) {
        return false;
      }
      if (capMin !== null && (v.capacity === null || v.capacity < capMin)) {
        return false;
      }
      if (capMax !== null && (v.capacity === null || v.capacity > capMax)) {
        return false;
      }
      return true;
    });
  }, [venues, filters]);

  return { venues: filtered, prefectures, loading, error };
}
