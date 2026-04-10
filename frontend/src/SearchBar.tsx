type Filters = {
  keyword: string;
  prefecture: string;
  capacityMin: string;
  capacityMax: string;
};

type Props = {
  filters: Filters;
  prefectures: string[];
  onChange: (filters: Filters) => void;
};

export function SearchBar({ filters, prefectures, onChange }: Props) {
  const set = (key: keyof Filters) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    onChange({ ...filters, [key]: e.target.value });

  return (
    <div className="search-bar">
      <input
        type="text"
        placeholder="会場名・住所で検索"
        value={filters.keyword}
        onChange={set("keyword")}
      />
      <select value={filters.prefecture} onChange={set("prefecture")}>
        <option value="">都道府県（すべて）</option>
        {prefectures.map((p) => (
          <option key={p} value={p}>{p}</option>
        ))}
      </select>
      <div className="capacity-range">
        <input
          type="number"
          placeholder="キャパ 下限"
          value={filters.capacityMin}
          onChange={set("capacityMin")}
          min={0}
        />
        <span>〜</span>
        <input
          type="number"
          placeholder="キャパ 上限"
          value={filters.capacityMax}
          onChange={set("capacityMax")}
          min={0}
        />
        <span>人</span>
      </div>
    </div>
  );
}
