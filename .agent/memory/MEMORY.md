# MEMORY.md — poodle-genetics 学習済み知識・教訓

## アーキテクチャ

- **エントリポイント**: `app.py`（Flask + gunicorn）
- **解析コア**: `poodle_genetics.py`（CLI兼用、2734行）
- **PDF解析**: `orivet_analyzer.py`（pdfplumber）
- **OCR解析**: `pedigree_ocr.py`（pytesseract + Pillow）
- **シミュレーター**: `breeding_simulator.html`（ブラウザ完結、サーバー不要）
- **本番**: Render Docker デプロイ、`SECRET_KEY` 環境変数必須

---

## 既知のバグパターンと対策

### [BUG-001] REPORT_FOLDER ディスク枯渇
- **症状**: セッションディレクトリが無限蓄積 → Render ディスク満杯で起動不能
- **修正**: `app.py` 起動時 `_cleanup_old_session_dirs()` で TTL 超過分を削除（PR #27）
- **設定**: `REPORT_TTL_HOURS` 環境変数（デフォルト 24h）

### [BUG-002] OCR タイムアウト不足
- **症状**: 劣化した写真で Tesseract が長時間ハング → gunicorn 全体に影響
- **修正**: `ocr_timeout = 120`（90s → 120s）+ `RuntimeError` フォールバック（PR #27）
- **場所**: `poodle_genetics.py:try_ocr`, `pedigree_ocr.py:try_ocr`

### [BUG-003] iOS Safari bfcache でスピナー固まる
- **症状**: 解析送信後「戻る」→ submitBtn が disabled のまま再送信不能
- **修正**: `pageshow(persisted)` リスナーで disabled/loading をリセット（PR #28）

### [BUG-006] Excel formula injection（修正済 PR #TBD）
- **症状**: `sanitize_for_excel` は制御文字除去のみで、CSV/Excel formula injection
  （先頭 `=`, `+`, `-`, `@` の式注入）を無害化していなかった
- **影響**: 悪意ある PDF/血統書から抽出されたテキストが Excel 起動時に式として評価
- **修正**: `sanitize_for_excel` を `sanitize_text` の単純別名から拡張。
  制御文字除去後、先頭が `=/+/-/@` なら `'` プレフィックスを付与。
  HTML 側で使われる `sanitize_text` は変更せず、Excel パスだけに影響を局所化。
- **影響範囲確認**: Excel cells に書き込まれる内容（category/test_name/genotype/
  result_text/jp_name）には負数や式始まりの正常データは含まれないことを確認済
- **テスト**: `test_app.py::TestSanitizeForExcel` に7件追加（=,+,-,@ 各プレフィックス、
  文字列中の = は素通し、遺伝子型は素通し、制御文字除去後の二次防御）

### [BUG-005] エラーログとユーザー報告の紐付け不能
- **症状**: ユーザーが「PDF解析失敗」と報告しても、バックエンドログから該当エラーを引けない
- **修正**: `_log_exc()` ヘルパーで `error_id` を発行し、`app.logger.exception` に構造化記録
  ユーザー向け flash メッセージにも `error_id=xxxxxxxx` を含める
- **ログ書式**: `analyze_error error_id=xxxxxxxx stage=xxx file=xxx exc_type=xxx`
- **検索**: Render ログから `grep "error_id=xxxxxxxx"` で完全特定可能

### [BUG-004] 100vh iOS アドレスバー干渉
- **症状**: iOS Safari でボタンがアドレスバーの裏に隠れる
- **修正**: `min-height: 100vh` → `min-height: 100dvh`（PR #28）

---

## 監査で訂正した誤判定

### [WRONG-001] T003「HEIC opener 統一」— 不要だった
- `poodle_genetics.py:66-67` に `register_heif_opener()` がモジュールロード時に既存
- 誤って「HEIC が読めない」と監査報告したが実際は対応済み

### [WRONG-002] T002「COI 3gen 重複排除」— 再検証が必要
- `calc_coi_3gen` の素朴合計は Wright 経路数え上げ式として正しい可能性が高い
- `add_if_exists` で各 ancestor slot がユニーク追加されるため重複なし
- `calc_coi_cross` の `seen` set は「同 gen × 同 name の重複」を排除しているが、
  これが本当に正しいかはサンプル血統データで検証が必要
- **保留理由**: サンプルなしに変更するとリグレッション

---

## 解析フォーマット知識

### Orivet PDF（遺伝子検査）
- キーワード: `"Genetic Summary Report"` or `"Health Tests Reported"`
- DNAプロファイル（DNAP）: `"ISAG Profile"` or `"DNA Profile"` が含まれ、
  `"Health Tests Reported"` が含まれない場合はスキップ
- 見方ガイド: ファイル名に `見方` or `説明` が含まれる場合はスキップ

### 血統書フォーマット判別優先順位
JKC → ALAJ → AKC → KC → generic（`detect_pedigree_format`）

### COI 計算仕様
- Wright 経路公式: `0.5 ^ (n + m + 1)` を共通祖先ごとに合計
- 3世代上限（`calc_coi_3gen`）
- 交配予測は `calc_coi_cross`（両血統書が必要）
- 名前正規化: スペース揺れを `re.sub(r'\s+', ' ', name.strip().upper())` で吸収

---

## Render 環境注意点

- メモリ上限: 無料枠 512MB（gunicorn workers=2 で大 PDF 並列処理時に OOM リスク）
- ヘルスチェック: `/healthz`（軽量 JSON、テンプレ描画なし）
- ディスク: エフェメラル（再デプロイでリセット）→ REPORT_FOLDER クリーンアップが必須
- ビルド時間: Tesseract + jpn パック + libheif-dev で数分

---

## テスト

- ファイル: `test_app.py`（33テスト、サンプル不要）
- 実行: `pytest test_app.py -v`
- CI: `.github/workflows/test.yml`（push/PR 時に自動実行）
- **サンプルPDF/画像提供時は `TestParser` クラスを追加すること**

---

## セキュリティ実装済み

- `secure_filename()` + UUID プレフィックス（パストラバーサル対策）
- `MAX_CONTENT_LENGTH = 50MB`（Flask 側）
- マジックバイト検証（`_is_valid_pdf`, `_is_valid_image`）
- `report_html | e` フィルタ（XSS 対策、iframe srcdoc）
- `SECRET_KEY` は Render で自動生成（ハードコードなし）
