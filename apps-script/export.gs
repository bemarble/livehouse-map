/**
 * Google スプレッドシートの会場データを venues.json として
 * GitHub リポジトリにコミットする Apps Script
 *
 * 設定方法:
 *   1. スクリプトエディタを開く（拡張機能 → Apps Script）
 *   2. GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, GITHUB_PATH を設定する
 *      → スクリプトエディタの「プロジェクトの設定」→「スクリプトプロパティ」に追加
 *   3. 「デプロイ」ボタンを実行する
 *
 * スクリプトプロパティ:
 *   GITHUB_TOKEN  : GitHub Personal Access Token（repo スコープ）
 *   GITHUB_OWNER  : GitHubユーザー名（例: yourname）
 *   GITHUB_REPO   : リポジトリ名（例: livehouse-map）
 *   GITHUB_PATH   : コミット先パス（例: frontend/public/venues.json）
 *   GITHUB_BRANCH : ブランチ名（例: main）※省略時は main
 */

// ---------------------------------------------------------------------------
// エントリーポイント（スプレッドシートのボタンに割り当てる）
// ---------------------------------------------------------------------------

function deployVenues() {
  const props = PropertiesService.getScriptProperties();
  const token  = props.getProperty("GITHUB_TOKEN");
  const owner  = props.getProperty("GITHUB_OWNER");
  const repo   = props.getProperty("GITHUB_REPO");
  const path   = props.getProperty("GITHUB_PATH") || "frontend/public/venues.json";
  const branch = props.getProperty("GITHUB_BRANCH") || "main";

  if (!token || !owner || !repo) {
    SpreadsheetApp.getUi().alert("スクリプトプロパティを設定してください。\n必須: GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO");
    return;
  }

  // スプレッドシートからデータ取得
  const venues = readVenues();
  if (venues.length === 0) {
    SpreadsheetApp.getUi().alert("データが0件です。シートを確認してください。");
    return;
  }

  // JSON 生成
  const json = JSON.stringify(venues, null, 2);

  // GitHub にコミット
  try {
    commitToGitHub({ token, owner, repo, path, branch, content: json });
    SpreadsheetApp.getUi().alert(`✅ デプロイ完了\n${venues.length} 件を ${path} にコミットしました。`);
  } catch (e) {
    SpreadsheetApp.getUi().alert(`❌ エラー: ${e.message}`);
  }
}

// ---------------------------------------------------------------------------
// スプレッドシートから会場データを読み取る
// ---------------------------------------------------------------------------

function readVenues() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const rows  = sheet.getDataRange().getValues();

  if (rows.length < 2) return [];

  const headers = rows[0].map(h => String(h).trim());
  const venues  = [];

  for (let i = 1; i < rows.length; i++) {
    const row = rows[i];
    const v   = {};

    headers.forEach((key, j) => {
      const val = row[j];
      v[key] = val === "" ? null : val;
    });

    // 空行をスキップ
    if (!v["name"]) continue;

    // 数値型に変換
    if (v["lat"]      !== null) v["lat"]      = Number(v["lat"]);
    if (v["lng"]      !== null) v["lng"]      = Number(v["lng"]);
    if (v["capacity"] !== null) v["capacity"] = v["capacity"] === "" ? null : Number(v["capacity"]);

    // NaN になった場合は null に戻す
    if (isNaN(v["lat"]))      v["lat"]      = null;
    if (isNaN(v["lng"]))      v["lng"]      = null;
    if (isNaN(v["capacity"])) v["capacity"] = null;

    venues.push(v);
  }

  return venues;
}

// ---------------------------------------------------------------------------
// GitHub Contents API にコミットする
// ---------------------------------------------------------------------------

function commitToGitHub({ token, owner, repo, path, branch, content }) {
  const apiUrl = `https://api.github.com/repos/${owner}/${repo}/contents/${path}`;
  const headers = {
    "Authorization": `Bearer ${token}`,
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };

  // 既存ファイルの SHA を取得（更新の場合に必要）
  let sha = null;
  const getResp = UrlFetchApp.fetch(`${apiUrl}?ref=${branch}`, {
    method: "get",
    headers,
    muteHttpExceptions: true,
  });
  if (getResp.getResponseCode() === 200) {
    sha = JSON.parse(getResp.getContentText()).sha;
  }

  // Base64 エンコード
  const encoded = Utilities.base64Encode(content, Utilities.Charset.UTF_8);

  const body = {
    message: `chore: venues.json を更新 (${new Date().toLocaleDateString("ja-JP")})`,
    content: encoded,
    branch,
    ...(sha ? { sha } : {}),
  };

  const putResp = UrlFetchApp.fetch(apiUrl, {
    method: "put",
    headers: { ...headers, "Content-Type": "application/json" },
    payload: JSON.stringify(body),
    muteHttpExceptions: true,
  });

  const code = putResp.getResponseCode();
  if (code !== 200 && code !== 201) {
    throw new Error(`GitHub API エラー ${code}: ${putResp.getContentText()}`);
  }
}

// ---------------------------------------------------------------------------
// スプレッドシートにメニューを追加する（スプレッドシートを開いたときに実行）
// ---------------------------------------------------------------------------

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("🎸 ライブハウスマップ")
    .addItem("venues.json をデプロイ", "deployVenues")
    .addToUi();
}
