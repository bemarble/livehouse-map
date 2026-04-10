"""
Google Places API (New) で東京都のライブハウス情報を収集するスクリプト

収集項目:
  - ライブハウス名
  - 住所
  - 座標（lat/lng）
  - キャパシティ（収容人数）※ Places API では取得不可のため空欄

使い方:
  pip install requests
  export GOOGLE_PLACES_API_KEY="your_api_key"
  python scrape_places.py
"""

import csv
import json
import os
import time
from pathlib import Path
from typing import Optional

import requests

API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
OUTPUT_DIR = Path(__file__).parent.parent / "data"

# 東京の区ごとに検索することで取得漏れを減らす
TOKYO_AREAS = [
    "千代田区", "中央区", "港区", "新宿区", "文京区",
    "台東区", "墨田区", "江東区", "品川区", "目黒区",
    "大田区", "世田谷区", "渋谷区", "中野区", "杉並区",
    "豊島区", "北区", "荒川区", "板橋区", "練馬区",
    "足立区", "葛飾区", "江戸川区",
    # 市部（ライブハウスが多い地域）
    "八王子市", "立川市", "吉祥寺", "下北沢", "高円寺",
]

TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"


def text_search(query: str, page_token: Optional[str] = None) -> dict:
    """Places API (New) の Text Search を呼び出す"""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,nextPageToken",
    }
    body: dict = {
        "textQuery": query,
        "languageCode": "ja",
        "regionCode": "JP",
        "maxResultCount": 20,
    }
    if page_token:
        body["pageToken"] = page_token

    resp = requests.post(TEXT_SEARCH_URL, headers=headers, json=body, timeout=10)
    if not resp.ok:
        print(f"    詳細エラー: {resp.status_code} {resp.text}")
    resp.raise_for_status()
    return resp.json()


def collect_venues(areas: list[str]) -> list[dict]:
    """エリアごとにライブハウスを検索して収集する"""
    seen_ids: set[str] = set()
    venues: list[dict] = []

    for area in areas:
        query = f"ライブハウス 東京都{area}"
        print(f"  検索: {query}")
        page_token = None

        while True:
            try:
                result = text_search(query, page_token)
            except requests.HTTPError as e:
                print(f"    ERROR: {e}")
                break

            places = result.get("places", [])
            for place in places:
                place_id = place.get("id", "")
                if place_id in seen_ids:
                    continue
                seen_ids.add(place_id)

                name = place.get("displayName", {}).get("text", "")
                address = place.get("formattedAddress", "")
                loc = place.get("location", {})
                lat = loc.get("latitude")
                lng = loc.get("longitude")

                venues.append({
                    "name": name,
                    "address": address,
                    "capacity": None,
                    "lat": lat,
                    "lng": lng,
                    "place_id": place_id,
                })

            print(f"    → {len(places)} 件取得 (累計: {len(venues)})")

            page_token = result.get("nextPageToken")
            if not page_token:
                break

            # ページトークンが有効になるまで少し待つ
            time.sleep(2)

        time.sleep(0.5)

    return venues


def save_results(venues: list[dict], output_dir: Path) -> None:
    """JSON と CSV で保存する"""
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "livehouses_tokyo.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(venues, f, ensure_ascii=False, indent=2)
    print(f"JSON saved: {json_path}")

    csv_path = output_dir / "livehouses_tokyo.csv"
    fields = ["name", "address", "capacity", "lat", "lng", "place_id"]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for venue in venues:
            writer.writerow({k: venue.get(k, "") for k in fields})
    print(f"CSV saved: {csv_path}")


def main() -> None:
    if not API_KEY:
        print("ERROR: 環境変数 GOOGLE_PLACES_API_KEY を設定してください")
        print("  export GOOGLE_PLACES_API_KEY='your_api_key'")
        return

    print("=== Google Places API 東京ライブハウス収集 ===\n")
    print("エリア別検索中...")

    venues = collect_venues(TOKYO_AREAS)

    print(f"\n合計 {len(venues)} 件収集完了")
    print("保存中...")
    save_results(venues, OUTPUT_DIR)

    with_coords = sum(1 for v in venues if v.get("lat"))
    print(f"\n=== 完了 ===")
    print(f"  総件数:   {len(venues)}")
    print(f"  座標あり: {with_coords}")
    print(f"\nキャパシティは Places API では取得できないため空欄です。")
    print(f"data/livehouses_tokyo.csv を開いて手動で補完するか、")
    print(f"別途 LiveFans 等から補完スクリプトを実行してください。")


if __name__ == "__main__":
    main()
