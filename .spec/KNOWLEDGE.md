# KNOWLEDGE.md — ドメイン知識・技術知識の蓄積

## Orivet PDF フォーマット

### 判別条件
- `"Genetic Summary Report"` または `"Health Tests Reported"` のいずれかが含まれる
- DNAプロファイル（DNAP）: `"ISAG Profile"` か `"DNA Profile"` が含まれ、
  かつ `"Health Tests Reported"` が含まれない → スキップ

### データ構造
- 健康検査結果: `parse_health_tests()` でリスト形式に抽出
- 形質結果: `parse_trait_results_from_text()` で抽出
- 遺伝子座: A/B/D/E/EM/K/M/Pied/Furnishings/Curly/CDPA/BrownTYRP1

---

## 血統書フォーマット

### フォーマット判別（優先順位）
1. JKC: `JKC-PT` / `ジャパンケネルクラブ` / `JAPAN KENNEL CLUB`
2. ALAJ: `ALAJ` / `Australian Labradoodle` / `ラブラドゥードル`
3. AKC: `AKC` / `AMERICAN KENNEL CLUB`
4. KC: `KC\b` / `THE KENNEL CLUB`
5. generic: `SIRE` / `DAM` / `PEDIGREE` など

### OCR 誤認識辞書（`pedigree_ocr._clean_ocr_text`）
```
KENNE1 → KENNEL
C1UB → CLUB
J@PAN → JAPAN
P00DLE → POODLE
S1RE → SIRE
```
→ 新たな誤認識パターンを発見したらここに追記

---

## COI（近交係数）計算

### Wright 経路公式
```
COI = Σ [ 0.5 ^ (n + m + 1) ]
```
- n: 個体 → 共通祖先 → sire 側の経路長
- m: 個体 → 共通祖先 → dam 側の経路長
- 共通祖先自身に近交がある場合: `(1 + F_A)` 倍（現在は未実装）

### 実装上の注意
- 名前正規化: `re.sub(r'\s+', ' ', name.strip().upper())`（スペース揺れ吸収）
- `calc_coi_3gen`: 単一血統書から当該個体の COI を計算（3世代上限）
- `calc_coi_cross`: 2頭の血統書から交配子犬の予測 COI を計算

### COI 目安
| COI | リスク | 色 |
|---|---|---|
| < 6.25% | 低 | 緑 |
| 6.25〜12.5% | 中 | 黄 |
| > 12.5% | 高 | 赤 |

---

## 遺伝子型マッピング（シミュレーター連携）

`app.py:_TRAIT_TO_SIM_KEY` に定義。追加した形質はここも更新が必要。

```python
"E Locus" → "e"
"K Locus" → "k"
"A Locus" → "a"
# etc.
```

---

## Render デプロイ

- ランタイム: Docker（Dockerfile に Tesseract + jpn パック同梱）
- 起動コマンド: `gunicorn app:app --timeout 300 --workers 2`
- ポート: 10000
- 環境変数: `SECRET_KEY`（必須・generateValue で自動生成）
- `REPORT_TTL_HOURS`（任意・デフォルト 24h）
