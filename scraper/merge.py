"""
scrape_places.py と scrape_events.py の結果を統合するスクリプト

名寄せ基準（安全な順に優先）:
  1. place_id 一致         → 確実に同一会場（Google が保証）
  2. 正規化名の完全一致    → 全角半角・大小文字・記号を除いて一致
  3. 住所の完全一致        → 同じ住所 = 同じ建物

※ 編集距離などのファジーマッチは「GotandaG4」と「GotandaG6」のような
   類似名だが別会場を誤マージするリスクがあるため使用しない

使い方:
  python merge.py
"""

import json
import re
import csv
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

INPUT_FILES = [
    DATA_DIR / "livehouses_tokyo.json",
    DATA_DIR / "venues_from_events.json",
]
OUTPUT_JSON = DATA_DIR / "venues_all.json"
OUTPUT_CSV = DATA_DIR / "venues_all.csv"


def normalize_name(name: str) -> str:
    """
    会場名を正規化する。
    - 全角英数字 → 半角
    - 大文字 → 小文字
    - スペース・記号・括弧を除去
    ※ 数字は除去しない（G4とG6を区別するため）
    """
    # 全角英数字 → 半角
    name = name.translate(str.maketrans(
        "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
        "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
        "０１２３４５６７８９",
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
    ))
    # 小文字化
    name = name.lower()
    # スペース・ハイフン・中黒・括弧・記号を除去（数字は残す）
    name = re.sub(r"[\s\u3000\-－―・【】「」()（）『』\[\]]", "", name)
    return name


def normalize_address(address: str) -> str:
    """住所を正規化する（空白・全角スペース除去）"""
    if not address:
        return ""
    address = address.strip()
    address = re.sub(r"[\s\u3000]", "", address)
    return address


def merge(files: list[Path]) -> list[dict]:
    seen_place_ids: set[str] = set()
    seen_names: set[str] = set()
    seen_addresses: set[str] = set()
    merged: list[dict] = []
    skipped = 0

    for path in files:
        if not path.exists():
            print(f"スキップ（ファイルなし）: {path}")
            continue

        with open(path, encoding="utf-8") as f:
            venues = json.load(f)

        added = 0
        for v in venues:
            place_id = v.get("place_id", "")
            norm_name = normalize_name(v.get("name", ""))
            norm_addr = normalize_address(v.get("address", ""))

            # 1. place_id で重複チェック
            if place_id and place_id in seen_place_ids:
                skipped += 1
                continue

            # 2. 正規化名で重複チェック
            if norm_name and norm_name in seen_names:
                skipped += 1
                continue

            # 3. 住所で重複チェック（住所が十分な長さの場合のみ）
            if norm_addr and len(norm_addr) >= 8 and norm_addr in seen_addresses:
                skipped += 1
                continue

            # 登録
            if place_id:
                seen_place_ids.add(place_id)
            if norm_name:
                seen_names.add(norm_name)
            if norm_addr and len(norm_addr) >= 8:
                seen_addresses.add(norm_addr)

            merged.append(v)
            added += 1

        print(f"{path.name}: {added} 件追加")

    print(f"重複除去: {skipped} 件スキップ")
    return merged


def save(venues: list[dict], json_path: Path, csv_path: Path) -> None:
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(venues, f, ensure_ascii=False, indent=2)
    print(f"JSON saved: {json_path}")

    fields = ["name", "address", "capacity", "lat", "lng", "place_id", "source"]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for v in venues:
            writer.writerow({k: v.get(k, "") for k in fields})
    print(f"CSV saved: {csv_path}")


def main() -> None:
    print("=== データ統合 ===\n")
    merged = merge(INPUT_FILES)
    print(f"\n統合後: {len(merged)} 件")
    save(merged, OUTPUT_JSON, OUTPUT_CSV)

    with_coords = sum(1 for v in merged if v.get("lat"))
    with_cap = sum(1 for v in merged if v.get("capacity"))
    print(f"\n=== サマリー ===")
    print(f"  総件数:     {len(merged)}")
    print(f"  座標あり:   {with_coords}")
    print(f"  キャパあり: {with_cap}")


if __name__ == "__main__":
    main()
