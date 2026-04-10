"""
Livepocket から東京の音楽ライブ会場名を逆引き収集するスクリプト

フロー:
  1. Livepocket 東京×音楽 のイベント一覧ページからイベントURLを収集
  2. 各イベントページの JSON-LD から会場名、HTML本文から住所を抽出
  3. 会場名で重複排除
  4. 住所があれば Google Geocoding API で座標付与
  5. 住所がなければ Places API でフォールバック
  6. data/venues_from_events.json に保存

使い方:
  export GOOGLE_PLACES_API_KEY="your_api_key"
  python scrape_events.py
"""

import csv
import json
import os
import re
import time
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
OUTPUT_DIR = Path(__file__).parent.parent / "data"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"

BASE = "https://livepocket.jp"
LIST_URL = f"{BASE}/event/search?area=%E9%96%A2%E6%9D%B1&pref=%E6%9D%B1%E4%BA%AC%E9%83%BD&l_cat=%E9%9F%B3%E6%A5%BD"

EXCLUDE_KEYWORDS = [
    "オンライン", "zoom", "配信", "youtube", "teams",
    "自宅", "各自", "未定", "調整中",
]

# 住所の正規表現（都道府県から始まる日本の住所）
ADDRESS_RE = re.compile(r"東京都[^\s\n「」（）]{5,40}")


# ---------------------------------------------------------------------------
# Step 1: イベントURL収集
# ---------------------------------------------------------------------------

def collect_event_urls(max_pages: int = 50) -> list[str]:
    """Livepocket の一覧ページからイベントURLを収集する"""
    urls: list[str] = []
    seen: set[str] = set()

    for page in range(1, max_pages + 1):
        url = LIST_URL if page == 1 else f"{LIST_URL}&page={page}"
        print(f"  一覧 page {page}: {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"    ERROR: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        found = 0
        for a in soup.find_all("a", href=re.compile(r"^/e/")):
            href = a["href"].split("?")[0]  # クエリパラメータを除去
            full = BASE + href
            if full not in seen:
                seen.add(full)
                urls.append(full)
                found += 1

        print(f"    → {found} 件追加 (累計: {len(urls)})")

        # 次ページがなければ終了
        next_page = soup.find("a", string=re.compile(r"次")) or \
                    soup.find("a", attrs={"rel": "next"})
        if not next_page and found == 0:
            print(f"    最終ページ到達")
            break

        time.sleep(0.8)

    return urls


# ---------------------------------------------------------------------------
# Step 2: イベントページから会場情報を抽出
# ---------------------------------------------------------------------------

def extract_venue(soup: BeautifulSoup, url: str) -> Optional[dict]:
    """イベントページから会場名・住所を抽出する"""

    # JSON-LD から会場名を取得
    name = ""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                loc = item.get("location", {})
                n = loc.get("name", "")
                if n:
                    name = n
                    break
            if name:
                break
        except (json.JSONDecodeError, AttributeError):
            pass

    if not name:
        return None
    if any(kw in name for kw in EXCLUDE_KEYWORDS):
        return None

    # HTML本文から東京都の住所を抽出
    body_text = soup.get_text()
    address = ""
    match = ADDRESS_RE.search(body_text)
    if match:
        address = match.group(0).strip()

    return {"name": name, "address": address}


def collect_venues(event_urls: list[str]) -> dict[str, dict]:
    """イベントURLリストから会場情報を収集する（会場名で重複排除）"""
    venues: dict[str, dict] = {}

    for i, url in enumerate(event_urls):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  [{i+1}/{len(event_urls)}] ERROR: {e}")
            time.sleep(1)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        venue = extract_venue(soup, url)

        if venue:
            name = venue["name"]
            if name not in venues:
                venues[name] = venue
                print(f"  [{i+1}/{len(event_urls)}] 新規: {name} / {venue['address'] or '住所なし'}")
        else:
            print(f"  [{i+1}/{len(event_urls)}] 会場情報なし: {url}")

        time.sleep(0.5)

    return venues


# ---------------------------------------------------------------------------
# Step 3: ジオコーディング
# ---------------------------------------------------------------------------

def geocode_by_address(address: str) -> tuple[Optional[float], Optional[float]]:
    """Google Geocoding API で住所から座標を取得する"""
    try:
        resp = requests.get(
            GEOCODING_URL,
            params={"address": address, "key": API_KEY, "language": "ja", "region": "JP"},
            timeout=10,
        )
        data = resp.json()
        if data.get("status") == "OK":
            loc = data["results"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]
    except requests.RequestException:
        pass
    return None, None


def lookup_by_name(name: str) -> tuple[Optional[float], Optional[float], str, str]:
    """Places API で会場名から座標・住所・place_id を取得する（フォールバック）"""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.id,places.formattedAddress,places.location",
    }
    body = {
        "textQuery": f"{name} 東京",
        "languageCode": "ja",
        "regionCode": "JP",
        "maxResultCount": 1,
    }
    try:
        resp = requests.post(PLACES_SEARCH_URL, headers=headers, json=body, timeout=10)
        if not resp.ok:
            return None, None, "", ""
        places = resp.json().get("places", [])
        if not places:
            return None, None, "", ""
        p = places[0]
        loc = p.get("location", {})
        return loc.get("latitude"), loc.get("longitude"), p.get("formattedAddress", ""), p.get("id", "")
    except requests.RequestException:
        return None, None, "", ""


