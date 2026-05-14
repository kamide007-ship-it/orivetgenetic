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

## ログ構造（観測性）

### /analyze ログイベント
- `analyze_start request_id=XXX session_id=YYY pdf_files=N pedigree_files=M`
- `analyze_empty request_id=XXX session_id=YYY ...`（解析可能データなし）
- `analyze_success request_id=XXX session_id=YYY dogs=N pedigrees=M elapsed_ms=T`
- `analyze_error error_id=ZZ request_id=XXX stage=... file=... exc_type=...`

### 検索例
- 特定ユーザーの「結果が変」報告: `grep "request_id=xxxxxxxx"` で start→success まで全足跡
- 特定エラー: `grep "error_id=xxxxxxxx"` で例外＋親リクエスト特定
- パフォーマンス分析: `grep "analyze_success" | awk -F'elapsed_ms=' '{...}'`

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

## 獣医遺伝学知識

### [REF-001] プードル毛色用語の参考ソース
- <https://www.wisconsindesignerdoodles.com/coat-genetics-in-poodles>
- 主な定義:
  - `bb dd KB_ E_` = **Lilac/Isabella**（dilute brown）
  - `bb D_ KB_ E_ G_` = Café au lait / Silver Beige（born brown, fades）
  - `ee dd` = **Champagne**（dilute yellow）
  - `ay_ ky/ky` = **Fawn/Sable**（×レッド）
  - `at/at` = Black-and-Tan / Tricolor
  - `a/a` = Recessive Black（aa = solid black の劣性形）
  - `aw` = Wild Sable（4番目の A 座位アレル、現行コード未対応）
- 記事に G 座位（Greying）の記載は **無い** が、PCAで認知された色

### [PROCESS-001] PR バンドル発生問題
- **症状**: 開いているPRに対して新コミットを push すると、新コミットも
  自動でそのPRに含まれる（GitHub の挙動として正常）。但し PR description は
  古いままなのでレビュー時に内容と差分が一致しない問題が発生
- **発生例**: PR #37 (pyflakes のはずが bb ee 修正もバンドル), PR #41 (docstring
  + 新例犬)
- **対策**: 前のPRがマージされる前に次の作業を始める場合、必ず別ブランチを
  切るか、push を待つ。あるいは PR description を update してバンドル内容を
  明記する
- **将来検討**: 各PR ごとに別ブランチを使う運用への変更

### [BUG-009] A 座位の cross() 結果キーが lookup と不一致（修正済 PR #TBD）
- **症状**: `cross()` は alleles を `[a,b].sort().join('')` でキー化するため、
  ay/at ヘテロは "ayat" ではなく **"atay"** がキー（'at' < 'ay'）
- 旧コード: `aResult["ayat"]` → 常に 0 → ヘテロ確率が完全脱落
- ユーザー視点: 結果テーブルの確率合計が 100% にならない場合があった
- **修正**: A 座位 lookup を全て sorted form に統一
  - `aResult["ayat"]` → `aResult["atay"]`
  - aw/a 系も sorted form 使用 (away/aaw/aay/ataw/aat)
- **教訓**: cross() の結果キーは常に `[a,b].sort().join('')` 形式と認識すること

### [DESIGN-001] KITLG 拡張ポイント（T026 future-ready）
- `breeding_simulator.html` に `KITLG_SUPPORTED` boolean を追加（現在 false）
- `computeEePhenotypes(creamProb, pB_, pdd, pD_, pbb, sire, dam)` 関数に
  ee 表現型決定ロジックを抽出。intensity 対応時はこの関数内のみ修正
- `splitAlleles` に `II/Ii/ii` を**事前定義済み** → cross() で即動作
- 将来手順（4ステップ）:
  1. `KITLG_SUPPORTED = true`
  2. 両親フォームに `<select id="cs-i"/cd-i">` 追加
  3. 例犬 DOGS に `i:'II'` 等を追加（または Object.assign デフォルト `'II'`）
  4. computeEePhenotypes 内 TODO ブロックを有効化

### [REF-002] ee 表現型は「クリーム〜ホワイト」が基本
- `e/e` の coat 色は **本質的にクリーム〜ホワイト**
- アプリコット・レッド・ベージュ等は **KITLG (Intensity) 座位**が決定する
- KITLG は Orivet 12項目には**含まれていない** → 検査結果からは不明
- よってシミュレーターは KITLG 未対応の前提で「クリーム〜ホワイト」表記し、
  アプリコット/レッド判定には KITLG 検査が必要と注記
- 将来 T026 で KITLG 対応時に変更予定

### [BUG-008] cafe_au_lait の語彙ミス（修正済 PR #TBD）
- **症状**: `bb dd KB_ E_` をシミュレーターで「カフェオレ」表示していた
- **正しい用語**: 「ライラック/イザベラ」（dilute brown）
- 「カフェオレ」は本来 `bb` + Greying 遺伝子（成犬で退色する場合の名称）
- **修正**: 新色キー `lilac` を追加して bb dd gg をライラック表示に。
  cafe_au_lait はラベルを「カフェオレ（bb + Greying）」に明確化して残置


### [BUG-007] 繁殖シミュレーターの ee + B/D 分岐が誤り（修正済 PR #TBD）
- **症状**: `bb ee` がコート色「アプリコット」、`bb ee dd` が「カフェオレ」と表示されていた
- **遺伝学的事実**:
  - `e/e` の犬は coat に eumelanin（黒/茶色色素）を作れない
  - `B` 座（黒vs茶）は eumelanin の色を決める → ee コートには影響しない
  - `D` 座（希釈）も eumelanin に作用 → ee コートには影響しない
  - B/D が影響するのは **鼻・パッド・アイリム** の色素のみ
- **正しい色対応**:
  | 遺伝子型 | コート色 | Points (鼻/パッド) |
  |---|---|---|
  | `BB/Bb ee D_` | クリーム/アプリコット/レッド | 黒色素 |
  | `BB/Bb ee dd` | 同上 | 希釈黒（ブルー系） |
  | `bb ee D_` | 同上 | ブラウン（リバー） |
  | `bb ee dd` | 同上 | イザベラ（ライラック=希釈ブラウン） |
- **「カフェオレ」の正しい定義**: `E_ KB bb dd`（チョコ + 希釈）。`bb ee dd` で使うのは語彙ミス
- **修正**: 4ブランチすべて `color:"cream"` に統一し、注記で points 色素を区別
- **未対応**: Intensity 座（クリーム vs レッド の濃淡）はテストされていないため範囲表示

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
