#!/usr/bin/env python3
"""
Orivet 遺伝子解析ツール — 全犬種対応
=====================================================
Orivet遺伝子検査PDFの自動解析 + JKC血統書OCR + COI算出を
1本にまとめた統合ツール。全犬種のOrivetレポートに対応。

コマンド:
    # 遺伝子検査PDFだけ解析
    python poodle_genetics.py orivet *.pdf

    # 血統書写真だけ解析
    python poodle_genetics.py pedigree photo.jpg

    # 両方まとめて統合レポート
    python poodle_genetics.py all *.pdf --pedigree seven

    # 既知データでデモ
    python poodle_genetics.py demo

出力:
    - orivet_report.html  (統合HTMLレポート: 遺伝子 + 血統 + COI)
    - orivet_report.xlsx  (Excelスプレッドシート)

必要ライブラリ:
    pip install pdfplumber openpyxl
    # 血統書OCRを使う場合:
    pip install pytesseract Pillow
    # + Tesseract OCR本体
"""

import sys
import os
import re
import glob
import json
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime

# ============================================================
# ライブラリ読み込み
# ============================================================

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass


# ============================================================
# データ構造
# ============================================================

@dataclass
class TestResult:
    """個別の検査結果"""
    category: str
    test_name: str
    genotype: str
    result_text: str
    status: str          # normal / carrier / positive / trait
    japanese_name: str = ""

@dataclass
class DogProfile:
    """犬1頭分の遺伝子検査プロファイル"""
    pet_name: str = ""
    registered_name: str = ""
    breed: str = ""
    sex: str = ""
    dob: str = ""
    colour: str = ""
    microchip: str = ""
    case_number: str = ""
    owner_name: str = ""
    test_date: str = ""
    test_requested: str = ""
    approved_collection: str = ""
    sample_type: str = ""
    health_results: list = field(default_factory=list)
    trait_results: list = field(default_factory=list)
    source_file: str = ""

@dataclass
class Ancestor:
    """血統書上の1頭分"""
    position: str = ""
    name: str = ""
    registration: str = ""
    titles: str = ""
    color: str = ""
    dna_number: str = ""
    microchip: str = ""
    dob: str = ""

@dataclass
class Pedigree:
    """1頭分の完全な血統書データ"""
    dog_name: str = ""
    breed: str = ""
    registration: str = ""
    sex: str = ""
    dob: str = ""
    color: str = ""
    microchip: str = ""
    breeder: str = ""
    owner: str = ""
    sire: Optional[Ancestor] = None
    dam: Optional[Ancestor] = None
    ss: Optional[Ancestor] = None
    sd: Optional[Ancestor] = None
    ds: Optional[Ancestor] = None
    dd: Optional[Ancestor] = None
    sss: Optional[Ancestor] = None
    ssd: Optional[Ancestor] = None
    sds: Optional[Ancestor] = None
    sdd: Optional[Ancestor] = None
    dss: Optional[Ancestor] = None
    dsd: Optional[Ancestor] = None
    dds: Optional[Ancestor] = None
    ddd: Optional[Ancestor] = None
    source_file: str = ""

    def all_ancestors(self):
        """全祖先のリストを返す"""
        return [
            ("父 (Sire)", self.sire),
            ("母 (Dam)", self.dam),
            ("父方祖父 (G.Sire)", self.ss),
            ("父方祖母 (G.Dam)", self.sd),
            ("母方祖父 (G.Sire)", self.ds),
            ("母方祖母 (G.Dam)", self.dd),
            ("父方曾祖父1 (GG.Sire)", self.sss),
            ("父方曾祖母1 (GG.Dam)", self.ssd),
            ("父方曾祖父2 (GG.Sire)", self.sds),
            ("父方曾祖母2 (GG.Dam)", self.sdd),
            ("母方曾祖父1 (GG.Sire)", self.dss),
            ("母方曾祖母1 (GG.Dam)", self.dsd),
            ("母方曾祖父2 (GG.Sire)", self.dds),
            ("母方曾祖母2 (GG.Dam)", self.ddd),
        ]


# ============================================================
# 日本語マッピング
# ============================================================

CATEGORY_JP = {
    "musculoskeletal": "筋骨格系",
    "haemolymphatic": "血液・リンパ系",
    "nervous": "神経系",
    "neurologic": "神経系",
    "metabolic": "代謝系",
    "ophthalmologic": "眼科系",
    "cardiorespiratory": "心肺系",
    "cardiovascular": "心血管系",
    "dermatologic": "皮膚科系",
    "immunological": "免疫系",
    "respiratory": "呼吸器系",
    "urogenital": "泌尿生殖器系",
    "trait": "形質（毛色・外見）",
}

TEST_NAME_JP = {
    "chondrodystrophy with intervertebral disc disease": "軟骨異栄養症+椎間板疾患リスク (CDDY+IVDD)",
    "cddy with ivdd": "軟骨異栄養症+椎間板疾患リスク (CDDY+IVDD)",
    "osteochondrodysplasia": "骨軟骨異形成症",
    "chondrodysplasia": "軟骨異形成症 (CDPA)",
    "cdpa": "軟骨異形成症 (CDPA)",
    "congenital macrothrombocytopenia": "先天性巨大血小板減少症",
    "congenital methemoglobinemia": "先天性メトヘモグロビン血症",
    "von willebrand": "フォンウィルブランド病 I型",
    "degenerative myelopathy": "変性性脊髄症 (DM)",
    "gangliosidosis gm2": "ガングリオシドーシス GM2",
    "progressive rod cone degeneration": "進行性網膜萎縮症 (prcd-PRA)",
    "prcd": "進行性網膜萎縮症 (prcd-PRA)",
    "progressive retinal atrophy": "進行性網膜萎縮症 (PRA)",
    "exercise-induced collapse": "運動誘発性虚脱 (EIC)",
    "neonatal encephalopathy": "新生児脳症",
    "hyperuricosuria": "高尿酸尿症",
    "cystinuria": "シスチン尿症",
    "a locus": "A座位 (アグーチ)",
    "b locus": "B座位 (ブラウン)",
    "d locus": "D座位 (ダイリュート)",
    "dilute": "D座位 (ダイリュート)",
    "e locus": "E座位 (エクステンション)",
    "em locus": "EM座位 (メラニスティックマスク)",
    "mc1r": "EM座位 (メラニスティックマスク)",
    "k locus": "K座位 (ドミナントブラック)",
    "m locus": "M座位 (マール/ダップル)",
    "merle": "M座位 (マール/ダップル)",
    "curly coat": "巻き毛 (Curly Coat)",
    "furnishings": "ファーニシング (RSPO2)",
    "rspo2": "ファーニシング (RSPO2)",
    "pied": "パイド (Pied)",
    "brown tyrp1": "ブラウン TYRP1",
    "improper coat": "インプロパーコート",
    "coat length": "毛の長さ",
    "shedding": "換毛",
}


# ============================================================
# 毛色・形質 遺伝子型の日本語注釈
# ============================================================

def get_trait_annotation(test_name: str, genotype: str) -> str:
    """検査項目と遺伝子型から、分かりやすい日本語の注釈を返す"""
    if not genotype or genotype == "—":
        return ""

    name_lower = test_name.lower()

    # E Locus (エクステンション / クリーム)
    if "e locus" in name_lower:
        return {
            "E/E": "クリーム因子なし。ブラック/ブラウン等の濃い毛色",
            "E/e": "クリーム因子を1つ保有（キャリア）。見た目は濃い色だが、子犬にクリーム/ホワイトが出る可能性あり",
            "e/e": "クリーム因子を2つ保有。クリーム/ホワイト/アプリコット/レッドの毛色になる",
        }.get(genotype, "")

    # K Locus (ドミナントブラック)
    if "k locus" in name_lower:
        mapping = {
            "KB/KB": "ドミナントブラックを2つ保有。全身が単色（ブラックまたはブラウン）",
            "K/K": "ドミナントブラックを2つ保有。全身が単色（ブラックまたはブラウン）",
            "KB/ky": "ドミナントブラック1つ保有。見た目は単色だが、ファントム/タンポイントの子が出る可能性あり",
            "KB/kbr": "ドミナントブラック1つ + ブリンドル1つ保有。見た目は単色",
            "ky/ky": "ドミナントブラックなし。アグーチ座位の模様（ファントム/セーブル等）が発現する",
            "kbr/ky": "ブリンドル因子あり。ブリンドル模様が出る可能性あり",
            "kbr/kbr": "ブリンドル因子を2つ保有。ブリンドル模様が発現する",
        }
        return mapping.get(genotype, "")

    # A Locus (アグーチ)
    if "a locus" in name_lower:
        return {
            "ay/ay": "セーブル（毛先が黒い明るい毛色）。ky/kyの場合に発現する",
            "ay/at": "セーブルだが、ファントム/タンポイントの子が出る可能性あり",
            "ay/aw": "セーブルとワイルドタイプのアグーチ。ky/kyの場合に発現する",
            "at/at": "ファントム/タンポイント（目の上・足先等に明るい斑点）。ky/kyの場合に発現する",
            "aw/at": "ワイルドタイプアグーチだが、ファントム/タンポイントの子が出る可能性あり",
            "aw/aw": "ワイルドタイプアグーチ。ウルフセーブル等の毛色パターン",
            "a/a": "リセッシブブラック。アグーチ模様なし",
        }.get(genotype, "A座位（アグーチ）: 毛色の模様パターンを決定する遺伝子座。K座位がky/kyの場合に模様が発現する")

    # B Locus (ブラウン)
    if "b locus" in name_lower:
        return {
            "BB": "ブラウン因子なし。鼻・肉球はブラック",
            "Bb": "ブラウン因子を1つ保有（キャリア）。見た目はブラックだが、ブラウンの子が出る可能性あり",
            "bb": "ブラウン因子を2つ保有。ブラウン（チョコレート）の毛色。鼻・肉球もブラウン",
        }.get(genotype, "B座位（ブラウン）: ブラウン/チョコレート/レバーの毛色を決定する遺伝子座")

    # D Locus (ダイリュート / 希釈)
    if "d locus" in name_lower or "dilute" in name_lower:
        return {
            "D/D": "希釈因子なし。色素は通常通り発現する",
            "D/d": "希釈因子を1つ保有（キャリア）。見た目は通常色だが、希釈色の子が出る可能性あり",
            "d/d": "希釈因子を2つ保有。ブラック→ブルー、ブラウン→カフェオレに希釈される",
        }.get(genotype, "")

    # M Locus (マール)
    if "m locus" in name_lower or "merle" in name_lower:
        return {
            "m/m": "マール因子なし。単色（ソリッドカラー）",
            "M/m": "マール因子を1つ保有。マール模様（まだら）が出る可能性あり",
            "M/M": "マール因子を2つ保有（ダブルマール）。健康リスク（聴覚・視覚障害）あり",
        }.get(genotype, "")

    # S Locus (パイド / 白斑)
    if "pied" in name_lower:
        return {
            "S/S": "パイド因子なし。白斑模様は出ない",
            "S/sp": "パイド因子を1つ保有（キャリア）。わずかな白斑が出ることがある",
            "sp/sp": "パイド因子を2つ保有。パーティカラー（大きな白斑模様）になる",
        }.get(genotype, "")

    # EM Locus (メラニスティックマスク)
    if "em" in name_lower or "mc1r" in name_lower or "melanistic mask" in name_lower:
        return {
            "En/En": "マスク因子なし。顔にメラニスティックマスクは出ない",
            "EM/EM": "マスク因子を2つ保有。顔周りに黒いマスク模様が出る",
            "EM/En": "マスク因子を1つ保有。マスク模様が出る可能性あり",
        }.get(genotype, "")

    # Furnishings (RSPO2)
    if "furnishings" in name_lower or "rspo2" in name_lower:
        return {
            "F/F": "ファーニシング因子を2つ保有。眉毛・ヒゲ・足の飾り毛あり（プードル・シュナウザー等の特徴的な外見）",
            "F/f": "ファーニシング因子を1つ保有。ファーニシングあり。抜け毛のある子が出る可能性",
            "f/f": "ファーニシング因子なし。ファーニシングなし（スムースフェイス）。抜け毛が多い傾向",
        }.get(genotype, "")

    # Curly Coat
    if "curly coat" in name_lower:
        return {
            "Cu/Cu": "巻き毛因子を2つ保有。しっかりとしたカーリーコート",
            "Cu/N": "巻き毛因子を1つ保有。ウェーブがかった被毛",
            "N/N": "巻き毛因子なし。ストレートな被毛",
        }.get(genotype, "")

    # Brown TYRP1
    if "brown tyrp1" in name_lower:
        return {
            "BL/BL": "TYRP1ブラウン因子なし。ブラウン/レバーにならない",
            "BL/bs": "TYRP1ブラウン因子を1つ保有（キャリア）",
            "bs/bs": "TYRP1ブラウン因子を2つ保有。ブラウン/レバーの毛色に影響する可能性",
        }.get(genotype, "")

    # CDPA (形質として出ることもある)
    if "chondrodysplasia" in name_lower or "cdpa" in name_lower:
        return {
            "N/N": "正常。短足因子(CDPA)なし",
            "P/N": "キャリア。短足因子を1つ保有",
            "P/P": "短足因子を2つ保有。脚が短くなる可能性",
        }.get(genotype, "")

    return ""


# ============================================================
# 健康検査 遺伝子型の日本語注釈
# ============================================================

