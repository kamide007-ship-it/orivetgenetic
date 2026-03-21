#!/usr/bin/env python3
"""
プードル遺伝子総合解析ツール (Orivet Genetics Suite)
=====================================================
Orivet遺伝子検査PDFの自動解析 + JKC血統書OCR + COI算出を
1本にまとめた統合ツール。

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
    - poodle_report.html  (統合HTMLレポート: 遺伝子 + 血統 + COI)
    - poodle_report.xlsx  (Excelスプレッドシート)

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


def extract_genotype(result_text: str) -> str:
    """結果テキストから遺伝子型を抽出"""
    m = re.search(r'\b([PN])/([PN])\b', result_text)
    if m:
        return f"{m.group(1)}/{m.group(2)}"

    patterns = [
        r'(at/at|ay/at|ay/ay|a/a|aw/at)',
        r'(Bb|BB|bb)\b',
        r'(D/D|D/d|d/d)\b',
        r'(E/e|e/e|E/E|Em/E|Em/e)\b',
        r'(En/En|EM/EM)',
        r'(K/K|KB/ky|KB/kbr|ky/ky|kbr/ky)',
        r'(m/m|M/m|M/M)',
        r'(Cu/Cu|Cu/N|N/N)',
        r'(F/F|F/f|f/f)',
        r'(S/S|S/sp|sp/sp)',
        r'(BL/BL|BL/bs|bs/bs)',
    ]
    for p in patterns:
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

            test_name = re.sub(r'^[\s\uf0b7\u2022\u25cf]+', '', test_name)
            test_name = re.sub(r'\s+', ' ', test_name).strip()

            if test_name and len(test_name) > 2:
                status = classify_result(result_text)
                genotype = extract_genotype(result_text)
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
        ("Pied", r"Pied\s*\(BOTH\s+SINE"),
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
                        if next_line and not re.search(r'^[A-Z]\s+Locus|^Breed|^Owner|^Microchip|^Pied|^Brown|^Curly|^Furnish|^Chondro', next_line):
                            result_text += " " + next_line
                        else:
                            break

                result_clean = re.sub(pattern, '', result_text, flags=re.IGNORECASE).strip()
                result_clean = re.sub(r'^[\s\-–:]+', '', result_clean).strip()

                genotype = extract_genotype(result_text)
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


# ████████████████████████████████████████████████████████████
# PART 2: 血統書 OCR + COI 算出
# ████████████████████████████████████████████████████████████

def try_ocr(image_path: str) -> str:
    """画像からテキストを抽出（Tesseract OCR）"""
    if not HAS_OCR:
        print("  pytesseract が未インストールです。")
        print("  pip install pytesseract Pillow")
        print("  + Tesseract OCR本体: sudo apt install tesseract-ocr tesseract-ocr-jpn")
        return ""
    try:
        img = Image.open(image_path)
        # HEIC/WEBP等をRGBに変換してTesseractが処理できるようにする
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        text = pytesseract.image_to_string(img, lang='jpn+eng')
        return text
    except Exception as e:
        print(f"  OCRエラー: {e}")
        return ""


def parse_jkc_pedigree_text(text: str) -> Optional[Pedigree]:
    """OCRテキストからJKC血統書を解析"""
    if not text:
        return None

    ped = Pedigree()

    m = re.search(r'(?:Name of Dog|犬名)\s*\n?\s*(.+?)(?:\n|$)', text)
    if m:
        ped.dog_name = m.group(1).strip()

    m = re.search(r'(JKC-PT\s*-?\s*\d+/\d+)', text)
    if m:
        ped.registration = m.group(1)

    if re.search(r'MALE|オス|牡', text):
        ped.sex = "MALE"
    elif re.search(r'FEMALE|メス|牝', text):
        ped.sex = "FEMALE"

    m = re.search(r'(?:色|Color)\s*(\w+)', text)
    if m:
        ped.color = m.group(1)

    m = re.search(r'(\d{4}年\s*\d{1,2}月\s*\d{1,2}日)', text)
    if m:
        ped.dob = m.group(1)

    m = re.search(r'ID\s*(392\d{12,15})', text)
    if m:
        ped.microchip = m.group(1)

    lines = text.split('\n')
    ancestors = {}
    for i, line in enumerate(lines):
        m = re.match(r'\s*(\d{1,2})\s*[\|\{]?\s*(.+)', line)
        if m:
            num = int(m.group(1))
            name_text = m.group(2).strip()
            name_m = re.search(r'((?:SMASH|IMPACT|BEATRIX)\s+JP\s+[\w\s]+)', name_text, re.IGNORECASE)
            if name_m:
                ancestors[num] = name_m.group(1).strip()

    pos_map = {
        1: "sire", 2: "dam", 3: "ss", 4: "sd", 5: "ds", 6: "dd",
        7: "sss", 8: "ssd", 9: "sds", 10: "sdd",
        11: "dss", 12: "dsd", 13: "dds", 14: "ddd"
    }
    for num, name in ancestors.items():
        if num in pos_map:
            setattr(ped, pos_map[num], Ancestor(position=pos_map[num], name=name))

    return ped


def calc_coi_3gen(ped: Pedigree) -> dict:
    """3世代の血統データからCOIを算出"""
    sire_ancestors = []
    dam_ancestors = []

    def add_if_exists(lst, ancestor, gen):
        if ancestor and ancestor.name:
            lst.append({"name": ancestor.name.strip().upper(), "gen": gen})

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
        if ped.dog_name:
            lst.append({"name": ped.dog_name.strip().upper(), "gen": base_gen})
        for anc, gen in ancestors_data:
            if anc and anc.name:
                lst.append({"name": anc.name.strip().upper(), "gen": base_gen + gen})

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

def sanitize_for_excel(text: str) -> str:
    """Excelで使えない文字を除去"""
    if not text:
        return text
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)


def status_badge(status: str, text: str) -> str:
    return f'<span class="status {status}">{text}</span>'


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

    for idx, dog in enumerate(dogs):
        name = dog.pet_name or dog.registered_name or f"犬{idx+1}"
        safe_id = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())

        tab_buttons += f'    <div class="tab" onclick="showTab(\'{safe_id}\')">{name}</div>\n'

        sex_class = "male" if "male" in dog.sex.lower() else "female"
        sex_label = "オス" if "male" in dog.sex.lower() else "メス"

        health_rows = ""
        for r in dog.health_results:
            display_name = r.japanese_name if r.japanese_name else r.test_name
            badge = status_badge(r.status, r.genotype if r.genotype else r.status.upper())
            health_rows += f"""        <tr>
          <td>{r.category}</td>
          <td>{display_name}<br><small style="color:#6b7280">{r.test_name}</small></td>
          <td>{badge}</td>
          <td style="font-size:0.85em">{r.result_text[:120]}</td>
        </tr>\n"""

        trait_rows = ""
        for r in dog.trait_results:
            display_name = r.japanese_name if r.japanese_name else r.test_name
            badge = status_badge("trait", r.genotype if r.genotype else "—")
            trait_rows += f"""        <tr>
          <td>{display_name}<br><small style="color:#6b7280">{r.test_name}</small></td>
          <td>{badge}</td>
          <td style="font-size:0.85em">{r.result_text[:150]}</td>
        </tr>\n"""

        tab_contents += f"""
  <div id="{safe_id}" class="tab-content">
    <div class="dog-card">
      <div class="dog-header">
        <div>
          <div class="dog-name">{name}</div>
          <div class="dog-reg">{dog.registered_name} — {dog.case_number}</div>
        </div>
        <div class="dog-meta">
          <span class="meta-tag {sex_class}">{sex_label} ({dog.sex})</span>
          <span class="meta-tag">{dog.breed}</span>
          <span class="meta-tag">{dog.dob}</span>
          {'<span class="meta-tag">MC: ' + dog.microchip + '</span>' if dog.microchip else ''}
          {'<span class="meta-tag">毛色: ' + dog.colour + '</span>' if dog.colour else ''}
        </div>
      </div>

      <h3 class="section-title">健康検査結果 ({len(dog.health_results)}項目)</h3>
      <table class="results-table">
        <tr><th>カテゴリー</th><th>検査項目</th><th>結果</th><th>詳細</th></tr>
{health_rows}
      </table>

      <h3 class="section-title">毛色・形質検査結果 ({len(dog.trait_results)}項目)</h3>
      <table class="results-table">
        <tr><th>検査項目</th><th>遺伝子型</th><th>詳細</th></tr>
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

        compare_header = "<th>検査項目</th>"
        for dog in dogs:
            compare_header += f"<th>{dog.pet_name or dog.registered_name}</th>"

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

        compare_tab_button = '<div class="tab" onclick="showTab(\'compare\')">比較表</div>'
        compare_tab_html = f"""<div id="compare" class="tab-content">
    <div class="dog-card">
      <h2 class="section-title">健康検査 比較表</h2>
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
            name = dog.pet_name or dog.registered_name
            display_name = r.japanese_name if r.japanese_name else r.test_name
            if r.status == "positive":
                alerts_html += f"""      <div class="breed-warn danger">
        <div class="warn-title">{display_name} — ポジティブ (P/P): {name}</div>
        <p>変異が2コピー検出されました。発症リスクがあります。獣医師にご相談の上、適切なケアをお願いいたします。</p>
        <p><small>原文: {r.result_text[:200]}</small></p>
      </div>\n"""
            elif r.status == "carrier":
                alerts_html += f"""      <div class="breed-warn">
        <div class="warn-title">{display_name} — キャリア (P/N): {name}</div>
        <p>変異が1コピー検出されました。キャリアまたはポジティブの個体との交配で発症する子犬が生まれる可能性があります。</p>
      </div>\n"""

    if not alerts_html and has_orivet:
        alerts_html = '<div class="breed-warn" style="background:#dcfce7;border-color:#86efac;"><div class="warn-title" style="color:#166534;">全頭クリア</div><p>全ての健康検査項目でノーマル（変異なし）でした。</p></div>'

    # ── Overview table rows ──
    overview_table_rows = ""
    for d in dogs:
        overview_table_rows += f"<tr><td><strong>{d.pet_name}</strong></td><td>{d.registered_name}</td><td>{d.breed}</td><td>{d.sex}</td><td>{d.dob}</td><td>{d.case_number}</td></tr>\n"

    # ── Pedigree section ──
    pedigree_tab_button = ""
    pedigree_tab_html = ""
    if has_pedigree:
        pedigree_tab_button = '<div class="tab" onclick="showTab(\'pedigree\')">血統書 + COI</div>'

        ped_parts = []
        for ped in pedigrees:
            coi_result = calc_coi_3gen(ped)

            ancestors_html = ""
            for label, anc in ped.all_ancestors():
                if anc:
                    color_dot = {"BLK": "#1a1a1a", "WH": "#e5e7eb", "BR": "#8B4513", "RED": "#CD5C5C"}.get(anc.color, "#9ca3af")
                    ancestors_html += f"""<tr>
                        <td>{label}</td>
                        <td style="font-weight:700;">{anc.name}</td>
                        <td>{anc.registration}</td>
                        <td><span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{color_dot};border:1px solid #999;vertical-align:middle;margin-right:4px;"></span>{anc.color}</td>
                        <td style="font-size:0.8em;">{anc.titles}</td>
                        <td style="font-size:0.8em;">{anc.dna_number}</td>
                    </tr>"""

            coi_color = '#22c55e' if coi_result['coi_pct'] < 6.25 else '#eab308' if coi_result['coi_pct'] < 12.5 else '#ef4444'
            common_text = ""
            if coi_result['common_ancestors']:
                names = ", ".join([c['name'] for c in coi_result['common_ancestors']])
                common_text = f"<p>共通祖先: {names}</p>"
            else:
                common_text = "<p>3世代以内に共通祖先は検出されませんでした。</p>"

            ped_parts.append(f"""
        <div class="dog-card">
            <h2 class="section-title">{ped.dog_name}</h2>
            <div class="info-grid">
                <div><strong>犬種:</strong> {ped.breed}</div>
                <div><strong>登録番号:</strong> {ped.registration}</div>
                <div><strong>性別:</strong> {ped.sex}</div>
                <div><strong>生年月日:</strong> {ped.dob}</div>
                <div><strong>毛色:</strong> {ped.color}</div>
                <div><strong>マイクロチップ:</strong> {ped.microchip}</div>
                <div><strong>ブリーダー:</strong> {ped.breeder}</div>
                <div><strong>オーナー:</strong> {ped.owner}</div>
            </div>

            <h3 class="section-title">3世代血統表</h3>
            <table class="results-table">
                <tr><th>位置</th><th>犬名</th><th>登録番号</th><th>毛色</th><th>タイトル</th><th>DNA番号</th></tr>
                {ancestors_html}
            </table>

            <h3 class="section-title">近親交配係数 (COI) — 個体分析</h3>
            <div style="text-align:center;margin:20px 0;">
                <div style="font-size:3em;font-weight:800;color:{coi_color};">{coi_result['coi_pct']:.2f}%</div>
                <div style="color:#6b7280;">Wright's COI (3世代)</div>
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
                    items += f"<li>{c['name']} (父方{c['sire_gen']}世代 / 母方{c['dam_gen']}世代 → 寄与: {c['contribution']*100:.3f}%)</li>"
                cross_common = f"<h3>共通祖先</h3><ul>{items}</ul>"
            else:
                cross_common = "<p>共通祖先は検出されませんでした。</p>"

            cross_html = f"""
        <div class="dog-card">
            <h2 class="section-title">交配COI予測: {pedigrees[0].dog_name} × {pedigrees[1].dog_name}</h2>
            <div style="text-align:center;margin:20px 0;">
                <div style="font-size:3em;font-weight:800;color:{cross_color};">{cross_result['coi_pct']:.2f}%</div>
                <div style="color:#6b7280;">予想される子犬のCOI</div>
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
    <div class="summary-card"><div class="num blue">{len(dogs)}</div><div class="label">検査頭数</div></div>
    <div class="summary-card"><div class="num green">{total_normal}</div><div class="label">ノーマル項目</div></div>
    <div class="summary-card"><div class="num yellow">{total_carrier}</div><div class="label">キャリア項目</div></div>
    <div class="summary-card"><div class="num red">{total_positive}</div><div class="label">ポジティブ (要注意)</div></div>
    {'<div class="summary-card"><div class="num" style="color:#4a1a7a;">' + str(len(pedigrees)) + '</div><div class="label">血統書データ</div></div>' if has_pedigree else ''}
  </div>"""
    elif has_pedigree:
        summary_html = f"""  <div class="summary-row">
    <div class="summary-card"><div class="num" style="color:#4a1a7a;">{len(pedigrees)}</div><div class="label">血統書データ</div></div>
  </div>"""

    # ── Subtitle ──
    features = []
    if has_orivet:
        features.append("遺伝子検査")
    if has_pedigree:
        features.append("血統書")
        features.append("COI算出")
    subtitle = " + ".join(features)

    # ── Pre-build conditional sections (avoid backslash in f-string) ──
    overview_tab_button = '<div class="tab active" onclick="showTab(\'overview\')">全体サマリー</div>' if has_orivet else ''

    if has_orivet:
        overview_table_html = '<div class="dog-card"><h2 class="section-title">検査対象一覧</h2><table class="results-table"><tr><th>ペット名</th><th>登録名</th><th>犬種</th><th>性別</th><th>生年月日</th><th>ケース番号</th></tr>' + overview_table_rows + '</table></div>'
        alerts_section = '<div class="dog-card"><h2 class="section-title">要注意事項</h2>' + alerts_html + '</div>'
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
<title>プードル遺伝子総合レポート</title>
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
      <h1>プードル遺伝子総合レポート</h1>
      <p>{subtitle} &nbsp;|&nbsp; 生成日: {now_str}</p>
      <p><span class="badge">Orivet Genetics</span> <span class="badge">JKC血統書</span> <span class="badge">Wright's COI</span></p>
    </div>
    <button class="print-btn" onclick="window.print()">印刷</button>
  </div>
</header>
<div class="container">
{summary_html}
  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#dcfce7;border:1px solid #166534;"></div>ノーマル (N/N)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#fef3c7;border:1px solid #92400e;"></div>キャリア (P/N)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#fee2e2;border:1px solid #991b1b;"></div>ポジティブ (P/P)</div>
    <div class="legend-item"><div class="legend-dot" style="background:#e0e7ff;border:1px solid #3730a3;"></div>形質 (Trait)</div>
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
    print("  プードル遺伝子総合解析ツール (Orivet Genetics Suite)")
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

    html_path = os.path.join(output_dir, "poodle_report.html")
    xlsx_path = os.path.join(output_dir, "poodle_report.xlsx")

    generate_unified_html(dogs, pedigrees, html_path)
    generate_excel(dogs, pedigrees, xlsx_path)

    print(f"\n完了! 以下のファイルが生成されました:")
    print(f"  HTML: {html_path}")
    print(f"  Excel: {xlsx_path}")
    print()


if __name__ == "__main__":
    main()
