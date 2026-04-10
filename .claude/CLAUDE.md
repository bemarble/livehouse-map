# CLAUDE.md — AI エージェント実装ルール

このリポジトリは AI エージェントによる実装を前提としています。
必ず以下の方針を守ってください。

---

## サービス概要

全国ライブハウス・ライブ会場の検索サービス。
詳細は `CONCEPT.md` を参照。

---

## 開発方針

1. シンプルな実装
2. MVP 優先（東京都から開始）
3. バックエンドなし・DB なし・フロントエンドのみで完結
4. 運用コスト最小化（Cloudflare Pages 無料枠 + OpenStreetMap）

---

## アーキテクチャ

| コンポーネント | 技術 | 役割 |
|---|---|---|
| フロントエンド | React + Vite + TypeScript | 検索・地図表示 |
| ホスティング | Cloudflare Pages | 静的サイト配信 |
| データ管理 | Google スプレッドシート | 会場データの編集・管理 |
| データ連携 | Google Apps Script | スプレッドシート → JSON → GitHub |
| 地図 | Leaflet + OpenStreetMap | 地図表示（無料） |
| データ収集 | Python スクリプト（scraper/） | 初期データ収集のみ |

---

## ディレクトリ構成

```
livehouse-map/
├── CONCEPT.md
├── frontend/              # React + Vite フロントエンド
│   ├── public/
│   │   └── venues.json   # 会場データ（Apps Script が生成）
│   └── src/
├── scraper/               # 初期データ収集スクリプト（Python）
├── data/                  # 収集生データ（.gitignore 対象）
└── apps-script/           # Google Apps Script ソース
```

---

## コードスタイル

- TypeScript: 厳密な型付け（`any` 禁止、`unknown` を使う）
- エラーは握りつぶさず、意味のあるメッセージ付きで処理する
- コンポーネントは小さく保つ
- 不要なライブラリを追加しない

---

## データ仕様

### venues.json スキーマ

```typescript
type Venue = {
  name: string;
  address: string;
  lat: number | null;
  lng: number | null;
  capacity: number | null;
  place_id: string;
  prefecture: string;
};
```

### 名寄せルール（merge.py）

重複判定は以下の順で行う（ファジーマッチは使用しない）:
1. `place_id` の一致
2. 正規化後の会場名の完全一致
3. 住所の完全一致（8文字以上の場合のみ）

「GotandaG4」と「GotandaG6」のように類似名だが別会場のケースがあるため、
編集距離などによるファジーマッチは禁止。

---

## 禁止事項

- バックエンド・DB の導入
- 有料 API の追加（Google Maps JavaScript API の地図表示など）
- `any` 型の使用
- README・ドキュメントを確認なしに生成・変更
- 既存の動作するコードを理由なくリファクタリング

---

## Git 規約

- Conventional Commits 形式、本文は日本語
  - 例: `feat: 会場検索フィルターを追加`
- 確認なしに自動コミット・自動 push しない
- `data/` ディレクトリは `.gitignore` に含める（生データはコミットしない）
- `frontend/public/venues.json` はコミット対象（Apps Script が生成するデータ）