def get_health_annotation(test_name: str, genotype: str, status: str) -> str:
    """健康検査項目と遺伝子型から、分かりやすい日本語の注釈を返す"""
    if not genotype:
        return ""

    name_lower = test_name.lower()

    # CDDY+IVDD (軟骨異栄養症+椎間板疾患)
    if "chondrodystrophy" in name_lower or "cddy" in name_lower or "ivdd" in name_lower:
        return {
            "N/N": "正常。椎間板疾患(IVDD)のリスクは一般レベル",
            "P/N": "キャリア（保因犬）。CDDY因子を1つ保有。椎間板ヘルニアのリスクがやや高い。繁殖相手の選定に注意が必要",
            "P/P": "発症リスクあり。CDDY因子を2つ保有。椎間板ヘルニアのリスクが高い。体重管理や激しい運動の制限を推奨",
        }.get(genotype, "")

    # 骨軟骨異形成症
    if "osteochondrodysplasia" in name_lower:
        return {
            "N/N": "正常。骨軟骨異形成症の変異なし",
            "P/N": "キャリア（保因犬）。繁殖時にキャリア同士の交配を避けること",
            "P/P": "発症リスクあり。骨・軟骨の異常な発達が起こる可能性。獣医師への相談を推奨",
        }.get(genotype, "")

    # 先天性巨大血小板減少症
    if "macrothrombocytopenia" in name_lower:
        return {
            "N/N": "正常。血小板に関する遺伝的異常なし",
            "P/N": "キャリア（保因犬）。血小板が大きく数が少ない場合がある。臨床的問題は通常なし",
            "P/P": "発症リスクあり。血小板が著しく大きく数が減少。出血傾向に注意",
        }.get(genotype, "")

    # 先天性メトヘモグロビン血症
    if "methemoglobinemia" in name_lower:
        return {
            "N/N": "正常。メトヘモグロビン血症の変異なし",
            "P/N": "キャリア（保因犬）。繁殖時にキャリア同士の交配を避けること",
            "P/P": "発症リスクあり。チアノーゼ（皮膚や粘膜の青紫変色）が見られる可能性。獣医師への相談を推奨",
        }.get(genotype, "")

    # フォンウィルブランド病 I型
    if "von willebrand" in name_lower:
        return {
            "N/N": "正常。出血性疾患のリスクなし",
            "P/N": "キャリア（保因犬）。通常は臨床症状なし。繁殖時にキャリア同士の交配を避けること",
            "P/P": "発症リスクあり。出血が止まりにくい傾向。手術前に獣医師に申告すること",
        }.get(genotype, "")

    # 変性性脊髄症 (DM)
    if "degenerative myelopathy" in name_lower:
        return {
            "N/N": "正常。変性性脊髄症のリスクなし",
            "P/N": "キャリア（保因犬）。通常は発症しない。繁殖時にキャリア同士の交配を避けること",
            "P/P": "発症リスクあり。高齢期に後肢の麻痺が進行する可能性。定期的な神経学的検査を推奨",
        }.get(genotype, "")

    # ガングリオシドーシス GM2
    if "gangliosidosis" in name_lower:
        return {
            "N/N": "正常。ガングリオシドーシスの変異なし",
            "P/N": "キャリア（保因犬）。繁殖時にキャリア同士の交配を避けること",
            "P/P": "発症リスクあり。神経系の進行性疾患。早期の獣医師への相談を推奨",
        }.get(genotype, "")

    # 進行性網膜萎縮症 (prcd-PRA)
    if "progressive rod cone" in name_lower or "prcd" in name_lower or "progressive retinal atrophy" in name_lower:
        return {
            "N/N": "正常。prcd-PRAによる失明リスクなし",
            "P/N": "キャリア（保因犬）。視力への影響なし。繁殖時にキャリア同士の交配を避けること",
            "P/P": "発症リスクあり。進行性の視力低下・失明の可能性。定期的な眼科検査を推奨",
        }.get(genotype, "")

    # 運動誘発性虚脱 (EIC)
    if "exercise-induced collapse" in name_lower or "eic" in name_lower:
        return {
            "N/N": "正常。運動誘発性虚脱のリスクなし",
            "P/N": "キャリア（保因犬）。通常は発症しない。繁殖時にキャリア同士の交配を避けること",
            "P/P": "発症リスクあり。激しい運動後に一過性の虚脱が起こる可能性。運動の強度に注意",
        }.get(genotype, "")

    # 新生児脳症
    if "neonatal encephalopathy" in name_lower:
        return {
            "N/N": "正常。新生児脳症の変異なし",
            "P/N": "キャリア（保因犬）。繁殖時にキャリア同士の交配を避けること",
            "P/P": "発症リスクあり。新生児期に神経症状が出る可能性",
        }.get(genotype, "")

    # 汎用的な注釈（上記に該当しない場合）
    if status == "normal":
        return "正常。この疾患に関連する遺伝子変異は検出されませんでした"
    elif status == "carrier":
        return "キャリア（保因犬）。変異を1つ保有。通常は発症しないが、繁殖相手の選定に注意が必要"
    elif status == "positive":
        return "発症リスクあり。変異を2つ保有。獣医師への相談を推奨"

    return ""


# ============================================================
# PDF解析時の不正データフィルター
# ============================================================

# PDFからの誤抽出を除外するための除外キーワード
HEALTH_TEST_BLACKLIST = [
    "glossary of genetic terms",
    "pass on any disease-causing mutation",
    "unknown then it may produce",
    "affected offspring",
    "genetic terms",
    "copyright",
    "disclaimer",
    "page ",
]


def is_valid_health_test(test_name: str) -> bool:
    """有効な健康検査項目かどうかを判定（PDFの文字化けやゴミデータを除外）"""
    if not test_name or len(test_name) < 3:
        return False
    name_lower = test_name.lower()
    for blacklisted in HEALTH_TEST_BLACKLIST:
        if blacklisted in name_lower:
            return False
    # 文字化けチェック: 制御文字や置換文字が含まれている場合
    if re.search(r'[\ufffd\x00-\x08\x0b\x0c\x0e-\x1f]', test_name):
        return False
    return True


# ============================================================
# 既知の血統書データ
# ============================================================

KNOWN_PEDIGREES = {
    "seven": Pedigree(
        dog_name="SMASH JP SEVEN NIGHT",
        breed="POODLE (トイプードル)",
        registration="JKC-PT -32565/25",
        sex="MALE",
        dob="2025年4月14日",
        color="BLACK",
        microchip="392149002585861",
        breeder="TOSHINORI OMURA, FUJISHI",
        owner="KENTARO KAMIDE, MINAMISOMASHI",
        sire=Ancestor(position="sire", name="SMASH JP NIGHT DANCER",
                       registration="JKC-PT -41545/23", titles="CH/24.11, J.CH",
                       color="BLK", dna_number="JP006738/24", microchip="392144000844198",
                       dob="2023年4月30日"),
        dam=Ancestor(position="dam", name="SMASH JP NEZUKO",
                      registration="JKC-PT -70721/20", titles="",
                      color="WH", dna_number="JP003236/24",
                      dob="2020年10月27日"),
        ss=Ancestor(position="ss", name="SMASH JP HIKARU",
                     registration="JKC-PT -30198/22", titles="CH/23.6, C1B-J, J.CH, CH(PH1), WJW22, AAO.CH",
                     color="BLK", dna_number="JP004083/23", microchip="392144000441530"),
        sd=Ancestor(position="sd", name="SMASH JP JEG VIL AT VI",
                     registration="JKC-PT -70711/20", titles="CH/21.11",
                     color="BLK", dna_number="JP007839/21", microchip="392144000312770"),
        ds=Ancestor(position="ds", name="SMASH JP PERFECT HUMAN",
                     registration="JKC-PT -33197/18", titles="CH/17.4",
                     color="WH", dna_number="JP002506/17", microchip="392148014113831"),
        dd=Ancestor(position="dd", name="SMASH JP TOGENYAN",
                     registration="JKC-PT -12866/15", titles="CH/18.7",
                     color="WH", dna_number="JP004270/16"),
        sss=Ancestor(position="sss", name="SMASH JP BLINDING LIGHTS",
                      registration="JKC-PT -47888/20", titles="CH/21.5",
                      color="BLK", dna_number="JP003001/21", microchip="392144000310643"),
        ssd=Ancestor(position="ssd", name="SMASH JP TIK TOK",
                      registration="JKC-PT -42345/18", titles="INT.CH, CH/19.5, GCH(PH1), AAO.CH, SEA.CH",
                      color="BLK", dna_number="JP002875/18", microchip="392144000158862"),
        sds=Ancestor(position="sds", name="SMASH JP ONE OF US",
                      registration="JKC-PT -00866/19", titles="C.I.B., CH/19.11",
                      color="BR", dna_number="JP007567/19", microchip="392145000477714"),
        sdd=Ancestor(position="sdd", name="SMASH JP LONDON WIND",
                      registration="JKC-PT -15146/18", titles="",
                      color="BLK", microchip="392144000313005"),
        dss=Ancestor(position="dss", name="SMASH JP MOON WALK",
                      registration="JKC-PT -67987/06", titles="INT.CH, CH/07.11, CH(AM, SWE, CRO), G.CH(AM), WW11",
                      color="WH", dna_number="JP013774/07", microchip="392143000042098"),
        dsd=Ancestor(position="dsd", name="SMASH JP CINDERELA",
                      registration="JKC-PT -37596/14", titles="CH/15.5",
                      color="WH", dna_number="JP003076/15", microchip="392141000628131"),
        dds=Ancestor(position="dds", name="SMASH JP BLIZARD",
                      registration="JKC-PT -02878/13", titles="CH/14.1",
                      color="WH", dna_number="JP000541/14", microchip="392141000595003"),
        ddd=Ancestor(position="ddd", name="SMASH JP THE POWER OF DREAMS",
                      registration="JKC-PT -21576/11", titles="CH/12.1",
                      color="WH", dna_number="JP000419/12"),
    ),
}


# ████████████████████████████████████████████████████████████
# PART 1: Orivet PDF 解析エンジン
# ████████████████████████████████████████████████████████████

def extract_all_text(pdf_path: str) -> str:
    """PDFから全ページのテキストを抽出"""
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
    return "\n\n".join(texts)


