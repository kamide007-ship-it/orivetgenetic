# HANDOFF.md — 前回セッション引き継ぎ

## 完了タスク（このセッション）

| PR | 内容 | 状態 |
|---|---|---|
| #27 | ディスク枯渇修正・OCR timeout・サイレントexcept撲滅・/healthz・413 handler | ✅ マージ済み |
| #28 | iOS 100dvh・aria-label・コントラスト・bfcache spinner・pytest 25件 | ✅ マージ済み |
| (直接push予定) | CI workflow・マジックバイト検証・.spec/.agent 整備 | 🚧 作業中 |

## 次セッションで最初にやること

1. `git pull origin main` でローカルを同期
2. `pytest test_app.py -v` で 33テスト全通過を確認
3. 下記「保留タスク」の優先度を確認

## 保留タスク（優先度順）

### 高優先度（ユーザー入力が来たら即着手）

- **T002 COI 数値検証**: サンプル血統書データ（既知 COI 値つき）が必要
  - `calc_coi_cross` の `seen` set が正しく機能しているか検証
  - 既知ケース例: AKC 公開血統 or ブリーダーが計算済みの COI 値
- **解析精度改善**: Orivet PDF / JKC 血統書 / ALAJ 血統書サンプル提供待ち
  - 提供されたら `TestParser` クラスを `test_app.py` に追加
  - Before/After 比較表を提示してから実装

### 中優先度（自律的に進められる）

- **UI 実機確認**: iPhone Safari での `100dvh` / bfcache リセット動作確認
  - スクリーンショット提供で検証可能
- **レポート HTML テーブルのスマホ横スクロール対応**
  - `generate_unified_html`（`poodle_genetics.py:1687-2282`）の table CSS を要確認

### 低優先度

- **KNOWLEDGE.md 作成**: PDF フォーマット構造・OCR 誤認識辞書の文書化
- **COI の `(1+F_A)` 完全 Wright 公式対応**: 共通祖先自身の近交係数補正
- **レポート PDF 出力機能**: 日本語フォント埋め込みが必要（`reportlab` or `weasyprint`）

## 注意点・ブロッカー

- `poodle_genetics.py` は 2734 行の巨大ファイル。全体把握より関数単位で確認すること
- `pedigree_ocr.py` の `try_ocr` は現在 `app.py` 経路では使われていない
  （`app.py` は `poodle_genetics.try_ocr` を使用）。混在に注意
- `calc_coi_3gen` と `calc_coi_cross` のロジック差異は意図的か不明。サンプルなしに変更禁止
- Render 無料枠: メモリ OOM の実測なし。大 PDF 並列処理時のピークは未確認

## MEMORY.md に追記すべき教訓（次セッション向け）

- 追記内容があれば `.agent/memory/MEMORY.md` に章を追加
- バグパターンは `[BUG-NNN]` 形式、誤判定は `[WRONG-NNN]` 形式
