# Orivet 遺伝子解析アプリケーション

[![pytest](https://github.com/kamide007-ship-it/orivetgenetic/actions/workflows/test.yml/badge.svg)](https://github.com/kamide007-ship-it/orivetgenetic/actions/workflows/test.yml)

全犬種対応の遺伝子検査・血統分析統合ツールキットです。Orivet（Paw Print Genetics）の遺伝子検査レポートとJKC（ジャパンケネルクラブ）の血統書を解析し、繁殖判断に役立つ情報をまとめたレポートを生成します。

## 主な機能

- **遺伝子検査PDF解析** — Orivet遺伝子検査レポートPDFからデータを抽出し、健康リスクや形質を分類
- **全14形質の日本語注釈** — A/B/D/E/EM/K/M/S/G座位 + Furnishings/Curly/L(被毛長)/SD(抜け毛)/BT(短尾) + メラニスティックマスクに、一般飼い主にも理解できる詳細解説を表示
- **血統書OCR解析** — JKC血統書の写真からTesseract OCRで3世代の血統情報を読み取り（写真向け前処理付き）
- **近交係数（COI）計算** — Wrightの方法による近交係数の算出と共通祖先の特定。「人間関係換算（兄妹婚相当・いとこ婚相当）」で結果を直感的に理解可能
- **繁殖シミュレーター** — 毛色予測・健康リスク分析・COI計算を行うインタラクティブなWebツール。全ての遺伝子座にヘルプモーダル、結果テーブルの遺伝子型表記がクリック可能
- **🆕 遺伝子疾患・形質辞書 (`/glossary`)** — 72疾患 + 14形質座位の詳細解説。カテゴリ別グルーピング、重症度フィルター（🔴高/🟡中/🟢低）、症状ベース検索（後肢麻痺・視覚障害・出血傾向等）、全文検索
- **🆕 重症度ベース可視化** — レポート・辞書の各疾患に重症度バッジを自動表示。サマリー行に🚨高リスク陽性カードを追加
- **レポート生成** — HTML・Excelの両形式で見やすいレポートを出力。各疾患・形質に📖折りたたみ詳細解説 + 参考リンク
- **モバイル完全対応** — iOS Safari の100dvh/bfcache/safe-area/自動ズーム対応、44x44タッチターゲット、モーダル全画面化

## ファイル構成

| ファイル | 説明 |
|---|---|
| `app.py` | Flask Webアプリ（Render対応） |
| `poodle_genetics.py` | 遺伝子検査＋血統分析の統合CLIツール |
| `orivet_analyzer.py` | Orivet遺伝子検査PDFの解析モジュール |
| `pedigree_ocr.py` | JKC血統書のOCR解析モジュール |
| `breeding_simulator.html` | ブラウザベースの繁殖シミュレーター |
| `templates/` | Webアプリ用HTMLテンプレート |
| `Dockerfile` | Docker ビルド設定（Tesseract OCR同梱） |
| `requirements.txt` | Python依存ライブラリ |
| `render.yaml` | Renderデプロイ設定 |

## 必要な環境

- Python 3.8以上
- Tesseract OCR + 日本語言語パック（血統書OCRを使用する場合）

### セットアップ

```bash
# Python依存ライブラリ
pip install -r requirements.txt

# Tesseract OCR（Ubuntu/Debian）
sudo apt install tesseract-ocr tesseract-ocr-jpn tesseract-ocr-eng

# Tesseract OCR（Mac）
brew install tesseract tesseract-lang
```

### 依存ライブラリ一覧

| パッケージ | 用途 |
|---|---|
| `flask` | Webアプリケーションフレームワーク |
| `gunicorn` | 本番用WSGIサーバー |
| `pdfplumber` | PDF テキスト抽出 |
| `openpyxl` | Excel レポート生成 |
| `pytesseract` | Tesseract OCR Python バインディング |
| `Pillow` | 画像処理（OCR前処理） |
| `pillow-heif` | HEIC/HEIF画像対応 |

## 使い方

### Webアプリ（推奨）

```bash
pip install -r requirements.txt
python app.py
```

ブラウザで `http://localhost:5000` を開き、PDFや血統書画像をアップロードして解析できます。

### CLI — 統合分析（遺伝子検査＋血統書）

```bash
python poodle_genetics.py all *.pdf --pedigree pedigree_photo.jpg
```

### CLI — 遺伝子検査PDFのみ

```bash
python poodle_genetics.py orivet *.pdf
```

### CLI — 血統書のみ

```bash
python poodle_genetics.py pedigree --pedigree pedigree_photo.jpg
```

### CLI — デモモード

```bash
python poodle_genetics.py demo
```

### 繁殖シミュレーター

`breeding_simulator.html` をブラウザで開くだけで使用できます（サーバー不要）。

- **毛色シミュレーション** — メンデル遺伝に基づく子犬の毛色予測（G座位対応でシルバー/シルバービーグ自動算出）
- **健康リスク分析** — 親犬の遺伝子型から子犬の疾患リスクを計算
- **COI計算** — 血統樹から近交係数を算出。**人間関係換算**で意味を即座に理解（25%=兄妹婚相当・6.25%=いとこ婚相当）
- **全ての遺伝子座にヘルプモーダル** — `?` ボタンで E/K/A/B/D/M/S/G 座位の詳細解説
- **結果テーブルがクリッカブル** — `E_`, `KB_`, `bb` 等の遺伝子型表記をクリックで該当座位の解説モーダル
- **健康疾患名がクリッカブル** — `/api/glossary` から KB を遅延ロードして詳細表示

### 🌐 多言語対応 (i18n)

辞書ページは**日本語と英語**に対応:

- `/glossary?lang=en` — 全 72 疾患 + 14 形質座位の英訳表示
- `/glossary/disease/<slug>?lang=en` — 疾患個別ページ英語
- `/glossary/trait/<slug>?lang=en` — 形質個別ページ英語
- 各ページ右上に **🌐 言語切替ボタン**
- `Accept-Language` ヘッダで自動判定（英語ブラウザでアクセスすると自動で英語表示）

英訳データは `kb_en.py` に集約（獣医監修対応のため分離）。

### 遺伝子疾患・形質辞書 (`/glossary`)

解析結果がなくても単独で利用可能な **72疾患 + 14形質座位** の総合辞書。

- **カテゴリ別表示（11カテゴリ）** — 🦴骨格 / 🧠神経 / 👁眼科 / 🩸血液 / 🧪代謝 / 💪筋運動 / 🫘腎泌尿 / 🧴皮膚 / 🛡免疫 / 🌱発達内分泌 / 🫃消化器 + 📑目次ナビ
- **重症度フィルター（🔴高/🟡中/🟢低）** — 自動推定 + 個別補正済の3段階分類 + 凡例付き
- **症状ベース検索（10カテゴリ）** — 「後肢麻痺」「視覚障害」「出血傾向」等から関連疾患を逆引き
- **全文検索 (`?q=`)** — 疾患名・遺伝子・症状などで部分文字列マッチ
- **JSON API (`/api/glossary`)** — DISEASE_KB / TRAIT_KB を JSON 取得可能（クライアント連携用）

各疾患エントリは: 📋 概要 / 🧬 メカニズム / ⚠️ 症状 / 🧪 遺伝様式 / 💡 アドバイス / 🔗 参考リンク

カバー範囲: Veqta / Orivet / Embark / Paw Print Genetics の標準パネルに準拠。

### 📚 ガイド記事 (`/guides`)

初心者から専門家まで利用可能なガイド記事:

**基礎ガイド**:
- Orivet 検査結果の読み方
- COI（近親交配係数）入門
- 犬の毛色遺伝子の基本（8座位）
- ブリーダー繁殖計画チェックリスト
- 重症度（🔴🟡🟢）判定基準

**犬種別ガイド** (PR #62):
- 🐩 プードル（スタンダード/ミニチュア/トイ）
- 🐕 ラブラドール・レトリーバー
- 🐾 ドゥードゥル系（Goldendoodle/Labradoodle/Cavapoo 等）
- 🐕 柴犬（Orivet JP 対応）
- 🐕 秋田犬（同）
- 🐕 シャー・ペイ（同）
- 🐕 狆（同）
- 🐕 ダックスフンド
- 🐕 フレンチブルドッグ
- 🐕 キャバリア K.C. スパニエル
- 🐕 ボーダーコリー
- 🐕 ジャーマンシェパード
- 🐕 ミニチュアシュナウザー

## 対応している形質検査（14項目）

| 検査項目 | 遺伝子座 | 注釈例 |
|---|---|---|
| A座位（アグーチ） | A Locus | セーブル/ファントム等の模様パターン |
| B座位（ブラウン） | B Locus | ブラウン/チョコレートの毛色 |
| D座位（ダイリュート） | D Locus | ブルー/カフェオレへの希釈 |
| E座位（エクステンション） | E Locus | クリーム/ホワイト/アプリコット |
| EM座位（マスク） | EM (MC1R) | 顔のメラニスティックマスク |
| K座位（ドミナントブラック） | K Locus | 単色/ブリンドル/アグーチ発現 |
| M座位（マール） | M Locus | マール模様・ダブルマールリスク |
| パイド | Pied (S Locus) | パーティカラー/白斑 |
| ファーニシング | RSPO2 | 眉毛・ヒゲ・飾り毛の有無 |
| 巻き毛 | Curly Coat | カーリー/ウェーブ/ストレート |
| 軟骨異形成症 | CDPA | 短足因子 |
| ブラウン TYRP1 | Brown TYRP1 | TYRP1によるブラウン/レバー |

## 血統書OCRの対応フォーマット

| 団体 | 対応状況 |
|---|---|
| JKC（ジャパンケネルクラブ） | 番号ベース＋ラベルベースの二重パース |
| AKC（アメリカンケネルクラブ） | ラベルベースパース |
| ALAJ（オーストラリアンラブラドゥードル協会） | ラベルベースパース |
| KC（ザ・ケネルクラブ） | ラベルベースパース |
| その他 | 汎用パーサー（SIRE/DAM形式） |

### OCR前処理

写真からの読み取り精度を上げるため、以下の前処理を自動で行います：

1. 大きすぎる画像のリサイズ（4000px上限）
2. グレースケール変換
3. コントラスト強化（1.8倍）+ シャープネス強化（2.0倍）
4. 二値化（平均値ベースの閾値）
5. 複数のTesseract設定（PSM 6/3）で試行し最良結果を採用

## 出力ファイル

| ファイル | 内容 |
|---|---|
| `orivet_report.html` / `.xlsx` | 遺伝子検査結果レポート |
| `pedigree_report.html` | 血統・COI分析レポート |
| `poodle_report.html` / `.xlsx` | 統合レポート |

## COI（近交係数）の目安

| COI | リスク |
|---|---|
| < 6.25% | 低（緑） |
| 6.25% 〜 12.5% | 中（黄） |
| > 12.5% | 高（赤） |

## セキュリティ

- HTMLレポート出力時のXSSエスケープ（全ユーザー入力を `_h()` でサニタイズ）
- `SECRET_KEY` の動的生成（ハードコードなし）
- ファイルアップロードの `secure_filename()` によるサニタイズ
- パストラバーサル対策（セッションID・ファイル名の検証）
- PDF/OCR処理の例外ハンドリング（壊れたファイルでクラッシュしない）
- セッションIDにフルUUID（128bit）を使用

## Render へのデプロイ

### 1. Render にサインアップ

[Render](https://render.com) でアカウントを作成し、GitHubリポジトリを連携します。

### 2. Web Service を作成

Dockerfileが含まれているため、Renderは自動的にDockerランタイムを検出します。

| 設定項目 | 値 |
|---|---|
| **Environment** | Docker（自動検出） |

### 3. 環境変数

| 環境変数 | 必須 | デフォルト | 説明 |
|---|---|---|---|
| `SECRET_KEY` | 推奨 | 起動時に自動生成（再起動でセッション無効化） | Flaskセッション用の秘密鍵。Renderの「Generate」ボタンで自動生成 |
| `REPORT_TTL_HOURS` | 任意 | 24 | レポート・アップロードファイルの自動削除TTL（時間）。ディスク枯渇防止のため起動時に古いセッションを掃除 |
| `PORT` | 任意 | 5000 | Flask開発サーバーのポート（Renderでは10000、Dockerfile側で指定済） |

> `render.yaml` が含まれているため、「Blueprint」からデプロイすると上記設定が自動的に適用されます。

### 4. ヘルスチェック

軽量なヘルスチェックエンドポイントを提供しています（Render等の死活監視向け）:

```
GET /healthz
→ 200 OK
  {"status": "ok", "pdfplumber": true, "ocr": true}
```

テンプレート描画やDBアクセスは行わないため、コールドスタート時もミリ秒単位で応答します。

### 5. サポート対応（エラー特定）

ユーザーから「PDF解析失敗」「OCR失敗」「レポート生成失敗」などの問い合わせを受けた場合、エラーメッセージに `error_id=xxxxxxxx`（8桁hex）が含まれています。

Render Logs（または `docker logs`）で以下を検索すると該当の例外スタックトレースが特定できます:

```bash
grep "error_id=xxxxxxxx" <log_file>
```

ログには `stage`（処理段階）・`file`（対象ファイル名）・`exc_type`（例外型）が構造化記録されます。

### 4. デプロイ

GitHubにプッシュすると自動デプロイされます。または Render ダッシュボードから手動デプロイも可能です。

Dockerイメージに Tesseract OCR（日本語・英語）が含まれているため、**血統書OCR機能もRender上で利用可能**です。

## ライセンス

このプロジェクトのライセンスについてはリポジトリオーナーにお問い合わせください。
