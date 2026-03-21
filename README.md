# OriVet Genetic Analysis Suite

トイプードルブリーダー向けの遺伝子検査・血統分析統合ツールキットです。Orivet（Paw Print Genetics）の遺伝子検査レポートとJKC（ジャパンケネルクラブ）の血統書を解析し、繁殖判断に役立つ情報をまとめたレポートを生成します。

## 主な機能

- **遺伝子検査PDF解析** — Orivet遺伝子検査レポートPDFからデータを抽出し、健康リスクや形質を分類
- **血統書OCR解析** — JKC血統書の写真からTesseract OCRで3世代の血統情報を読み取り
- **近交係数（COI）計算** — Wrightの方法による近交係数の算出と共通祖先の特定
- **繁殖シミュレーター** — 毛色予測・健康リスク分析・COI計算を行うインタラクティブなWebツール
- **レポート生成** — HTML・Excelの両形式で見やすいレポートを出力

## ファイル構成

| ファイル | 説明 |
|---|---|
| `poodle_genetics.py` | 遺伝子検査＋血統分析の統合CLIツール |
| `orivet_analyzer.py` | Orivet遺伝子検査PDFの解析モジュール |
| `pedigree_ocr.py` | JKC血統書のOCR解析モジュール |
| `breeding_simulator.html` | ブラウザベースの繁殖シミュレーター |
| `orivet_report.html` | 遺伝子検査レポート（生成済みサンプル） |
| `orivet_genetic_report.html` | 遺伝子検査詳細レポート（生成済みサンプル） |
| `pedigree_report.html` | 血統・COIレポート（生成済みサンプル） |
| `poodle_report.html` | 統合レポート（生成済みサンプル） |

## 必要な環境

- Python 3.8以上
- Tesseract OCR（血統書解析を使用する場合）

### Pythonライブラリ

```
pip install pdfplumber openpyxl pytesseract Pillow
```

## 使い方

### 統合分析（遺伝子検査＋血統書）

```bash
python poodle_genetics.py all *.pdf --pedigree pedigree_photo.jpg
```

### 遺伝子検査PDFのみ

```bash
python poodle_genetics.py orivet *.pdf
```

### 血統書のみ

```bash
python poodle_genetics.py pedigree --pedigree pedigree_photo.jpg
```

### デモモード

```bash
python poodle_genetics.py demo
```

### 繁殖シミュレーター

`breeding_simulator.html` をブラウザで開くだけで使用できます（サーバー不要）。

- **毛色シミュレーション** — メンデル遺伝に基づく子犬の毛色予測
- **健康リスク分析** — 親犬の遺伝子型から子犬の疾患リスクを計算
- **COI計算** — 血統樹から近交係数を算出

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

## ライセンス

このプロジェクトのライセンスについてはリポジトリオーナーにお問い合わせください。