def parse_animal_details(text: str) -> dict:
    """動物の基本情報を抽出"""
    info = {}
    patterns = {
        "registered_name": r"Registered\s+Name\s*:?\s*(.+?)(?:\n|$)",
        "pet_name": r"Pet\s+Name\s*:?\s*(.+?)(?:\n|$)",
        "breed": r"Breed\s*:?\s*:?\s*(.+?)(?:\n|$)",
        "microchip": r"Microchip\s+Number\s*:?\s*(\d[\d\s]*\d)",
        "sex": r"Sex\s*:?\s*:?\s*(.+?)(?:\n|$)",
        "dob": r"Date\s+of\s+Birth\s*:?\s*(.+?)(?:\n|$)",
        "colour": r"Colour\s*:?\s*(.+?)(?:\n|$)",
        "case_number": r"Case\s+Number\s*:?\s*(\S+)",
        "owner_name": r"(?:Owner|Name)\s*:?\s*([\w\s]+Kamide|[\w\s]+(?:san|sama))",
        "test_date": r"Date\s+of\s+Test\s*:?\s*(.+?)(?:\n|$)",
        "test_requested": r"Test\s+Requested\s*:?\s*(.+?)(?:\n|$)",
        "approved_collection": r"Approved\s+Collection\s*(?:Method)?\s*:?\s*(Yes|No)",
        "sample_type": r"Sample\s+Type\s*:?\s*(\S+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            val = re.sub(r'\s+', ' ', val).strip()
            if val and val.lower() not in (':', ''):
                info[key] = val

    if "pet_name" not in info:
        m = re.search(r"Animal\s+Name\s*:?\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if m:
            info["pet_name"] = m.group(1).strip()

    if "owner_name" not in info:
        m = re.search(r"Name\s*:\s*(.+?)(?:\n|$)", text)
        if m:
            info["owner_name"] = m.group(1).strip()

    return info


def classify_result(result_text: str) -> str:
    """結果テキストからステータスを分類"""
    text_upper = result_text.upper()
    if "POSITIVE (P/P)" in text_upper or "TWO COPIES" in text_upper:
        return "positive"
    elif "CARRIER (P/N)" in text_upper or "ONE COPY OF THE" in text_upper:
        return "carrier"
    elif "NORMAL (N/N)" in text_upper or "NO VARIANT DETECTED" in text_upper:
        return "normal"
    elif "POSITIVE HETEROZYGOUS" in text_upper:
        return "carrier"
    elif "POSITIVE" in text_upper and "P/P" in text_upper:
        return "positive"
    elif "CARRIER" in text_upper:
        return "carrier"
    elif "NORMAL" in text_upper:
        return "normal"
    else:
        return "trait"


def get_japanese_name(test_name: str) -> str:
    """検査名から日本語名を取得"""
    name_lower = test_name.lower()
    for key, jp_name in TEST_NAME_JP.items():
        if key in name_lower:
            return jp_name
    return ""


def get_category_jp(category: str) -> str:
    """カテゴリーの日本語名を取得"""
    cat_lower = category.lower()
    for key, jp_name in CATEGORY_JP.items():
        if key in cat_lower:
            return jp_name
    return category


def extract_genotype(result_text: str, test_name: str = "") -> str:
    """結果テキストから遺伝子型を抽出（検査名に応じた優先順位付き）"""
    name_lower = test_name.lower() if test_name else ""

    # 検査名に特化した遺伝子型パターン（優先）
    specific_patterns = {
        "a locus": [r'(at/at|ay/at|ay/ay|a/a|aw/at|aw/aw|ay/aw)'],
        "b locus": [r'(Bb|BB|bb)\b'],
        "d locus": [r'(D/D|D/d|d/d)\b'],
        "dilute": [r'(D/D|D/d|d/d)\b'],
        "e locus": [r'(E/e|e/e|E/E|Em/E|Em/e)\b'],
        "em ": [r'(En/En|EM/EM|EM/En|EM/e)'],
        "mc1r": [r'(En/En|EM/EM|EM/En|EM/e)'],
        "melanistic mask": [r'(En/En|EM/EM|EM/En|EM/e)'],
        "k locus": [r'(KB\s*/\s*KB|K/K|KB\s*/\s*ky|KB\s*/\s*kbr|ky\s*/\s*ky|kbr\s*/\s*ky|kbr\s*/\s*kbr)'],
        "m locus": [r'(m/m|M/m|M/M)'],
        "merle": [r'(m/m|M/m|M/M)'],
        "curly": [r'(Cu/Cu|Cu/N|N/N)'],
        "furnishings": [r'(F/F|F/f|f/f)'],
        "rspo2": [r'(F/F|F/f|f/f)'],
        "pied": [r'(S/S|S/sp|sp/sp)'],
        "brown tyrp1": [r'(BL/BL|BL/bs|bs/bs)'],
        "tyrp1": [r'(BL/BL|BL/bs|bs/bs)'],
        "cdpa": [r'\b([PN])/([PN])\b'],
        "chondrodysplasia": [r'\b([PN])/([PN])\b'],
    }

    # 検査名に特化したパターンを優先的に試行
    for key, patterns in specific_patterns.items():
        if key in name_lower:
            for p in patterns:
                m = re.search(p, result_text, re.IGNORECASE)
                if m:
                    if m.lastindex and m.lastindex >= 2:
                        return f"{m.group(1)}/{m.group(2)}"
                    # スペースを除去して正規化（"KB / ky" → "KB/ky"）
                    return re.sub(r'\s*/\s*', '/', m.group(1)).strip()
            break

    # 汎用パターン（フォールバック）
    m = re.search(r'\b([PN])/([PN])\b', result_text)
    if m:
        return f"{m.group(1)}/{m.group(2)}"

    generic_patterns = [
        r'(at/at|ay/at|ay/ay|a/a|aw/at)',
        r'(Bb|BB|bb)\b',
        r'(D/D|D/d|d/d)\b',
        r'(E/e|e/e|E/E|Em/E|Em/e)\b',
        r'(En/En|EM/EM)',
        r'(KB/KB|K/K|KB/ky|KB/kbr|ky/ky|kbr/ky)',
        r'(m/m|M/m|M/M)',
        r'(Cu/Cu|Cu/N|N/N)',
        r'(F/F|F/f|f/f)',
        r'(S/S|S/sp|sp/sp)',
        r'(BL/BL|BL/bs|bs/bs)',
    ]
    for p in generic_patterns:
        m = re.search(p, result_text, re.IGNORECASE)
        if m:
            return m.group(1)

    m = re.search(r'^([A-Za-z/\[\]\d\s]{1,30})\s*[-–]', result_text)
    if m:
        return m.group(1).strip()

    return ""


def parse_health_tests(text: str) -> list:
    """健康検査結果を解析"""
    results = []

    category_headers = [
        ("Musculoskeletal", r"Musculoskeletal"),
        ("Haemolymphatic", r"Haemolymphatic"),
        ("Nervous system / Neurologic", r"Nervous\s+system|Neurologic"),
        ("Metabolic", r"Metabolic"),
        ("Ophthalmologic", r"Ophthalmologic"),
        ("Cardiorespiratory", r"Cardiorespiratory"),
        ("Cardiovascular", r"Cardiovascular"),
        ("Dermatologic", r"Dermatologic"),
        ("Immunological", r"Immunological"),
        ("Respiratory", r"Respiratory"),
        ("Urogenital", r"Urogenital"),
    ]

    lines = text.split('\n')
    current_category = "Trait"
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        for cat_name, cat_pattern in category_headers:
            if re.search(cat_pattern, line, re.IGNORECASE):
                current_category = cat_name
                break

        if "Trait (Associated with Phenotype)" in line:
            current_category = "Trait"

        if re.search(r'NORMAL\s*\(N/N\)|CARRIER\s*\(P/N\)|POSITIVE\s*\(P/P\)', line, re.IGNORECASE):
            m = re.match(r'(.+?)\s+((?:NORMAL|CARRIER|POSITIVE)\s*\([PN]/[PN]\).+)', line, re.IGNORECASE)
            if m:
                test_name = m.group(1).strip()
                result_text = m.group(2).strip()
            else:
                test_name = lines[i-1].strip() if i > 0 else ""
                result_text = line.strip()

            test_name = sanitize_text(test_name)
            result_text = sanitize_text(result_text)
            test_name = re.sub(r'^[\s\uf0b7\u2022\u25cf]+', '', test_name)
            test_name = re.sub(r'\s+', ' ', test_name).strip()

            if test_name and len(test_name) > 2 and is_valid_health_test(test_name):
                status = classify_result(result_text)
                genotype = extract_genotype(result_text, test_name)
                jp_name = get_japanese_name(test_name)
                cat_jp = get_category_jp(current_category)

                result = TestResult(
                    category=cat_jp,
                    test_name=test_name,
                    genotype=genotype,
                    result_text=result_text,
                    status=status,
                    japanese_name=jp_name,
                )

                if current_category != "Trait":
                    results.append(result)

        i += 1

    return results


def parse_trait_results_from_text(text: str) -> list:
    """形質（毛色）結果をテキストから解析"""
    results = []

    trait_items = [
        ("A Locus (Agouti)", r"A\s+Locus\s*\(Agouti\)"),
        ("B Locus (Brown)", r"B\s+Locus\s*[-–]?\s*(?:Bd|Bs|Bc|Various)"),
        ("Chondrodysplasia (CDPA)", r"Chondrodysplasia\s*\(CDPA\)"),
        ("Curly Coat/Hair Variant 1", r"Curly\s+Coat"),
        ("D (Dilute) Locus", r"D\s*\(?Dilute\)?\s+Locus"),
        ("E Locus (Cream/Red/Yellow)", r"E\s+Locus\s*[-–]?\s*\(?Cream"),
        ("EM (MC1R) - Melanistic Mask", r"EM\s*\(MC1R\)|Melanistic\s+Mask"),
        ("Furnishings (RSPO2)", r"Furnishings\s*\(RSPO2\)"),
        ("K Locus (Dominant Black)", r"K\s+Locus\s*\(Dominant"),
        ("M Locus (Merle/Dapple)", r"M\s+Locus\s*\(Merle"),
        ("Pied", r"Pied\b"),
        ("Brown TYRP1", r"Brown\s+TYRP1"),
        ("Improper Coat", r"Improper\s+Coat"),
        ("Coat Length", r"Coat\s+Length"),
    ]

    lines = text.split('\n')

    for test_name, pattern in trait_items:
        for i, line in enumerate(lines):
            if re.search(pattern, line, re.IGNORECASE):
                result_text = line
                for j in range(1, 3):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        # 他の形質・健康検査のヘッダー行は取り込まない
                        if next_line and not re.search(
                            r'^[A-Z]\s+Locus|^[ABDEKMS]\s*\(|^Breed|^Owner|^Microchip'
                            r'|^Pied|^Brown\s+TYRP|^Curly\s+Coat|^Furnish|^Chondro'
                            r'|^Improper|^Coat\s+Length|^EM\s*\(MC1R\)|^Melanistic'
                            r'|LOCUS\]|^\d+\.\s',
                            next_line, re.IGNORECASE
                        ):
                            result_text += " " + next_line
                        else:
                            break

                result_clean = re.sub(pattern, '', result_text, flags=re.IGNORECASE).strip()
                result_clean = re.sub(r'^[\s\-–:]+', '', result_clean).strip()

                genotype = extract_genotype(result_text, test_name)
                status = classify_result(result_text)
                if status == "normal" and test_name != "Chondrodysplasia (CDPA)":
                    status = "trait"

                jp_name = get_japanese_name(test_name)

                results.append(TestResult(
                    category="形質（毛色・外見）",
                    test_name=test_name,
                    genotype=genotype,
                    result_text=result_clean if result_clean else result_text,
                    status=status,
                    japanese_name=jp_name,
                ))
                break

    return results


def parse_pdf(pdf_path: str) -> Optional[DogProfile]:
    """PDFファイル1つを解析してDogProfileを返す"""
    basename = os.path.basename(pdf_path)
    if "DNAP" in basename.upper() or "DNA PROFILE" in basename.upper():
        text = extract_all_text(pdf_path)
        if "ISAG Profile" in text or "DNA Profile" in text:
            if "Health Tests Reported" not in text:
                print(f"  スキップ (DNAプロファイル): {basename}")
                return None

    if "見方" in basename or "説明" in basename:
        print(f"  スキップ (ガイド): {basename}")
        return None

    print(f"  解析中: {basename}")

    text = extract_all_text(pdf_path)

    if "Genetic Summary Report" not in text and "Health Tests Reported" not in text:
        print(f"  → Orivet Genetic Summary Report ではありません。スキップします。")
        return None

    info = parse_animal_details(text)
    if not info.get("pet_name") and not info.get("registered_name"):
        print(f"  → 動物情報を検出できませんでした。スキップします。")
        return None

    health_results = parse_health_tests(text)
    trait_results = parse_trait_results_from_text(text)

    dog = DogProfile(
        pet_name=info.get("pet_name", ""),
        registered_name=info.get("registered_name", ""),
        breed=info.get("breed", ""),
        sex=info.get("sex", ""),
        dob=info.get("dob", ""),
        colour=info.get("colour", ""),
        microchip=info.get("microchip", ""),
        case_number=info.get("case_number", ""),
        owner_name=info.get("owner_name", ""),
        test_date=info.get("test_date", ""),
        test_requested=info.get("test_requested", ""),
        approved_collection=info.get("approved_collection", ""),
        sample_type=info.get("sample_type", ""),
        health_results=health_results,
        trait_results=trait_results,
        source_file=basename,
    )

    print(f"  → {dog.pet_name or dog.registered_name}: 健康{len(health_results)}項目, 形質{len(trait_results)}項目")
    return dog


def is_pedigree_pdf(text: str) -> bool:
    """PDFテキストが血統書かどうかを判定"""
    # Orivet遺伝子レポートは除外
    if "Genetic Summary Report" in text or "Health Tests Reported" in text:
        return False
    # 血統書キーワードの検出
    pedigree_keywords = [
        r'JKC-PT|ジャパンケネルクラブ|JAPAN KENNEL CLUB',
        r'ALAJ|Australian Labradoodle',
        r'AKC|AMERICAN KENNEL CLUB',
        r'PEDIGREE|血統書|血統証明',
        r'SIRE.*DAM|DAM.*SIRE',
        r'G\.?\s*SIRE|G\.?\s*DAM',
        r'犬\s*名.*犬\s*種|犬\s*種.*犬\s*名',
        r'Name of Dog',
    ]
    score = sum(1 for p in pedigree_keywords if re.search(p, text, re.IGNORECASE))
    return score >= 1


def parse_pedigree_pdf(pdf_path: str) -> Optional[Pedigree]:
    """血統書PDFからPedigreeデータを抽出"""
    if not HAS_PDFPLUMBER:
        return None

    basename = os.path.basename(pdf_path)
    print(f"  血統書PDF解析中: {basename}")

    try:
        text = extract_all_text(pdf_path)
    except Exception as e:
        print(f"  → PDF読み取りエラー: {e}")
        return None

    if not text or not is_pedigree_pdf(text):
        return None

    ped = parse_pedigree_text(text)
    if ped and ped.dog_name:
        ped.source_file = basename
        print(f"  → 血統書PDF検出: {ped.dog_name}")
        return ped
    else:
        print(f"  → 血統書データの解析に失敗しました")
        return None


# ████████████████████████████████████████████████████████████
# PART 2: 血統書 OCR + COI 算出
# ████████████████████████████████████████████████████████████

def try_ocr(image_path: str) -> str:
    """画像からテキストを抽出（Tesseract OCR）— 写真向け前処理付き"""
    if not HAS_OCR:
        print("  pytesseract が未インストールです。")
        print("  pip install pytesseract Pillow")
        print("  + Tesseract OCR本体: sudo apt install tesseract-ocr tesseract-ocr-jpn")
        return ""
    try:
        from PIL import ImageEnhance, ImageFilter, ImageOps
        img = Image.open(image_path)
        # HEIC/WEBP等をRGBに変換
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # EXIF回転情報を適用（写真の向き補正）
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # --- 写真向け前処理 ---
        # 1. リサイズ（速度改善 + Tesseract最適解像度）
        max_dim = 2000
        if max(img.size) > max_dim:
            ratio = max_dim / max(img.size)
            img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)

        # 2. グレースケール変換
        gray = img.convert("L")

        # 3. コントラスト・シャープネス強化
        gray = ImageEnhance.Contrast(gray).enhance(2.0)
        gray = ImageEnhance.Sharpness(gray).enhance(2.0)

        # 4. 軽いノイズ除去（MedianFilter）
        gray = gray.filter(ImageFilter.MedianFilter(size=3))

        # 5. 適応的二値化（ブロック平均ベース）
        # numpy不要の簡易実装: 全体平均から閾値を決定
        stat = gray.resize((1, 1), Image.LANCZOS).getpixel((0, 0))
        threshold = max(stat - 30, 80)
        binarized = gray.point(lambda x: 255 if x > threshold else 0)

        # OCR実行（1パスで高速化）
        # 血統書の主要情報は英語表記が多いため eng+jpn 順で優先
        ocr_timeout = 90
        best_text = ""

        # パス1: 英語優先（高速・血統書の構造テキストに最適）
        try:
            text = pytesseract.image_to_string(
                binarized, lang='eng+jpn', config='--psm 6 --oem 3',
                timeout=ocr_timeout
            )
            if text:
                best_text = text
        except RuntimeError:
            pass

        # 十分なテキストが取れた場合は早期終了
        if len(best_text) > 300 and re.search(r'SIRE|DAM|JKC|PEDIGREE|血統', best_text, re.IGNORECASE):
            return best_text

        # パス2: フォールバック（グレースケール + 日本語優先）
        try:
            text = pytesseract.image_to_string(
                gray, lang='jpn+eng', config='--psm 6 --oem 3',
                timeout=ocr_timeout
            )
            if len(text) > len(best_text):
                best_text = text
        except RuntimeError:
            pass

        return best_text
    except Exception as e:
        print(f"  OCRエラー: {e}")
        return ""


def detect_pedigree_format(text: str) -> str:
    """血統書のフォーマットを自動判定"""
    if re.search(r'JKC-PT|ジャパンケネルクラブ|JAPAN KENNEL CLUB', text, re.IGNORECASE):
        return "jkc"
    if re.search(r'ALAJ|Australian Labradoodle|ラブラドゥードル', text, re.IGNORECASE):
        return "alaj"
    if re.search(r'AKC|AMERICAN KENNEL CLUB', text, re.IGNORECASE):
        return "akc"
    if re.search(r'KC\b|THE KENNEL CLUB', text, re.IGNORECASE):
        return "kc"
    if re.search(r'SIRE|DAM|G\.SIRE|G\.DAM|PEDIGREE|血統書', text, re.IGNORECASE):
        return "generic"
    return "generic"


def _extract_basic_info(text: str, ped: Pedigree):
    """共通の基本情報を抽出"""
    if re.search(r'\bMALE\b|オス|牡|♂|性\s*別\s*Male', text, re.IGNORECASE):
        ped.sex = "MALE"
    elif re.search(r'\bFEMALE\b|メス|牝|♀|性\s*別\s*Female', text, re.IGNORECASE):
        ped.sex = "FEMALE"

    m = re.search(r'(\d{4}年\s*\d{1,2}月\s*\d{1,2}日)', text)
    if m:
        ped.dob = m.group(1)
    else:
        m = re.search(r'(?:生年月日|Date of Birth|DOB|D\.O\.B)\s*[:\s]*(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})', text, re.IGNORECASE)
        if m:
            ped.dob = m.group(1)
        else:
            m = re.search(r'(?:生\s*年\s*月\s*日)\s*(\d{4}/\d{1,2}/\d{1,2})', text)
            if m:
                ped.dob = m.group(1)

    m = re.search(r'(?:毛\s*色|色|Color|Colour)\s*[:\s]*([A-Za-z\s]+?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        ped.color = m.group(1).strip()

    m = re.search(r'(?:マイクロチップ|Microchip|MC|ID)\s*[番号:\s]*(\d{10,15})', text, re.IGNORECASE)
    if m:
        ped.microchip = m.group(1)

    m = re.search(r'(?:所\s*有\s*者|Owner)\s*[:\s]*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        ped.owner = m.group(1).strip()

    m = re.search(r'(?:繁殖者|Breeder)\s*[:\s]*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        ped.breeder = m.group(1).strip()

    m = re.search(r'(?:犬\s*種|Breed)\s*[:\s]*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        ped.breed = m.group(1).strip()


def _extract_jkc_dog_name_from_line(text_after: str) -> tuple:
    """JKCラベル直後のテキストから犬名・登録番号・毛色・DNA番号を抽出"""
    name = ""
    registration = ""
    color = ""
    dna = ""
    lines = [l.strip() for l in text_after.split('\n') if l.strip()]
    for line in lines:
        # ラベル行（SIRE/DAM等）自体はスキップ
        if re.match(r'^(?:SIRE|DAM|G\.\s*(?:G\.\s*)?(?:SIRE|DAM)|父|母|祖父|祖母|曾祖父|曾祖母)\b', line, re.IGNORECASE):
            continue
        # CH/タイトル + 犬名行
        if not name:
            # タイトル(CH/xx.xx)を除いた犬名を取得
            cleaned = re.sub(r'^(?:CH/[\d.]+\s*,?\s*)*', '', line).strip()
            # "SMASH JP ..." のようなケネル名パターン
            m_name = re.search(r'([A-Z][A-Z\s]+(?:JP|OF|DE|VAN|VON)\s+[A-Z][A-Z\s]+)', cleaned)
            if m_name:
                name = m_name.group(1).strip()
                continue
            # 英字3文字以上で犬名とみなす
            cleaned = re.sub(r'\s*JKC-PT.*$', '', cleaned).strip()
            cleaned = re.sub(r'\s*CD\d*\s*$', '', cleaned).strip()
            if len(cleaned) >= 3 and re.search(r'[A-Z]', cleaned):
                name = cleaned
                continue
        # JKC-PT 登録番号
        m_reg = re.search(r'(JKC-PT\s*-?\s*\d+/\d+)', line)
        if m_reg:
            registration = m_reg.group(1)
        # DNA番号
        m_dna = re.search(r'(DNA\s*JP\d+/\d+)', line)
        if m_dna:
            dna = m_dna.group(1)
        # 毛色
        m_color = re.search(r'\b(BLK|BLACK|WH|WHITE|BR|BROWN|RED|APR|APRICOT|CR|CREAM|SV|SILVER|BL|BLUE|CAFE|GOLD|FAWN|SABLE|BRINDLE|MERLE|PARTI|BEIGE)\b', line, re.IGNORECASE)
        if m_color and not color:
            color = m_color.group(1).upper()
        # 4行で十分
        if name and registration:
            break
    return name, registration, color, dna


def _parse_jkc_ancestors(text: str, ped: Pedigree):
    """JKC形式の祖先名を抽出（番号ベース + ラベルベース）"""
    # --- 方法1: 番号ベース ---
    lines = text.split('\n')
    ancestors = {}
    for line in lines:
        m = re.match(r'\s*(\d{1,2})\s*[\|\{(]?\s*(.+)', line)
        if m:
            num = int(m.group(1))
            if 1 <= num <= 14:
                name_text = m.group(2).strip()
                # ラベル部分を除去（"G.SIRE 祖父" 等）
                name_text = re.sub(r'^(?:G\.?\s*G\.?\s*)?(?:SIRE|DAM)\s*', '', name_text, flags=re.IGNORECASE).strip()
                name_text = re.sub(r'^(?:父|母|祖父|祖母|曾祖父|曾祖母)\s*', '', name_text).strip()
                name_text = re.sub(r'\s*JKC-PT.*$', '', name_text).strip()
                name_text = re.sub(r'\s*CH/\d+.*$', '', name_text).strip()
                name_text = re.sub(r'\s*CD\d*\s*$', '', name_text).strip()
                if len(name_text) > 2:
                    ancestors[num] = name_text

    pos_map = {
        1: "sire", 2: "dam", 3: "ss", 4: "sd", 5: "ds", 6: "dd",
        7: "sss", 8: "ssd", 9: "sds", 10: "sdd",
        11: "dss", 12: "dsd", 13: "dds", 14: "ddd"
    }
    for num, name in ancestors.items():
        if num in pos_map:
            setattr(ped, pos_map[num], Ancestor(position=pos_map[num], name=name))

    # --- 方法2: ラベルベース（番号ベースで取れなかったものを補完）---
    # JKC血統書のラベルパターン: "G.G.SIRE 曾祖父" / "G.SIRE 祖父" / "SIRE 父"
    label_patterns = [
        # (regex, position, priority) — longer patterns first to avoid partial matches
        (r'G\.?\s*G\.?\s*SIRE\s*(?:曾祖父)?', 'sss', 7),  # 曾祖父 positions: 7,9,11,13
        (r'G\.?\s*G\.?\s*DAM\s*(?:曾祖母)?', 'ssd', 8),    # 曾祖母 positions: 8,10,12,14
        (r'G\.?\s*SIRE\s*(?:祖父)?', 'ss', 3),               # 祖父 positions: 3,5
        (r'G\.?\s*DAM\s*(?:祖母)?', 'sd', 4),                 # 祖母 positions: 4,6
        (r'\bSIRE\s*(?:父)?', 'sire', 1),
        (r'\bDAM\s*(?:母)?', 'dam', 2),
    ]

    # G.G.SIRE/G.G.DAM の位置を順番に割り当てるためのカウンター
    gg_sire_slots = ['sss', 'sds', 'dss', 'dds']
    gg_dam_slots = ['ssd', 'sdd', 'dsd', 'ddd']
    g_sire_slots = ['ss', 'ds']
    g_dam_slots = ['sd', 'dd']
    gg_sire_idx = 0
    gg_dam_idx = 0
    g_sire_idx = 0
    g_dam_idx = 0

    # G.G.SIRE / G.G.DAM を検索
    for m in re.finditer(r'G\.?\s*G\.?\s*SIRE\s*(?:曾祖父)?', text, re.IGNORECASE):
        pos_after = m.end()
        remaining = text[pos_after:pos_after + 300]
        name, reg, color, dna = _extract_jkc_dog_name_from_line(remaining)
        if name and gg_sire_idx < len(gg_sire_slots):
            slot = gg_sire_slots[gg_sire_idx]
            if not getattr(ped, slot):
                setattr(ped, slot, Ancestor(position=slot, name=name, registration=reg, color=color, dna_number=dna))
            gg_sire_idx += 1

    for m in re.finditer(r'G\.?\s*G\.?\s*DAM\s*(?:曾祖母)?', text, re.IGNORECASE):
        pos_after = m.end()
        remaining = text[pos_after:pos_after + 300]
        name, reg, color, dna = _extract_jkc_dog_name_from_line(remaining)
        if name and gg_dam_idx < len(gg_dam_slots):
            slot = gg_dam_slots[gg_dam_idx]
            if not getattr(ped, slot):
                setattr(ped, slot, Ancestor(position=slot, name=name, registration=reg, color=color, dna_number=dna))
            gg_dam_idx += 1

    # G.SIRE / G.DAM（G.G.を除外）
    for m in re.finditer(r'G\.?\s*SIRE\s*(?:祖父)?', text, re.IGNORECASE):
        # G.G.SIREにマッチしていないか確認
        start = m.start()
        prefix = text[max(0, start - 3):start]
        if re.search(r'G\.?$', prefix):
            continue
        pos_after = m.end()
        remaining = text[pos_after:pos_after + 300]
        name, reg, color, dna = _extract_jkc_dog_name_from_line(remaining)
        if name and g_sire_idx < len(g_sire_slots):
            slot = g_sire_slots[g_sire_idx]
            if not getattr(ped, slot):
                setattr(ped, slot, Ancestor(position=slot, name=name, registration=reg, color=color, dna_number=dna))
            g_sire_idx += 1

    for m in re.finditer(r'G\.?\s*DAM\s*(?:祖母)?', text, re.IGNORECASE):
        start = m.start()
        prefix = text[max(0, start - 3):start]
        if re.search(r'G\.?$', prefix):
            continue
        pos_after = m.end()
        remaining = text[pos_after:pos_after + 300]
        name, reg, color, dna = _extract_jkc_dog_name_from_line(remaining)
        if name and g_dam_idx < len(g_dam_slots):
            slot = g_dam_slots[g_dam_idx]
            if not getattr(ped, slot):
                setattr(ped, slot, Ancestor(position=slot, name=name, registration=reg, color=color, dna_number=dna))
            g_dam_idx += 1

    # SIRE / DAM（G.SIRE/G.DAMを除外）
    if not ped.sire:
        m = re.search(r'(?<![G.])\bSIRE\s*(?:父)?', text, re.IGNORECASE)
        if m:
            remaining = text[m.end():m.end() + 300]
            name, reg, color, dna = _extract_jkc_dog_name_from_line(remaining)
            if name:
                ped.sire = Ancestor(position="sire", name=name, registration=reg, color=color, dna_number=dna)

    if not ped.dam:
        m = re.search(r'(?<![G.])\bDAM\s*(?:母)?', text, re.IGNORECASE)
        if m:
            remaining = text[m.end():m.end() + 300]
            name, reg, color, dna = _extract_jkc_dog_name_from_line(remaining)
            if name:
                ped.dam = Ancestor(position="dam", name=name, registration=reg, color=color, dna_number=dna)


def _parse_labeled_ancestors(text: str, ped: Pedigree):
    """ラベルベースの祖先抽出（SIRE/DAM/G.SIRE/G.DAM形式 — ALAJ等）"""

    def get_name_after_label(text: str, label_end: int, max_chars: int = 200) -> str:
        remaining = text[label_end:label_end + max_chars]
        lines = [l.strip() for l in remaining.split('\n') if l.strip()]
        for line in lines:
            if re.match(r'^(?:SIRE|DAM|G\.?SIRE|G\.?DAM|GG|父犬|母犬|祖父|祖母|曾祖|犬種|性別|サイズ|毛色|生年月日|所有者)', line, re.IGNORECASE):
                continue
            cleaned = re.sub(r'^\d+\s*', '', line).strip()
            if len(cleaned) >= 3 and not re.match(r'^\d{4}[/\-]', cleaned):
                return cleaned
        return ""

    sire_match = re.search(r'(?:^|\n)\s*SIRE\b', text, re.IGNORECASE)
    dam_match = re.search(r'(?:^|\n)\s*DAM\b', text, re.IGNORECASE)

    gsire_positions = [(m.start(), m.end()) for m in re.finditer(r'G\.?SIRE\b|父方祖父|祖父犬', text, re.IGNORECASE)]
    gdam_positions = [(m.start(), m.end()) for m in re.finditer(r'G\.?DAM\b|父方祖母|祖母犬', text, re.IGNORECASE)]

    if sire_match:
        name = get_name_after_label(text, sire_match.end())
        if name:
            ped.sire = Ancestor(position="sire", name=name)

    if dam_match:
        name = get_name_after_label(text, dam_match.end())
        if name:
            ped.dam = Ancestor(position="dam", name=name)

    dam_pos = dam_match.start() if dam_match else len(text) // 2

    sire_gsires = [p for p in gsire_positions if p[0] < dam_pos]
    sire_gdams = [p for p in gdam_positions if p[0] < dam_pos]
    dam_gsires = [p for p in gsire_positions if p[0] >= dam_pos]
    dam_gdams = [p for p in gdam_positions if p[0] >= dam_pos]

    if sire_gsires:
        name = get_name_after_label(text, sire_gsires[0][1])
        if name:
            ped.ss = Ancestor(position="ss", name=name)
    if sire_gdams:
        name = get_name_after_label(text, sire_gdams[0][1])
        if name:
            ped.sd = Ancestor(position="sd", name=name)
    if dam_gsires:
        name = get_name_after_label(text, dam_gsires[0][1])
        if name:
            ped.ds = Ancestor(position="ds", name=name)
    if dam_gdams:
        name = get_name_after_label(text, dam_gdams[0][1])
        if name:
            ped.dd = Ancestor(position="dd", name=name)

    gg_sire_positions = [(m.start(), m.end()) for m in re.finditer(r'GG\.?SIRE\b|G\.G\.SIRE|曾祖父', text, re.IGNORECASE)]
    gg_dam_positions = [(m.start(), m.end()) for m in re.finditer(r'GG\.?DAM\b|G\.G\.DAM|曾祖母', text, re.IGNORECASE)]

    gg_sire_fields = ["sss", "sds", "dss", "dds"]
    gg_dam_fields = ["ssd", "sdd", "dsd", "ddd"]

    for idx, (start, end) in enumerate(gg_sire_positions):
        if idx < len(gg_sire_fields):
            name = get_name_after_label(text, end)
            if name:
                setattr(ped, gg_sire_fields[idx], Ancestor(position=gg_sire_fields[idx], name=name))

    for idx, (start, end) in enumerate(gg_dam_positions):
        if idx < len(gg_dam_fields):
            name = get_name_after_label(text, end)
            if name:
                setattr(ped, gg_dam_fields[idx], Ancestor(position=gg_dam_fields[idx], name=name))


def parse_jkc_pedigree_text(text: str) -> Optional[Pedigree]:
    """OCRテキストから血統書を解析（全フォーマット自動対応）"""
    return parse_pedigree_text(text)


def parse_pedigree_text(text: str) -> Optional[Pedigree]:
    """OCRテキストから血統書を解析（全フォーマット自動対応）"""
    if not text:
        return None

    ped = Pedigree()
    fmt = detect_pedigree_format(text)

    _extract_basic_info(text, ped)

    if fmt == "jkc":
        # 犬名抽出: "Name of Dog" / "犬名" の後
        m = re.search(r'(?:Name of Dog|犬\s*名)\s*\n?\s*(.+?)(?:\n|$)', text)
        if m:
            candidate = m.group(1).strip()
            # "Name of Dog" 自体の残りやラベルだけの場合はスキップして次の行を探す
            if len(candidate) < 3 or re.match(r'^(?:Name|犬名|犬\s*名)', candidate, re.IGNORECASE):
                # 次の非空行を犬名として取る
                after = text[m.end():]
                for line in after.split('\n'):
                    line = line.strip()
                    if line and len(line) >= 3 and not re.match(r'^(?:Breed|犬\s*種|登録|スマ)', line, re.IGNORECASE):
                        # カタカナ読み行はスキップ
                        if re.match(r'^[ァ-ヴー\s゛゜]+$', line):
                            continue
                        ped.dog_name = line
                        break
            else:
                ped.dog_name = candidate
        # 犬名が取れなかった場合、大文字ケネル名パターンで探す
        if not ped.dog_name:
            m_name = re.search(r'([A-Z][A-Z\s]+(?:JP|OF|DE|VAN|VON)\s+[A-Z][A-Z\s]+)\s*\n', text)
            if m_name:
                ped.dog_name = m_name.group(1).strip()

        m = re.search(r'(JKC-PT\s*-?\s*\d+/\d+)', text)
        if m:
            ped.registration = m.group(1)
        _parse_jkc_ancestors(text, ped)

    elif fmt == "alaj":
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            for i, line in enumerate(lines):
                if re.search(r'PEDIGREE|血統書', line, re.IGNORECASE):
                    # 犬名がPEDIGREEと同じ行にある場合
                    name_on_line = re.sub(r'\s*PEDIGREE\s*', '', line, flags=re.IGNORECASE).strip()
                    name_on_line = re.sub(r'\s*血統書\s*', '', name_on_line).strip()
                    if len(name_on_line) > 3:
                        ped.dog_name = name_on_line
                    elif i > 0:
                        ped.dog_name = lines[i-1].strip()
                    break
            if not ped.dog_name and lines:
                ped.dog_name = lines[0].strip()

        m = re.search(r'(?:登\s*録\s*番\s*号|Registration)\s*[:\s]*([A-Z]{2,}\d+)', text, re.IGNORECASE)
        if m:
            ped.registration = m.group(1)

        _parse_labeled_ancestors(text, ped)

    else:
        m = re.search(r'(?:Name of Dog|犬名|Dog Name|名前)\s*[:\s]*\n?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if m:
            ped.dog_name = m.group(1).strip()
        else:
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if lines:
                ped.dog_name = lines[0]

        m = re.search(r'(?:登録番号|Registration|Reg\.?\s*No\.?)\s*[:\s]*([A-Z0-9\-/]+)', text, re.IGNORECASE)
        if m:
            ped.registration = m.group(1)

        _parse_labeled_ancestors(text, ped)
        if not ped.sire:
            _parse_jkc_ancestors(text, ped)

    if not ped.dog_name:
        lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 5]
        if lines:
            ped.dog_name = lines[0]

    return ped


def calc_coi_3gen(ped: Pedigree) -> dict:
    """3世代の血統データからCOIを算出"""
    sire_ancestors = []
    dam_ancestors = []

    def _normalize_name(name):
        """スペースの揺れを正規化して比較精度を向上"""
        return re.sub(r'\s+', ' ', name.strip().upper())

    def add_if_exists(lst, ancestor, gen):
        if ancestor and ancestor.name:
            lst.append({"name": _normalize_name(ancestor.name), "gen": gen})

    add_if_exists(sire_ancestors, ped.sire, 1)
    add_if_exists(sire_ancestors, ped.ss, 2)
    add_if_exists(sire_ancestors, ped.sd, 2)
    add_if_exists(sire_ancestors, ped.sss, 3)
    add_if_exists(sire_ancestors, ped.ssd, 3)
    add_if_exists(sire_ancestors, ped.sds, 3)
    add_if_exists(sire_ancestors, ped.sdd, 3)

    add_if_exists(dam_ancestors, ped.dam, 1)
    add_if_exists(dam_ancestors, ped.ds, 2)
    add_if_exists(dam_ancestors, ped.dd, 2)
    add_if_exists(dam_ancestors, ped.dss, 3)
    add_if_exists(dam_ancestors, ped.dsd, 3)
    add_if_exists(dam_ancestors, ped.dds, 3)
    add_if_exists(dam_ancestors, ped.ddd, 3)

    coi = 0.0
    common = []
    for sa in sire_ancestors:
        for da in dam_ancestors:
            if sa["name"] == da["name"]:
                contribution = 0.5 ** (sa["gen"] + da["gen"] + 1)
                coi += contribution
                common.append({
                    "name": sa["name"],
                    "sire_gen": sa["gen"],
                    "dam_gen": da["gen"],
                    "contribution": contribution
                })

    return {
        "coi": coi,
        "coi_pct": coi * 100,
        "common_ancestors": common,
        "sire_count": len(sire_ancestors),
        "dam_count": len(dam_ancestors),
    }


def calc_coi_cross(sire_ped: Pedigree, dam_ped: Pedigree) -> dict:
    """2頭の血統書から交配時のCOIを算出（子犬のCOI予測）"""
    sire_all = []
    dam_all = []

    def collect(lst, ped, base_gen=0):
        ancestors_data = [
            (ped.sire, 1), (ped.dam, 1),
            (ped.ss, 2), (ped.sd, 2), (ped.ds, 2), (ped.dd, 2),
            (ped.sss, 3), (ped.ssd, 3), (ped.sds, 3), (ped.sdd, 3),
            (ped.dss, 3), (ped.dsd, 3), (ped.dds, 3), (ped.ddd, 3),
        ]
        def _norm(n):
            return re.sub(r'\s+', ' ', n.strip().upper())
        if ped.dog_name:
            lst.append({"name": _norm(ped.dog_name), "gen": base_gen})
        for anc, gen in ancestors_data:
            if anc and anc.name:
                lst.append({"name": _norm(anc.name), "gen": base_gen + gen})

    collect(sire_all, sire_ped, 0)
    collect(dam_all, dam_ped, 0)

    coi = 0.0
    common = []
    seen = set()
    for sa in sire_all:
        for da in dam_all:
            if sa["name"] == da["name"]:
                key = f"{sa['name']}_{sa['gen']}_{da['gen']}"
                if key not in seen:
                    seen.add(key)
                    contribution = 0.5 ** (sa["gen"] + da["gen"] + 1)
                    coi += contribution
                    common.append({
                        "name": sa["name"],
                        "sire_gen": sa["gen"],
                        "dam_gen": da["gen"],
                        "contribution": contribution
                    })

    return {
        "coi": coi,
        "coi_pct": coi * 100,
        "common_ancestors": common,
    }


# ████████████████████████████████████████████████████████████
# PART 3: 統合HTML出力
# ████████████████████████████████████████████████████████████

def sanitize_text(text: str) -> str:
    """PDF由来の文字化け・制御文字を修正"""
    if not text:
        return text
    # 制御文字を除去
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    # よくある文字化けパターンを修正
    text = text.replace('\ufffd', '')      # 置換文字(�)を除去
    text = re.sub(r'(?<=[a-z])\s*\ufb00\s*(?=[a-z])', 'ff', text)  # ﬀ → ff
    text = re.sub(r'(?<=[a-z])\s*\ufb01\s*(?=[a-z])', 'fi', text)  # ﬁ → fi
    text = re.sub(r'(?<=[a-z])\s*\ufb02\s*(?=[a-z])', 'fl', text)  # ﬂ → fl
    text = re.sub(r'(?<=[a-z])\s*\ufb03\s*(?=[a-z])', 'ffi', text) # ﬃ → ffi
    text = re.sub(r'(?<=[a-z])\s*\ufb04\s*(?=[a-z])', 'ffl', text) # ﬄ → ffl
    return text


def sanitize_for_excel(text: str) -> str:
    """Excelで使えない文字を除去"""
    return sanitize_text(text)


def _h(text) -> str:
    """HTMLエスケープ（XSS対策）"""
    if text is None:
        return ""
    s = str(text)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#x27;")


def status_badge(status: str, text: str) -> str:
    return f'<span class="status {status}">{_h(text)}</span>'


def generate_unified_html(dogs: list, pedigrees: list, output_path: str):
    """遺伝子検査 + 血統書 + COIの統合HTMLレポートを生成"""

    now_str = datetime.now().strftime('%Y年%m月%d日')

    # Count totals
    total_normal = sum(len([r for r in d.health_results if r.status == "normal"]) for d in dogs)
    total_carrier = sum(len([r for r in d.health_results if r.status == "carrier"]) for d in dogs)
    total_positive = sum(len([r for r in d.health_results if r.status == "positive"]) for d in dogs)

    has_orivet = len(dogs) > 0
    has_pedigree = len(pedigrees) > 0

    # ── Dog tabs (Orivet) ──
    tab_buttons = ""
    tab_contents = ""
    sex_i18n_en = {}  # per-dog sex translations for JS

    for idx, dog in enumerate(dogs):
        name = dog.pet_name or dog.registered_name or f"犬{idx+1}"
        safe_id = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())

        tab_buttons += f'    <div class="tab" onclick="showTab(\'{safe_id}\')">{_h(name)}</div>\n'

        sex_class = "male" if "male" in dog.sex.lower() else "female"
        sex_label = "オス" if "male" in dog.sex.lower() else "メス"
        sex_label_en = "Male" if "male" in dog.sex.lower() else "Female"
        sex_i18n_en[f"sex_{safe_id}"] = sex_label_en

        health_rows = ""
        for r in dog.health_results:
            display_name = _h(r.japanese_name if r.japanese_name else r.test_name)
            badge = status_badge(r.status, r.genotype if r.genotype else r.status.upper())
            annotation = get_health_annotation(r.test_name, r.genotype, r.status)
            annotation_html = f'<div style="margin-top:4px;padding:6px 8px;background:#fef3c7;border-left:3px solid #f59e0b;border-radius:4px;font-size:0.85em;color:#374151;">{_h(annotation)}</div>' if annotation else ''
            health_rows += f"""        <tr>
          <td>{_h(r.category)}</td>
          <td>{display_name}<br><small style="color:#6b7280">{_h(r.test_name)}</small>{annotation_html}</td>
          <td>{badge}</td>
          <td style="font-size:0.85em">{_h(r.result_text[:120])}</td>
        </tr>\n"""

        trait_rows = ""
        for r in dog.trait_results:
            display_name = _h(r.japanese_name if r.japanese_name else r.test_name)
            badge = status_badge("trait", r.genotype if r.genotype else "—")
            annotation = get_trait_annotation(r.test_name, r.genotype)
            annotation_html = f'<div style="margin-top:4px;padding:6px 8px;background:#f0f4ff;border-left:3px solid #667eea;border-radius:4px;font-size:0.85em;color:#374151;">{_h(annotation)}</div>' if annotation else ''
            trait_rows += f"""        <tr>
          <td>{display_name}<br><small style="color:#6b7280">{_h(r.test_name)}</small></td>
          <td>{badge}</td>
          <td style="font-size:0.85em">{_h(r.result_text[:150])}{annotation_html}</td>
        </tr>\n"""

        tab_contents += f"""
  <div id="{safe_id}" class="tab-content">
    <div class="dog-card">
      <div class="dog-header">
        <div>
          <div class="dog-name">{_h(name)}</div>
          <div class="dog-reg">{_h(dog.registered_name)} — {_h(dog.case_number)}</div>
        </div>
        <div class="dog-meta">
          <span class="meta-tag {sex_class}"><span data-i18n="sex_{safe_id}">{_h(sex_label)}</span> ({_h(dog.sex)})</span>
          <span class="meta-tag">{_h(dog.breed)}</span>
          <span class="meta-tag">{_h(dog.dob)}</span>
          {'<span class="meta-tag">MC: ' + _h(dog.microchip) + '</span>' if dog.microchip else ''}
          {'<span class="meta-tag"><span data-i18n="lbl_colour">毛色</span>: ' + _h(dog.colour) + '</span>' if dog.colour else ''}
        </div>
      </div>

      <h3 class="section-title"><span data-i18n="health_results">健康検査結果</span> ({len(dog.health_results)}<span data-i18n="items_suffix">項目</span>)</h3>
      <table class="results-table">
        <tr><th data-i18n="th_category">カテゴリー</th><th data-i18n="th_test">検査項目</th><th data-i18n="th_result">結果</th><th data-i18n="th_detail">詳細</th></tr>
{health_rows}
      </table>

      <h3 class="section-title"><span data-i18n="trait_results">毛色・形質検査結果</span> ({len(dog.trait_results)}<span data-i18n="items_suffix">項目</span>)</h3>
      <table class="results-table">
        <tr><th data-i18n="th_test">検査項目</th><th data-i18n="th_genotype">遺伝子型</th><th data-i18n="th_detail">詳細</th></tr>
{trait_rows}
      </table>
    </div>
  </div>"""

    # ── Comparison table ──
    compare_tab_button = ""
    compare_tab_html = ""
    if len(dogs) > 1:
        all_tests = {}
        for dog in dogs:
            for r in dog.health_results:
                key = r.test_name
                if key not in all_tests:
                    all_tests[key] = {"jp": r.japanese_name or r.test_name, "name": r.test_name}

        compare_header = '<th data-i18n="th_test">検査項目</th>'
        for dog in dogs:
            compare_header += f"<th>{_h(dog.pet_name or dog.registered_name)}</th>"

        compare_health_rows = ""
        for test_key, test_info in all_tests.items():
            row = f"<td>{test_info['jp']}</td>"
            for dog in dogs:
                found = False
                for r in dog.health_results:
                    if r.test_name == test_key:
                        badge = status_badge(r.status, r.genotype if r.genotype else r.status.upper())
                        row += f"<td>{badge}</td>"
                        found = True
                        break
                if not found:
                    row += "<td>—</td>"
            compare_health_rows += f"        <tr>{row}</tr>\n"

        compare_tab_button = '<div class="tab" onclick="showTab(\'compare\')"><span data-i18n="tab_compare">比較表</span></div>'
        compare_tab_html = f"""<div id="compare" class="tab-content">
    <div class="dog-card">
      <h2 class="section-title" data-i18n="health_compare">健康検査 比較表</h2>
      <div style="overflow-x:auto;">
      <table class="compare-table">
        <tr>{compare_header}</tr>
{compare_health_rows}
      </table>
      </div>
    </div>
  </div>"""

    # ── Alerts ──
    alerts_html = ""
    for dog in dogs:
        for r in dog.health_results:
            name = _h(dog.pet_name or dog.registered_name)
            display_name = _h(r.japanese_name if r.japanese_name else r.test_name)
            if r.status == "positive":
                alerts_html += f"""      <div class="breed-warn danger">
        <div class="warn-title">{display_name} — <span data-i18n="lbl_positive">ポジティブ</span> (P/P): {name}</div>
        <p data-i18n="alert_positive">変異が2コピー検出されました。発症リスクがあります。獣医師にご相談の上、適切なケアをお願いいたします。</p>
        <p><small><span data-i18n="lbl_original">原文</span>: {_h(r.result_text[:200])}</small></p>
      </div>\n"""
            elif r.status == "carrier":
                alerts_html += f"""      <div class="breed-warn">
        <div class="warn-title">{display_name} — <span data-i18n="lbl_carrier">キャリア</span> (P/N): {name}</div>
        <p data-i18n="alert_carrier">変異が1コピー検出されました。キャリアまたはポジティブの個体との交配で発症する子犬が生まれる可能性があります。</p>
      </div>\n"""

    if not alerts_html and has_orivet:
        alerts_html = '<div class="breed-warn" style="background:#dcfce7;border-color:#86efac;"><div class="warn-title" style="color:#166534;" data-i18n="all_clear">全頭クリア</div><p data-i18n="all_clear_desc">全ての健康検査項目でノーマル（変異なし）でした。</p></div>'

    # ── Overview table rows ──
    overview_table_rows = ""
    for d in dogs:
        overview_table_rows += f"<tr><td><strong>{_h(d.pet_name)}</strong></td><td>{_h(d.registered_name)}</td><td>{_h(d.breed)}</td><td>{_h(d.sex)}</td><td>{_h(d.dob)}</td><td>{_h(d.case_number)}</td></tr>\n"

    # ── Pedigree section ──
    pedigree_tab_button = ""
    pedigree_tab_html = ""
    if has_pedigree:
        pedigree_tab_button = '<div class="tab" onclick="showTab(\'pedigree\')"><span data-i18n="tab_pedigree">血統書 + COI</span></div>'

        ped_parts = []
        for ped in pedigrees:
            coi_result = calc_coi_3gen(ped)

            ancestors_html = ""
            for label, anc in ped.all_ancestors():
                if anc:
                    _color_map = {
                        "BLK": "#1a1a1a", "BLACK": "#1a1a1a",
                        "WH": "#f5f5f5", "WHITE": "#f5f5f5",
                        "BR": "#8B4513", "BROWN": "#8B4513", "CHOCO": "#5C3317",
                        "RED": "#CD5C5C",
                        "APR": "#FBCEB1", "APRICOT": "#FBCEB1",
                        "CR": "#FFF8DC", "CREAM": "#FFF8DC",
                        "SV": "#C0C0C0", "SILVER": "#C0C0C0",
                        "BL": "#4a6fa5", "BLUE": "#4a6fa5",
                        "CAFE": "#A67B5B", "CAFE AU LAIT": "#A67B5B",
                        "GR": "#DAA520", "GOLD": "#DAA520", "GOLDEN": "#DAA520",
                        "F": "#D2B48C", "FAWN": "#D2B48C",
                        "SBL": "#D2691E", "SABLE": "#D2691E",
                        "BRN": "#CD853F", "BRINDLE": "#8B7355",
                        "MERLE": "#9FB6CD",
                        "PARTI": "#ffffff",
                        "TAN": "#D2B48C",
                        "BEIGE": "#F5F5DC",
                    }
                    _c = (anc.color or "").strip().upper()
                    color_dot = _color_map.get(_c, "#9ca3af")
                    # 部分一致フォールバック
                    if color_dot == "#9ca3af" and _c:
                        for k, v in _color_map.items():
                            if k in _c or _c in k:
                                color_dot = v
                                break
                    ancestors_html += f"""<tr>
                        <td>{_h(label)}</td>
                        <td style="font-weight:700;">{_h(anc.name)}</td>
                        <td>{_h(anc.registration)}</td>
                        <td><span style="display:inline-block;width:16px;height:16px;border-radius:50%;background:{color_dot};border:1px solid #bbb;vertical-align:middle;margin-right:6px;"></span>{_h(anc.color)}</td>
                        <td style="font-size:0.8em;">{_h(anc.titles)}</td>
                        <td style="font-size:0.8em;">{_h(anc.dna_number)}</td>
                    </tr>"""

            coi_color = '#22c55e' if coi_result['coi_pct'] < 6.25 else '#eab308' if coi_result['coi_pct'] < 12.5 else '#ef4444'
            common_text = ""
            if coi_result['common_ancestors']:
                names = ", ".join([_h(c['name']) for c in coi_result['common_ancestors']])
                common_text = f'<p><span data-i18n="lbl_common_ancestors">共通祖先</span>: {names}</p>'
            else:
                common_text = '<p data-i18n="no_common_ancestors">3世代以内に共通祖先は検出されませんでした。</p>'

            ped_parts.append(f"""
        <div class="dog-card">
            <h2 class="section-title">{_h(ped.dog_name)}</h2>
            <div class="info-grid">
                <div><strong data-i18n="lbl_breed">犬種</strong>: {_h(ped.breed)}</div>
                <div><strong data-i18n="lbl_reg_no">登録番号</strong>: {_h(ped.registration)}</div>
                <div><strong data-i18n="lbl_sex">性別</strong>: {_h(ped.sex)}</div>
                <div><strong data-i18n="lbl_dob">生年月日</strong>: {_h(ped.dob)}</div>
                <div><strong data-i18n="lbl_colour">毛色</strong>: {_h(ped.color)}</div>
                <div><strong data-i18n="lbl_microchip">マイクロチップ</strong>: {_h(ped.microchip)}</div>
                <div><strong data-i18n="lbl_breeder">ブリーダー</strong>: {_h(ped.breeder)}</div>
                <div><strong data-i18n="lbl_owner">オーナー</strong>: {_h(ped.owner)}</div>
            </div>

            <h3 class="section-title" data-i18n="ped_3gen">3世代血統表</h3>
            <table class="results-table">
                <tr><th data-i18n="th_position">位置</th><th data-i18n="th_dog_name">犬名</th><th data-i18n="th_reg_no">登録番号</th><th data-i18n="th_colour">毛色</th><th data-i18n="th_title">タイトル</th><th data-i18n="th_dna">DNA番号</th></tr>
                {ancestors_html}
            </table>

            <h3 class="section-title" data-i18n="coi_individual">近親交配係数 (COI) — 個体分析</h3>
            <div style="text-align:center;margin:20px 0;">
                <div style="font-size:3em;font-weight:800;color:{coi_color};">{coi_result['coi_pct']:.2f}%</div>
                <div style="color:#6b7280;" data-i18n="coi_wright">Wright's COI (3世代)</div>
            </div>
            {common_text}
        </div>""")

        # Cross COI if multiple pedigrees
        cross_html = ""
        if len(pedigrees) >= 2:
            cross_result = calc_coi_cross(pedigrees[0], pedigrees[1])
            cross_color = '#22c55e' if cross_result['coi_pct'] < 6.25 else '#eab308' if cross_result['coi_pct'] < 12.5 else '#ef4444'
            cross_common = ""
            if cross_result['common_ancestors']:
                items = ""
                for c in cross_result['common_ancestors']:
                    items += f"<li>{_h(c['name'])} (<span data-i18n='lbl_sire_side'>父方</span>{c['sire_gen']}<span data-i18n='lbl_gen'>世代</span> / <span data-i18n='lbl_dam_side'>母方</span>{c['dam_gen']}<span data-i18n='lbl_gen'>世代</span> → <span data-i18n='lbl_contribution'>寄与</span>: {c['contribution']*100:.3f}%)</li>"
                cross_common = f'<h3 data-i18n="lbl_common_ancestors">共通祖先</h3><ul>{items}</ul>'
            else:
                cross_common = '<p data-i18n="no_common_detected">共通祖先は検出されませんでした。</p>'

            cross_html = f"""
        <div class="dog-card">
            <h2 class="section-title"><span data-i18n="cross_coi_title">交配COI予測</span>: {_h(pedigrees[0].dog_name)} × {_h(pedigrees[1].dog_name)}</h2>
            <div style="text-align:center;margin:20px 0;">
                <div style="font-size:3em;font-weight:800;color:{cross_color};">{cross_result['coi_pct']:.2f}%</div>
                <div style="color:#6b7280;" data-i18n="expected_puppy_coi">予想される子犬のCOI</div>
            </div>
            {cross_common}
        </div>"""

        pedigree_tab_html = f"""<div id="pedigree" class="tab-content">
    {"".join(ped_parts)}
    {cross_html}
  </div>"""

    # ── Summary card counts ──
    summary_html = ""
    if has_orivet:
        summary_html = f"""  <div class="summary-row">
    <div class="summary-card"><div class="num blue">{len(dogs)}</div><div class="label" data-i18n="sum_tested">検査頭数</div></div>
    <div class="summary-card"><div class="num green">{total_normal}</div><div class="label" data-i18n="sum_normal">ノーマル項目</div></div>
    <div class="summary-card"><div class="num yellow">{total_carrier}</div><div class="label" data-i18n="sum_carrier">キャリア項目</div></div>
    <div class="summary-card"><div class="num red">{total_positive}</div><div class="label" data-i18n="sum_positive">ポジティブ (要注意)</div></div>
    {'<div class="summary-card"><div class="num" style="color:#4a1a7a;">' + str(len(pedigrees)) + '</div><div class="label" data-i18n="sum_pedigree">血統書データ</div></div>' if has_pedigree else ''}
  </div>"""
    elif has_pedigree:
        summary_html = f"""  <div class="summary-row">
    <div class="summary-card"><div class="num" style="color:#4a1a7a;">{len(pedigrees)}</div><div class="label" data-i18n="sum_pedigree">血統書データ</div></div>
  </div>"""

    # ── Subtitle ──
    features = []
    features_en = []
    if has_orivet:
        features.append("遺伝子検査")
        features_en.append("Genetic Test")
    if has_pedigree:
        features.append("血統書")
        features.append("COI算出")
        features_en.append("Pedigree")
        features_en.append("COI Calculation")
    subtitle = " + ".join(features)
    subtitle_en = " + ".join(features_en)

    # ── Pre-build conditional sections (avoid backslash in f-string) ──
    overview_tab_button = '<div class="tab active" onclick="showTab(\'overview\')"><span data-i18n="tab_overview">全体サマリー</span></div>' if has_orivet else ''

    if has_orivet:
        overview_table_html = '<div class="dog-card"><h2 class="section-title" data-i18n="test_subjects">検査対象一覧</h2><table class="results-table"><tr><th data-i18n="th_pet_name">ペット名</th><th data-i18n="th_reg_name">登録名</th><th data-i18n="lbl_breed">犬種</th><th data-i18n="lbl_sex">性別</th><th data-i18n="lbl_dob">生年月日</th><th data-i18n="th_case_no">ケース番号</th></tr>' + overview_table_rows + '</table></div>'
        alerts_section = '<div class="dog-card"><h2 class="section-title" data-i18n="alerts_title">要注意事項</h2>' + alerts_html + '</div>'
        overview_section = '<!-- Overview Tab -->\n  <div id="overview" class="tab-content active">\n  ' + overview_table_html + '\n  ' + alerts_section + '\n  </div>'
    else:
        overview_section = ''

    auto_activate_js = '' if has_orivet else "document.querySelector('.tab')?.click();"

    # ── Full HTML ──
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Orivet Genetics Report</title>
<style>
:root {{ --pink:#e6007e; --purple:#4a1a7a; --green:#22c55e; --yellow:#eab308; --red:#ef4444; --gray:#6b7280; --bg:#f8f9fa; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Segoe UI','Hiragino Sans','Meiryo',sans-serif; background:var(--bg); color:#1f2937; line-height:1.6; }}
.container {{ max-width:1200px; margin:0 auto; padding:20px; }}
header {{ background:linear-gradient(135deg,var(--purple),var(--pink)); color:white; padding:30px 0; margin-bottom:30px; border-radius:0 0 20px 20px; }}
header .container {{ display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; }}
header h1 {{ font-size:1.8em; }}
header p {{ opacity:0.9; font-size:0.95em; }}
.badge {{ display:inline-block; background:rgba(255,255,255,0.2); padding:4px 12px; border-radius:20px; font-size:0.85em; }}
.summary-row {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:15px; margin-bottom:30px; }}
.summary-card {{ background:white; border-radius:12px; padding:20px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.06); }}
.summary-card .num {{ font-size:2em; font-weight:700; }}
.summary-card .label {{ font-size:0.85em; color:var(--gray); margin-top:4px; }}
.num.green {{ color:var(--green); }} .num.yellow {{ color:var(--yellow); }} .num.red {{ color:var(--red); }} .num.blue {{ color:#3b82f6; }}
.tabs {{ display:flex; gap:8px; margin-bottom:20px; flex-wrap:wrap; }}
.tab {{ padding:10px 20px; border-radius:10px 10px 0 0; cursor:pointer; font-weight:600; border:2px solid #e5e7eb; border-bottom:none; background:white; transition:all 0.2s; font-size:0.95em; }}
.tab:hover {{ background:#f3e8ff; }}
.tab.active {{ background:var(--purple); color:white; border-color:var(--purple); }}
.tab-content {{ display:none; }} .tab-content.active {{ display:block; }}
.dog-card {{ background:white; border-radius:16px; padding:24px; margin-bottom:24px; box-shadow:0 2px 12px rgba(0,0,0,0.06); }}
.dog-header {{ display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:15px; margin-bottom:20px; padding-bottom:16px; border-bottom:2px solid #f3f4f6; }}
.dog-name {{ font-size:1.4em; font-weight:700; color:var(--purple); }}
.dog-reg {{ font-size:0.85em; color:var(--gray); }}
.dog-meta {{ display:flex; gap:12px; flex-wrap:wrap; }}
.meta-tag {{ background:#f3f4f6; padding:4px 12px; border-radius:20px; font-size:0.82em; white-space:nowrap; }}
.meta-tag.male {{ background:#dbeafe; color:#1e40af; }} .meta-tag.female {{ background:#fce7f3; color:#be185d; }}
.section-title {{ font-size:1.1em; font-weight:700; color:var(--purple); margin:20px 0 12px; padding-left:10px; border-left:4px solid var(--pink); }}
.results-table {{ width:100%; border-collapse:separate; border-spacing:0; font-size:0.88em; }}
.results-table th {{ background:var(--purple); color:white; padding:10px 12px; text-align:left; font-weight:600; }}
.results-table th:first-child {{ border-radius:8px 0 0 0; }} .results-table th:last-child {{ border-radius:0 8px 0 0; }}
.results-table td {{ padding:10px 12px; border-bottom:1px solid #f3f4f6; vertical-align:top; }}
.results-table tr:hover td {{ background:#faf5ff; }}
.compare-table {{ width:100%; border-collapse:separate; border-spacing:0; font-size:0.85em; }}
.compare-table th {{ background:var(--purple); color:white; padding:10px; text-align:center; position:sticky; top:0; }}
.compare-table th:first-child {{ text-align:left; min-width:200px; }}
.compare-table td {{ padding:8px 10px; border-bottom:1px solid #f3f4f6; text-align:center; }}
.compare-table td:first-child {{ text-align:left; font-weight:500; }}
.compare-table tr:hover td {{ background:#faf5ff; }}
.status {{ display:inline-block; padding:3px 10px; border-radius:12px; font-size:0.82em; font-weight:600; white-space:nowrap; }}
.status.normal {{ background:#dcfce7; color:#166534; }}
.status.carrier {{ background:#fef3c7; color:#92400e; }}
.status.positive {{ background:#fee2e2; color:#991b1b; }}
.status.trait {{ background:#e0e7ff; color:#3730a3; }}
.legend {{ display:flex; gap:16px; flex-wrap:wrap; margin:16px 0; padding:12px 16px; background:white; border-radius:10px; font-size:0.85em; }}
.legend-item {{ display:flex; align-items:center; gap:6px; }}
.legend-dot {{ width:14px; height:14px; border-radius:4px; }}
.info-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:16px; font-size:0.9em; }}
.breed-warn {{ background:#fff7ed; border:1px solid #fed7aa; border-radius:10px; padding:16px; margin:12px 0; }}
.breed-warn.danger {{ background:#fef2f2; border-color:#fecaca; }}
.breed-warn .warn-title {{ font-weight:700; color:#c2410c; margin-bottom:4px; }}
.breed-warn.danger .warn-title {{ color:#dc2626; }}
.print-btn {{ background:var(--purple); color:white; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-weight:600; }}
.print-btn:hover {{ background:var(--pink); }}
@media (max-width:768px) {{ header h1 {{ font-size:1.3em; }} .dog-header {{ flex-direction:column; }} .compare-table {{ display:block; overflow-x:auto; }} .info-grid {{ grid-template-columns:1fr; }} }}
@media print {{ .tabs,.print-btn,header {{ display:none!important; }} .tab-content {{ display:block!important; page-break-inside:avoid; }} .dog-card {{ break-inside:avoid; }} }}
</style>
</head>
<body>
<header>
  <div class="container">
    <div>
      <h1>Orivet Genetics Report</h1>
      <p><span data-i18n="report_subtitle">{subtitle}</span> &nbsp;|&nbsp; <span data-i18n="generated_on">生成日</span>: {now_str}</p>
      <p><span class="badge">Orivet Genetics</span> <span class="badge" data-i18n="badge_pedigree">JKC血統書</span> <span class="badge">Wright's COI</span></p>
    </div>
    <button class="print-btn" onclick="window.print()" data-i18n="btn_print">印刷</button>
  </div>
</header>
<div class="container">
{summary_html}
  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#dcfce7;border:1px solid #166534;"></div><span data-i18n="leg_normal">ノーマル (N/N)</span></div>
    <div class="legend-item"><div class="legend-dot" style="background:#fef3c7;border:1px solid #92400e;"></div><span data-i18n="leg_carrier">キャリア (P/N)</span></div>
    <div class="legend-item"><div class="legend-dot" style="background:#fee2e2;border:1px solid #991b1b;"></div><span data-i18n="leg_positive">ポジティブ (P/P)</span></div>
    <div class="legend-item"><div class="legend-dot" style="background:#e0e7ff;border:1px solid #3730a3;"></div><span data-i18n="leg_trait">形質 (Trait)</span></div>
  </div>

  <div class="tabs">
    {overview_tab_button}
{tab_buttons}
    {compare_tab_button}
    {pedigree_tab_button}
  </div>

  {overview_section}

  <!-- Individual Dog Tabs -->
{tab_contents}

  <!-- Compare Tab -->
  {compare_tab_html}

  <!-- Pedigree + COI Tab -->
  {pedigree_tab_html}
</div>
<script>
function showTab(id) {{
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  event.target.classList.add('active');
}}

// ── Language toggle ──
var REPORT_I18N = {{
  en: Object.assign({{
    report_subtitle: "{subtitle_en}",
    generated_on: "Generated",
    badge_pedigree: "Pedigree",
    btn_print: "Print",
    sum_tested: "Dogs Tested",
    sum_normal: "Normal",
    sum_carrier: "Carrier",
    sum_positive: "Positive (Attention)",
    sum_pedigree: "Pedigree Data",
    leg_normal: "Normal (N/N)",
    leg_carrier: "Carrier (P/N)",
    leg_positive: "Positive (P/P)",
    leg_trait: "Trait",
    tab_overview: "Summary",
    tab_compare: "Comparison",
    tab_pedigree: "Pedigree + COI",
    test_subjects: "Test Subjects",
    th_pet_name: "Pet Name",
    th_reg_name: "Registered Name",
    lbl_breed: "Breed",
    lbl_sex: "Sex",
    lbl_dob: "Date of Birth",
    th_case_no: "Case No.",
    alerts_title: "Alerts",
    health_results: "Health Test Results",
    items_suffix: " items",
    th_category: "Category",
    th_test: "Test",
    th_result: "Result",
    th_detail: "Details",
    trait_results: "Coat Color & Trait Results",
    th_genotype: "Genotype",
    lbl_colour: "Color",
    lbl_positive: "Positive",
    lbl_carrier: "Carrier",
    alert_positive: "Two copies of the mutation detected. There is a risk of developing the condition. Please consult your veterinarian for appropriate care.",
    alert_carrier: "One copy of the mutation detected. Breeding with a carrier or positive individual may produce affected puppies.",
    lbl_original: "Original",
    all_clear: "All Clear",
    all_clear_desc: "All health test results are normal (no mutations detected).",
    health_compare: "Health Test Comparison",
    lbl_reg_no: "Registration No.",
    lbl_microchip: "Microchip",
    lbl_breeder: "Breeder",
    lbl_owner: "Owner",
    ped_3gen: "3-Generation Pedigree",
    th_position: "Position",
    th_dog_name: "Dog Name",
    th_reg_no: "Reg. No.",
    th_colour: "Color",
    th_title: "Titles",
    th_dna: "DNA No.",
    coi_individual: "Coefficient of Inbreeding (COI) — Individual",
    coi_wright: "Wright's COI (3 generations)",
    lbl_common_ancestors: "Common Ancestors",
    no_common_ancestors: "No common ancestors detected within 3 generations.",
    no_common_detected: "No common ancestors detected.",
    cross_coi_title: "Breeding COI Prediction",
    expected_puppy_coi: "Expected Puppy COI",
    lbl_sire_side: "Sire",
    lbl_dam_side: "Dam",
    lbl_gen: " gen",
    lbl_contribution: "Contribution"
  }}, {json.dumps(sex_i18n_en, ensure_ascii=False)}),
  ja: {{
    report_subtitle: "{subtitle}",
    generated_on: "生成日",
    badge_pedigree: "JKC血統書",
    btn_print: "印刷",
    sum_tested: "検査頭数",
    sum_normal: "ノーマル項目",
    sum_carrier: "キャリア項目",
    sum_positive: "ポジティブ (要注意)",
    sum_pedigree: "血統書データ",
    leg_normal: "ノーマル (N/N)",
    leg_carrier: "キャリア (P/N)",
    leg_positive: "ポジティブ (P/P)",
    leg_trait: "形質 (Trait)",
    tab_overview: "全体サマリー",
    tab_compare: "比較表",
    tab_pedigree: "血統書 + COI",
    test_subjects: "検査対象一覧",
    th_pet_name: "ペット名",
    th_reg_name: "登録名",
    lbl_breed: "犬種",
    lbl_sex: "性別",
    lbl_dob: "生年月日",
    th_case_no: "ケース番号",
    alerts_title: "要注意事項",
    health_results: "健康検査結果",
    items_suffix: "項目",
    th_category: "カテゴリー",
    th_test: "検査項目",
    th_result: "結果",
    th_detail: "詳細",
    trait_results: "毛色・形質検査結果",
    th_genotype: "遺伝子型",
    lbl_colour: "毛色",
    lbl_positive: "ポジティブ",
    lbl_carrier: "キャリア",
    alert_positive: "変異が2コピー検出されました。発症リスクがあります。獣医師にご相談の上、適切なケアをお願いいたします。",
    alert_carrier: "変異が1コピー検出されました。キャリアまたはポジティブの個体との交配で発症する子犬が生まれる可能性があります。",
    lbl_original: "原文",
    all_clear: "全頭クリア",
    all_clear_desc: "全ての健康検査項目でノーマル（変異なし）でした。",
    health_compare: "健康検査 比較表",
    lbl_reg_no: "登録番号",
    lbl_microchip: "マイクロチップ",
    lbl_breeder: "ブリーダー",
    lbl_owner: "オーナー",
    ped_3gen: "3世代血統表",
    th_position: "位置",
    th_dog_name: "犬名",
    th_reg_no: "登録番号",
    th_colour: "毛色",
    th_title: "タイトル",
    th_dna: "DNA番号",
    coi_individual: "近親交配係数 (COI) — 個体分析",
    coi_wright: "Wright's COI (3世代)",
    lbl_common_ancestors: "共通祖先",
    no_common_ancestors: "3世代以内に共通祖先は検出されませんでした。",
    no_common_detected: "共通祖先は検出されませんでした。",
    cross_coi_title: "交配COI予測",
    expected_puppy_coi: "予想される子犬のCOI",
    lbl_sire_side: "父方",
    lbl_dam_side: "母方",
    lbl_gen: "世代",
    lbl_contribution: "寄与"
  }}
}};

// Store per-dog sex labels for ja
(function() {{
  var jaExtra = {json.dumps({f"sex_{re.sub(r'[^a-zA-Z0-9]', '_', (d.pet_name or d.registered_name or f'犬{i+1}').lower())}": "オス" if "male" in d.sex.lower() else "メス" for i, d in enumerate(dogs)}, ensure_ascii=False)};
  Object.assign(REPORT_I18N.ja, jaExtra);
}})();

function __applyLang(lang) {{
  var dict = REPORT_I18N[lang];
  if (!dict) return;
  document.querySelectorAll('[data-i18n]').forEach(function(el) {{
    var key = el.getAttribute('data-i18n');
    if (dict[key] !== undefined) el.innerHTML = dict[key];
  }});
  document.documentElement.lang = lang;
}}

// Expose for parent iframe access
document.__applyLang = __applyLang;
window.__applyLang = __applyLang;

// Auto-apply saved language
(function() {{
  try {{
    var lang = (window.parent !== window) ? null : localStorage.getItem('appLang');
    if (lang) __applyLang(lang);
  }} catch(e) {{}}
}})();

{auto_activate_js}
</script>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n統合HTMLレポート出力: {output_path}")


# ████████████████████████████████████████████████████████████
# PART 4: Excel出力
# ████████████████████████████████████████████████████████████

def generate_excel(dogs: list, pedigrees: list, output_path: str):
    """Excel スプレッドシートを生成"""
    if not HAS_OPENPYXL:
        print("  openpyxl が未インストールのためExcel出力をスキップします。")
        return

    wb = Workbook()

    header_font = Font(bold=True, color="FFFFFF", size=11, name="Arial")
    header_fill = PatternFill("solid", fgColor="4A1A7A")
    normal_fill = PatternFill("solid", fgColor="DCFCE7")
    carrier_fill = PatternFill("solid", fgColor="FEF3C7")
    positive_fill = PatternFill("solid", fgColor="FEE2E2")
    trait_fill = PatternFill("solid", fgColor="E0E7FF")
    border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB'),
    )

    def style_header(ws, row, cols):
        for col in range(1, cols + 1):
            cell = ws.cell(row=row, column=col)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = border

    def style_cell(ws, row, col, status=None):
        cell = ws.cell(row=row, column=col)
        cell.border = border
        cell.alignment = Alignment(vertical='top', wrap_text=True)
        if status == "normal":
            cell.fill = normal_fill
        elif status == "carrier":
            cell.fill = carrier_fill
        elif status == "positive":
            cell.fill = positive_fill
        elif status == "trait":
            cell.fill = trait_fill

    # ── Sheet 1: Overview ──
    if dogs:
        ws = wb.active
        ws.title = "概要"
        headers = ["ペット名", "登録名", "犬種", "性別", "生年月日", "マイクロチップ", "ケース番号", "検査日"]
        for c, h in enumerate(headers, 1):
            ws.cell(row=1, column=c, value=h)
        style_header(ws, 1, len(headers))

        for r, dog in enumerate(dogs, 2):
            data = [dog.pet_name, dog.registered_name, dog.breed, dog.sex, dog.dob, dog.microchip, dog.case_number, dog.test_date]
            for c, val in enumerate(data, 1):
                ws.cell(row=r, column=c, value=val)
                style_cell(ws, r, c)

        for col_letter in ['A','B','C','D','E','F','G','H']:
            ws.column_dimensions[col_letter].width = 22

        # ── Per-dog sheets ──
        for dog in dogs:
            name = (dog.pet_name or dog.registered_name or "犬")[:30]
            ws = wb.create_sheet(title=name)

            ws.cell(row=1, column=1, value="ペット名").font = Font(bold=True, name="Arial")
            ws.cell(row=1, column=2, value=dog.pet_name)
            ws.cell(row=2, column=1, value="登録名").font = Font(bold=True, name="Arial")
            ws.cell(row=2, column=2, value=dog.registered_name)
            ws.cell(row=3, column=1, value="犬種").font = Font(bold=True, name="Arial")
            ws.cell(row=3, column=2, value=dog.breed)
            ws.cell(row=4, column=1, value="性別").font = Font(bold=True, name="Arial")
            ws.cell(row=4, column=2, value=dog.sex)
            ws.cell(row=5, column=1, value="生年月日").font = Font(bold=True, name="Arial")
            ws.cell(row=5, column=2, value=dog.dob)
            ws.cell(row=6, column=1, value="マイクロチップ").font = Font(bold=True, name="Arial")
            ws.cell(row=6, column=2, value=dog.microchip)
            ws.cell(row=7, column=1, value="ケース番号").font = Font(bold=True, name="Arial")
            ws.cell(row=7, column=2, value=dog.case_number)

            row = 9
            ws.cell(row=row, column=1, value="【健康検査結果】").font = Font(bold=True, size=12, color="4A1A7A", name="Arial")
            row = 10
            for c, h in enumerate(["カテゴリー", "検査項目", "検査項目(英語)", "遺伝子型", "ステータス", "詳細"], 1):
                ws.cell(row=row, column=c, value=h)
            style_header(ws, row, 6)

            for r_idx, result in enumerate(dog.health_results):
                r = row + 1 + r_idx
                ws.cell(row=r, column=1, value=sanitize_for_excel(result.category))
                ws.cell(row=r, column=2, value=sanitize_for_excel(result.japanese_name or result.test_name))
                ws.cell(row=r, column=3, value=sanitize_for_excel(result.test_name))
                ws.cell(row=r, column=4, value=sanitize_for_excel(result.genotype))
                status_jp = {"normal": "ノーマル", "carrier": "キャリア", "positive": "ポジティブ"}.get(result.status, result.status)
                ws.cell(row=r, column=5, value=status_jp)
                ws.cell(row=r, column=6, value=sanitize_for_excel(result.result_text[:150]))
                for c in range(1, 7):
                    style_cell(ws, r, c, result.status)

            row = row + len(dog.health_results) + 3
            ws.cell(row=row, column=1, value="【毛色・形質検査結果】").font = Font(bold=True, size=12, color="4A1A7A", name="Arial")
            row += 1
            for c, h in enumerate(["検査項目", "検査項目(英語)", "遺伝子型", "詳細"], 1):
                ws.cell(row=row, column=c, value=h)
            style_header(ws, row, 4)

            for r_idx, result in enumerate(dog.trait_results):
                r = row + 1 + r_idx
                ws.cell(row=r, column=1, value=sanitize_for_excel(result.japanese_name or result.test_name))
                ws.cell(row=r, column=2, value=sanitize_for_excel(result.test_name))
                ws.cell(row=r, column=3, value=sanitize_for_excel(result.genotype))
                ws.cell(row=r, column=4, value=sanitize_for_excel(result.result_text[:150]))
                for c in range(1, 5):
                    style_cell(ws, r, c, "trait")

            ws.column_dimensions['A'].width = 28
            ws.column_dimensions['B'].width = 35
            ws.column_dimensions['C'].width = 35
            ws.column_dimensions['D'].width = 18
            ws.column_dimensions['E'].width = 14
            ws.column_dimensions['F'].width = 60

        # ── Comparison Sheet ──
        if len(dogs) > 1:
            ws = wb.create_sheet(title="比較表")
            headers = ["検査項目"] + [d.pet_name or d.registered_name for d in dogs]
            for c, h in enumerate(headers, 1):
                ws.cell(row=1, column=c, value=h)
            style_header(ws, 1, len(headers))

            all_tests = {}
            for dog in dogs:
                for r in dog.health_results:
                    key = r.test_name
                    if key not in all_tests:
                        all_tests[key] = r.japanese_name or r.test_name

            row = 2
            for test_key, jp_name in all_tests.items():
                ws.cell(row=row, column=1, value=sanitize_for_excel(jp_name))
                style_cell(ws, row, 1)
                for d_idx, dog in enumerate(dogs):
                    col = d_idx + 2
                    found = False
                    for r in dog.health_results:
                        if r.test_name == test_key:
                            ws.cell(row=row, column=col, value=r.genotype)
                            ws.cell(row=row, column=col).alignment = Alignment(horizontal='center')
                            style_cell(ws, row, col, r.status)
                            found = True
                            break
                    if not found:
                        ws.cell(row=row, column=col, value="—")
                        style_cell(ws, row, col)
                row += 1

            ws.column_dimensions['A'].width = 40
            for i in range(len(dogs)):
                ws.column_dimensions[chr(66 + i)].width = 18

    # ── Pedigree Sheet ──
    if pedigrees:
        if not dogs:
            ws = wb.active
            ws.title = "血統書"
        else:
            ws = wb.create_sheet(title="血統書")

        row = 1
        for ped in pedigrees:
            ws.cell(row=row, column=1, value=f"【{ped.dog_name}】").font = Font(bold=True, size=14, color="4A1A7A", name="Arial")
            row += 1
            info_items = [
                ("犬種", ped.breed), ("登録番号", ped.registration),
                ("性別", ped.sex), ("生年月日", ped.dob),
                ("毛色", ped.color), ("マイクロチップ", ped.microchip),
                ("ブリーダー", ped.breeder), ("オーナー", ped.owner),
            ]
            for label, val in info_items:
                ws.cell(row=row, column=1, value=label).font = Font(bold=True, name="Arial")
                ws.cell(row=row, column=2, value=val)
                row += 1

            row += 1
            for c, h in enumerate(["位置", "犬名", "登録番号", "毛色", "タイトル", "DNA番号"], 1):
                ws.cell(row=row, column=c, value=h)
            style_header(ws, row, 6)

            for label, anc in ped.all_ancestors():
                if anc:
                    row += 1
                    ws.cell(row=row, column=1, value=label)
                    ws.cell(row=row, column=2, value=anc.name)
                    ws.cell(row=row, column=3, value=anc.registration)
                    ws.cell(row=row, column=4, value=anc.color)
                    ws.cell(row=row, column=5, value=anc.titles)
                    ws.cell(row=row, column=6, value=anc.dna_number)
                    for c in range(1, 7):
                        style_cell(ws, row, c)

            # COI
            coi_result = calc_coi_3gen(ped)
            row += 2
            ws.cell(row=row, column=1, value="近親交配係数 (COI)").font = Font(bold=True, size=12, color="4A1A7A", name="Arial")
            row += 1
            ws.cell(row=row, column=1, value="Wright's COI (3世代)")
            ws.cell(row=row, column=2, value=f"{coi_result['coi_pct']:.2f}%")
            if coi_result['coi_pct'] > 6.25:
                ws.cell(row=row, column=2).font = Font(bold=True, color="FF0000", name="Arial")
            else:
                ws.cell(row=row, column=2).font = Font(bold=True, color="22C55E", name="Arial")

            if coi_result['common_ancestors']:
                row += 1
                ws.cell(row=row, column=1, value="共通祖先")
                names = ", ".join([c['name'] for c in coi_result['common_ancestors']])
                ws.cell(row=row, column=2, value=names)

            row += 3

        ws.column_dimensions['A'].width = 28
        ws.column_dimensions['B'].width = 35
        ws.column_dimensions['C'].width = 22
        ws.column_dimensions['D'].width = 10
        ws.column_dimensions['E'].width = 40
        ws.column_dimensions['F'].width = 18

    wb.save(output_path)
    print(f"Excel レポート出力: {output_path}")


# ████████████████████████████████████████████████████████████
# PART 5: メインエントリポイント
# ████████████████████████████████████████████████████████████

def collect_pdf_files(args: list) -> list:
    """引数からPDFファイルリストを収集"""
    pdf_files = []
    for arg in args:
        if arg in ('--output', '-o', '--pedigree', '-p'):
            continue
        if os.path.isdir(arg):
            pdf_files.extend(glob.glob(os.path.join(arg, "*.pdf")))
            pdf_files.extend(glob.glob(os.path.join(arg, "*.PDF")))
        elif os.path.isfile(arg) and arg.lower().endswith('.pdf'):
            pdf_files.append(arg)
        elif '*' in arg or '?' in arg:
            pdf_files.extend(glob.glob(arg))
    return sorted(set(pdf_files))


def collect_pedigree_args(args: list) -> list:
    """血統書関連の引数を収集"""
    pedigree_sources = []
    i = 0
    while i < len(args):
        if args[i] in ('--pedigree', '-p') and i + 1 < len(args):
            pedigree_sources.append(args[i + 1])
            i += 2
        else:
            i += 1
    return pedigree_sources


def get_output_dir(args: list) -> str:
    """出力ディレクトリを取得"""
    for i, arg in enumerate(args):
        if arg in ('--output', '-o') and i + 1 < len(args):
            return args[i + 1]
    return os.getcwd()


def print_usage():
    print("""
使い方:
  python poodle_genetics.py <コマンド> [オプション]

コマンド:
  orivet <PDFファイル...>              Orivet遺伝子検査PDFを解析
  pedigree <写真 or 犬名>             血統書解析 + COI算出
  all <PDFファイル...> -p <犬名>       遺伝子 + 血統書の統合レポート
  demo                                 デモ実行 (Sevenの全データ)

オプション:
  -o, --output <ディレクトリ>   出力先ディレクトリ
  -p, --pedigree <犬名/写真>    血統書データ (複数指定可)

例:
  python poodle_genetics.py orivet *.pdf -o ./output
  python poodle_genetics.py pedigree seven -o ./output
  python poodle_genetics.py all *.pdf -p seven -o ./output
  python poodle_genetics.py demo
""")


def main():
    print("=" * 60)
    print("  Orivet 遺伝子解析ツール — 全犬種対応")
    print("=" * 60)

    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()
    remaining_args = sys.argv[2:]

    output_dir = get_output_dir(remaining_args)
    os.makedirs(output_dir, exist_ok=True)

    dogs = []       # Orivet解析結果
    pedigrees = []  # 血統書データ

    if command == "demo":
        # デモモード: PDFがあれば解析、なければサンプルメッセージ
        print("\n[デモモード] Sevenの既知データで実行します。")

        # Try to parse PDFs in uploads
        upload_dir = "/sessions/sleepy-practical-cannon/mnt/uploads"
        if os.path.isdir(upload_dir):
            pdf_files = glob.glob(os.path.join(upload_dir, "*.pdf")) + glob.glob(os.path.join(upload_dir, "*.PDF"))
            if pdf_files and HAS_PDFPLUMBER:
                print(f"\n{len(pdf_files)} 個のPDFファイルを検出。解析中...")
                for pdf_path in pdf_files:
                    dog = parse_pdf(pdf_path)
                    if dog:
                        dogs.append(dog)
                if dogs:
                    print(f"  → {len(dogs)} 頭分のOrivetデータを解析しました。")

        # Add Seven's pedigree
        pedigrees.append(KNOWN_PEDIGREES["seven"])

    elif command == "orivet":
        if not HAS_PDFPLUMBER:
            print("\nエラー: pdfplumber が必要です。\n  pip install pdfplumber")
            sys.exit(1)

        # Filter out option flags from file arguments
        file_args = [a for a in remaining_args if a not in ('--output', '-o') and not (len(remaining_args) > 1 and remaining_args[remaining_args.index(a)-1] in ('--output', '-o') if a in remaining_args else False)]
        pdf_files = collect_pdf_files(remaining_args)

        if not pdf_files:
            pdf_files = glob.glob("*.pdf") + glob.glob("*.PDF")

        if not pdf_files:
            print("\nエラー: PDFファイルが見つかりません。")
            sys.exit(1)

        print(f"\n{len(pdf_files)} 個のPDFファイルを検出。\n")
        for pdf_path in pdf_files:
            dog = parse_pdf(pdf_path)
            if dog:
                dogs.append(dog)

        if not dogs:
            print("\nエラー: 解析可能なOrivetレポートが見つかりませんでした。")
            sys.exit(1)

    elif command == "pedigree":
        pedigree_sources = remaining_args
        # Remove output flag args
        clean_sources = []
        skip_next = False
        for a in pedigree_sources:
            if skip_next:
                skip_next = False
                continue
            if a in ('--output', '-o'):
                skip_next = True
                continue
            clean_sources.append(a)

        if not clean_sources:
            clean_sources = ["seven"]

        for src in clean_sources:
            if src.lower() in KNOWN_PEDIGREES:
                pedigrees.append(KNOWN_PEDIGREES[src.lower()])
                print(f"  → 既知の血統書データ: {KNOWN_PEDIGREES[src.lower()].dog_name}")
            elif os.path.isfile(src):
                print(f"\n画像を解析中: {src}")
                text = try_ocr(src)
                if text:
                    ped = parse_jkc_pedigree_text(text)
                    if ped and ped.dog_name:
                        pedigrees.append(ped)
                        print(f"  → {ped.dog_name} の血統書を解析しました。")
                    else:
                        print(f"  → 血統書データの解析に失敗しました。")
            else:
                print(f"  → 不明な引数: {src}")

    elif command == "all":
        # 統合モード
        if HAS_PDFPLUMBER:
            pdf_files = collect_pdf_files(remaining_args)
            if pdf_files:
                print(f"\n{len(pdf_files)} 個のPDFファイルを検出。\n")
                for pdf_path in pdf_files:
                    dog = parse_pdf(pdf_path)
                    if dog:
                        dogs.append(dog)

        # Pedigree sources
        ped_sources = collect_pedigree_args(remaining_args)
        if not ped_sources:
            ped_sources = ["seven"]

        for src in ped_sources:
            if src.lower() in KNOWN_PEDIGREES:
                pedigrees.append(KNOWN_PEDIGREES[src.lower()])
            elif os.path.isfile(src):
                text = try_ocr(src)
                if text:
                    ped = parse_jkc_pedigree_text(text)
                    if ped and ped.dog_name:
                        pedigrees.append(ped)

    else:
        print(f"\n不明なコマンド: {command}")
        print_usage()
        sys.exit(1)

    if not dogs and not pedigrees:
        print("\nエラー: 解析可能なデータがありません。")
        sys.exit(1)

    # ── 出力 ──
    print(f"\n{'='*40}")
    if dogs:
        print(f"Orivet解析: {len(dogs)} 頭")
    if pedigrees:
        print(f"血統書データ: {len(pedigrees)} 頭")
        for ped in pedigrees:
            result = calc_coi_3gen(ped)
            print(f"  {ped.dog_name}: COI = {result['coi_pct']:.2f}%")

    html_path = os.path.join(output_dir, "orivet_report.html")
    xlsx_path = os.path.join(output_dir, "orivet_report.xlsx")

    generate_unified_html(dogs, pedigrees, html_path)
    generate_excel(dogs, pedigrees, xlsx_path)

    print(f"\n完了! 以下のファイルが生成されました:")
    print(f"  HTML: {html_path}")
    print(f"  Excel: {xlsx_path}")
    print()


if __name__ == "__main__":
    main()