def geocode_venues(venues: dict[str, dict]) -> list[dict]:
    """全会場に座標を付与する"""
    result: list[dict] = []
    items = sorted(venues.items())

    for i, (name, v) in enumerate(items):
        address = v.get("address", "")
        lat, lng, place_id = None, None, ""

        if address:
            lat, lng = geocode_by_address(address)
            print(f"  [{i+1}/{len(items)}] {name} → {lat}, {lng}")
            time.sleep(0.05)
        else:
            lat, lng, address, place_id = lookup_by_name(name)
            print(f"  [{i+1}/{len(items)}] {name} → Places API: {lat}, {lng}")
            time.sleep(0.1)

        result.append({
            "name": name,
            "address": address,
            "capacity": None,
            "lat": lat,
            "lng": lng,
            "place_id": place_id,
            "source": "events",
        })

    return result


# ---------------------------------------------------------------------------
# 保存
# ---------------------------------------------------------------------------

def save_results(venues: list[dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUTPUT_DIR / "venues_from_events.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(venues, f, ensure_ascii=False, indent=2)
    print(f"JSON saved: {json_path}")

    csv_path = OUTPUT_DIR / "venues_from_events.csv"
    fields = ["name", "address", "capacity", "lat", "lng", "place_id", "source"]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for v in venues:
            writer.writerow({k: v.get(k, "") for k in fields})
    print(f"CSV saved: {csv_path}")


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main() -> None:
    if not API_KEY:
        print("ERROR: 環境変数 GOOGLE_PLACES_API_KEY を設定してください")
        return

    print("=== Livepocket 東京音楽イベント 会場収集 ===\n")

    print("Step 1: イベントURL収集中...")
    event_urls = collect_event_urls(max_pages=50)
    print(f"  合計 {len(event_urls)} 件のイベントURL\n")

    print("Step 2: 会場情報を抽出中...")
    venues = collect_venues(event_urls)
    print(f"  ユニーク会場: {len(venues)} 件\n")

    if not venues:
        print("会場が0件でした。")
        return

    print("Step 3: 座標取得中...")
    result = geocode_venues(venues)

    print("\nStep 4: 保存中...")
    save_results(result)

    with_coords = sum(1 for v in result if v.get("lat"))
    print(f"\n=== 完了 ===")
    print(f"  総件数:   {len(result)}")
    print(f"  座標あり: {with_coords}")


if __name__ == "__main__":
    main()
