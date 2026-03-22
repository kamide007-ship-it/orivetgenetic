# Orivet 遺伝子解析アプリケーション

全犬種対応の遺伝子検査・血統分析統合ツールキットです。Orivet（Paw Print Genetics）の遺伝子検査レポートとJKC（ジャパンケネルクラブ）の血統書を解析し、繁殖判断に役立つ情報をまとめたレポートを生成します。

## 主な機能

- **遺伝子検査PDF解析** — Orivet遺伝子検査レポートPDFからデータを抽出し、健康リスクや形質を分類
- **全12形質の日本語注釈** — A/B/D/E/EM/K/M座位、パイド、ファーニシング、巻き毛、CDPA、ブラウンTYRP1の遺伝子型に素人でも分かる解説を表示
- **血統書OCR解析** — JKC血統書の写真からTesseract OCRで3世代の血統情報を読み取り（写真向け前処理付き）
- **近交係数（COI）計算** — Wrightの方法による近交係数の算出と共通祖先の特定
- **繁殖シミュレーター** — 毛色予測・健康リスク分析・COI計算を行うインタラクティブなWebツール
- **レポート生成** — HTML・Excelの両形式で見やすいレポートを出力

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

- **毛色シミュレーション** — メンデル遺伝に基づく子犬の毛色予測
- **健康リスク分析** — 親犬の遺伝子型から子犬の疾患リスクを計算
- **COI計算** — 血統樹から近交係数を算出

## 対応している形質検査（12項目）

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

| 環境変数 | 説明 | 設定方法 |
|---|---|---|
| `SECRET_KEY` | Flaskセッション用の秘密鍵 | Renderの「Generate」ボタンで自動生成 |

> `render.yaml` が含まれているため、「Blueprint」からデプロイすると上記設定が自動的に適用されます。

### 4. デプロイ

GitHubにプッシュすると自動デプロイされます。または Render ダッシュボードから手動デプロイも可能です。

Dockerイメージに Tesseract OCR（日本語・英語）が含まれているため、**血統書OCR機能もRender上で利用可能**です。

## ライセンス

このプロジェクトのライセンスについてはリポジトリオーナーにお問い合わせください。
