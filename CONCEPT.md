# ライブハウスマップ コンセプト

## サービス概要

全国のライブハウス・ライブ会場を地図で探せる検索サービス。
小さなライブハウスから大型ホールまで網羅し、Google マップでは見つけにくい会場も収録する。

## ターゲットユーザー

- ライブに行きたいが近くの会場を知らない人
- 遠征先で会場を探しているアーティスト・バンドマン
- 新しい会場を開拓したい音楽ファン

## MVP スコープ

- 東京都の会場を網羅したリストでサービス開始
- 順次、全国展開

---

## アーキテクチャ

```
[管理者]
  Google スプレッドシートで会場データを編集
      ↓ Google Apps Script（手動実行）
  JSON を生成 → GitHub にコミット
      ↓ Cloudflare Pages が自動デプロイ
[ユーザー]
  Cloudflare Pages（フロントエンドのみ）
  → venues.json を fetch → クライアントサイドで検索・地図表示
```

### 技術スタック

| レイヤー | 技術 |
|---|---|
| フロントエンド | React + Vite + TypeScript |
| ホスティング | Cloudflare Pages |
| データ管理 | Google スプレッドシート |
| データ連携 | Google Apps Script |
| 地図表示 | Leaflet + OpenStreetMap（無料） |
| バックエンド | なし（フロントエンドのみで完結） |

---

## データ仕様

### 会場データ項目

| フィールド | 型 | 説明 |
|---|---|---|
| `name` | string | 会場名 |
| `address` | string | 住所 |
| `lat` | number | 緯度 |
| `lng` | number | 経度 |
| `capacity` | number \| null | 収容人数 |
| `place_id` | string | Google Place ID |
| `prefecture` | string | 都道府県 |

### データ管理フロー

1. 収集スクリプト（`scraper/`）で初期データを生成
2. Google スプレッドシートにインポートして人手で確認・補完
3. Apps Script で `public/venues.json` を生成し GitHub へコミット
4. Cloudflare Pages が自動デプロイ

---

## フロントエンド機能

### 検索
- 会場名・住所のキーワード検索
- 都道府県・エリアで絞り込み
- キャパシティ（収容人数）で絞り込み

### 表示
- 地図モード（Leaflet でピンを表示）
- リストモード（一覧表示）

### その他
- 各会場の詳細ページ（住所・キャパ・Google マップリンク）
- スマートフォン対応（レスポンシブ）

---

## 運用方針

- データ更新はスプレッドシートで管理し、Apps Script で手動デプロイ
- サーバーレス・DBなし・バックエンドなしで運用コストを最小化
- OpenStreetMap を使用して地図の API コストをゼロに抑える

---

## ディレクトリ構成

```
livehouse-map/
├── CONCEPT.md
├── frontend/          # React + Vite フロントエンド
│   ├── public/
│   │   └── venues.json   # デプロイされる会場データ
│   └── src/
├── scraper/           # データ収集スクリプト（Python）
│   ├── scrape_places.py
│   ├── scrape_events.py
│   └── merge.py
├── data/              # 収集した生データ（git 管理外）
└── apps-script/       # Google Apps Script
    └── export.gs
```
