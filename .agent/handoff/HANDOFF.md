# HANDOFF.md — 次セッションへの引き継ぎ（PR #53 マージ後・2026-05-16 状態）

## 全体サマリー

**このセッションは「理解できる」コンセプトを中核として poodle-genetics アプリを大幅進化させた。**

| 軸 | 数 |
|---|---|
| マージ済 PR | 30+ (PR #27〜#53) |
| 修正済バグ | 9件 (BUG-001〜009) |
| pytest テスト | 0 → **161件** |
| 疾患 KB | **72エントリ** (Veqta/Orivet/Embark/PPG 完全カバー) |
| 形質 KB | **14エントリ** (E/K/A/B/D/M/S/G + L/SD/BT/Em + Furnishings/Curly) |
| カテゴリ分類 | 11 + 目次 |
| 重症度3段階 | 高/中/低 + フィルター + 凡例 + バッジ |
| 症状ベース検索 | 10カテゴリ・60+疾患マッピング |
| 新ルート | `/glossary` `/api/glossary` `/healthz` |
| GitHub Actions CI | pytest 自動実行 |

## アーキテクチャ要点

### ファイル構成
```
poodle_genetics.py    主要解析エンジン + KB + HTML生成 (3500+ 行)
  ├ DISEASE_KB (72)   疾患辞書（match/title/summary/mechanism/symptoms/inheritance/advice/references/severity）
  ├ TRAIT_KB (14)     形質辞書（match/title/summary/mechanism/phenotype/advice/references）
  ├ SYMPTOM_INDEX (10) 症状→疾患 マッピング
  ├ DISEASE_CATEGORIES タイトルキーワード → カテゴリ
  ├ SEVERITY_LABELS    重症度ラベル定義
  └ generate_unified_html  レポートHTML生成

app.py                Flask app
  ├ /              index page
  ├ /analyze       PDF/画像アップロード解析
  ├ /report/<id>   生成レポート表示
  ├ /api/dogs/<id> /api/pedigrees/<id>  シミュレーター連携
  ├ /simulator     繁殖シミュレーター（静的HTML）
  ├ /glossary      辞書ページ（症状/重症度/全文検索）
  ├ /api/glossary  KB JSON API
  └ /healthz       軽量ヘルスチェック

templates/
  ├ index.html      ランディング（信頼バッジ・解析中ステップ表示）
  ├ report.html     レポート iframe wrapper
  └ glossary.html   辞書ページ

breeding_simulator.html  シミュレーター本体（1300+ 行）
  ├ 色シミュレーション（E/K/A/B/D/M/S/G 座位・clickable）
  ├ 健康リスク分析（疾患名 → KBモーダル）
  └ COI 計算（人間関係換算 KB 付き）
```

### KB の構造
各 DISEASE_KB エントリ:
```python
{
  "match": ["pattern1", "pattern2", "\\bword boundary\\b"],
  "title": "疾患名 (英略 / 遺伝子)",
  "summary": "1〜2文の概要",
  "mechanism": "発症メカニズム",
  "symptoms": "症状",
  "inheritance": "遺伝様式",
  "advice": "飼育・繁殖アドバイス",
  "severity": "high" | "medium" | "low",  # optional 明示オーバーライド
  "references": [{"label": "...", "url": "..."}],
}
```

`get_disease_severity(entry)` は明示 severity を優先、なければ本文キーワードから推定。

### マッチングの罠
- `_normalize_for_match()` でハイフン・アンダースコアを空白に正規化
- パターンマッチは先頭一致ではなく substring match
- `\bword\b` パターンは正規表現で単語境界
- **第1文字が同じ短い別パターン** が誤マッチする可能性あり（例: "m locus" が "em locus" にもマッチ）
- → そういう場合は `\bm locus\b` で囲む

## 重要な学び・注意点

### [BUG-009] cross() 関数の sort 動作
JS の `cross()` は `[a,b].sort().join('')` でキー化するため、`'at' < 'ay'` で `ay/at` は `"atay"` がキー。
旧コード `aResult["ayat"]` は常に 0 を返していた → ヘテロ確率が完全脱落していた。

```js
/**
 * sorted form ("at" < "ay" → "atay") で lookup する
 * @see cross() JSDoc in breeding_simulator.html
 */
const payat = aResult["atay"];  // ✓
```

### [PROCESS-001] PR バンドル発生
セッション中に何度も「PR が open のまま新コミット push → PR にバンドル」が発生した（#37, #41, #45, #48, #50, #52）。
→ 今後は前PRマージを待ってから次コミットを push する運用に。

### 「理解できる」コンセプトのデザイン哲学
**ユーザーが疑問を持つ全ての箇所に詳細解説への経路がある状態**を目指す:
1. レポート HTML: 各疾患・形質行に `<details>` 折りたたみ + サマリー行に重症度可視化
2. シミュレーター: 座位ラベル `?` / 健康疾患名クリック / 色結果のロカスコード / COI `?` ボタン
3. 辞書ページ: カテゴリ + 重症度 + 症状 + 全文検索の4軸絞り込み

### 重症度の自動推定
キーワード優先順位:
- HIGH: 「予後不良」「致死」「死亡」「失明」「生命に関わる」
- MEDIUM: 「対症療法のみ」「進行性」「重症」「リスク大幅」
- LOW: 「通常は無症状」「QOL 維持可能」「完治はしない」

誤分類はエントリの `severity` フィールドで明示オーバーライド（既に 6件補正済）。

## 次セッションで最初にやること

1. `git pull origin main` でローカル同期
2. `pytest test_app.py -v` で 全件通過を確認
3. `.spec/TODO.md` で保留・Future タスク確認
4. 本ドキュメント (`HANDOFF.md`) で全体把握

## 🩺 KB レビュー Workflow（重要）

**現状の KB は私 (Claude) が生成しており、Orivet 獣医チームの監修を経ていません**。
Orivet ブランドで公開する前にレビュー必須。

エクスポートツール:
```bash
python3 export_kb_review.py
# → kb_review_YYYY-MM-DD.md が生成される（3000+ 行の Markdown）
```

各疾患エントリには:
- 全フィールド（title / match / severity / summary / mechanism / symptoms / inheritance / advice / references）
- レビューチェックリスト 6項目

このファイルを Orivet 獣医チームに共有 → 修正コメント受領 → DISEASE_KB / TRAIT_KB 反映 → デプロイ。

## 残るタスク（優先度順）

### 高優先（ユーザー入力待ち）
- **T009/T010**: 実 Orivet/JKC PDF サンプル提供で解析精度改善
- **実機検証**: iPhone Safari で動作確認・スクリーンショット

### 中優先（自律実行可）
- KITLG (Intensity) 座位対応 — スキャフォルド済、`KITLG_SUPPORTED=true` 変更で動作
- 犬種別の疾患推奨表示
- Wikipedia 検索URL → 直接記事URL 置換（要 URL 検証）

### 低優先
- 英語版 KB 翻訳（XL 工数）
- レポート PDF 出力（日本語フォント埋め込み必要）
- AI API 連携

## 注意点・ブロッカー

- `poodle_genetics.py` は **3500+ 行** の巨大ファイル。全体把握より関数単位で確認推奨
- 既存例犬は `Object.assign({g:'gg'}, ...)` で G 座位デフォルト指定。新例犬は最初から `g` 指定要
- Wikipedia/Google 検索URL は常に有効。**直接記事URLに置換する場合は要URL検証**
- スマホでテストする際は実機推奨（Chrome DevTools の dvh エミュレーションは不完全）

## MEMORY.md / KNOWLEDGE.md へ追記すべき教訓

- 重症度ヒューリスティックの限界と明示 override 戦略
- 症状ベース検索の追加で UX が大きく向上
- 各画面で KB アクセス経路を整える＝「理解できる」アプリ設計の中核
