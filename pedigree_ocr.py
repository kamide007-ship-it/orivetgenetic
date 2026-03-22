#!/usr/bin/env python3
"""
血統書 写真OCR解析ツール（全犬種・全団体対応）
==============================================
各種血統証明書（JKC・ALAJ・AKC等）の写真から
血統情報を自動で読み取り、近親交配係数(COI)を算出します。
フォーマットを自動判定し、適切なパーサーを選択します。

使い方:
    python pedigree_ocr.py pedigree_photo.jpg
    python pedigree_ocr.py pedigree1.jpg pedigree2.jpg  (複数犬のCOI比較)

出力:
    - pedigree_report.html  (血統書データ + COI算出結果)

必要ライブラリ:
    pip install pytesseract Pillow
    # + Tesseract OCR本体のインストールが必要
    # Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-jpn
    # Mac: brew install tesseract tesseract-lang
"""

import sys
import os
import re
import json
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

# ============================================================
# データ構造
# ============================================================

@dataclass
class Ancestor:
    """血統書上の1頭分"""
    position: str = ""       # "sire", "dam", "ss", "sd", etc.
    name: str = ""
    registration: str = ""   # JKC-PT番号
    titles: str = ""         # CH等のタイトル
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
    # 3世代血統
    sire: Optional[Ancestor] = None      # 父
    dam: Optional[Ancestor] = None       # 母
    ss: Optional[Ancestor] = None        # 父方祖父
    sd: Optional[Ancestor] = None        # 父方祖母
    ds: Optional[Ancestor] = None        # 母方祖父
    dd: Optional[Ancestor] = None        # 母方祖母
    sss: Optional[Ancestor] = None       # 父方曾祖父1
    ssd: Optional[Ancestor] = None       # 父方曾祖母1
    sds: Optional[Ancestor] = None       # 父方曾祖父2
    sdd: Optional[Ancestor] = None       # 父方曾祖母2
    dss: Optional[Ancestor] = None       # 母方曾祖父1
    dsd: Optional[Ancestor] = None       # 母方曾祖母1
    dds: Optional[Ancestor] = None       # 母方曾祖父2
    ddd: Optional[Ancestor] = None       # 母方曾祖母2
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
# 手動データ入力 (既知の血統書)
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


# ============================================================
# OCR解析エンジン
# ============================================================

def try_ocr(image_path: str) -> str:
    """画像からテキストを抽出（Tesseract OCR）"""
    try:
        import pytesseract
        from PIL import Image
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            pass
        img = Image.open(image_path)
        # HEIC/WEBP等をRGBに変換してTesseractが処理できるようにする
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        text = pytesseract.image_to_string(img, lang='jpn+eng')
        return text
    except ImportError:
        print("  pytesseract が未インストールです。")
        print("  pip install pytesseract Pillow")
        print("  + Tesseract OCR本体: sudo apt install tesseract-ocr tesseract-ocr-jpn")
        return ""
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
    # Sex（全フォーマット共通）
    if re.search(r'\bMALE\b|オス|牡|♂|性\s*別\s*Male', text, re.IGNORECASE):
        ped.sex = "MALE"
    elif re.search(r'\bFEMALE\b|メス|牝|♀|性\s*別\s*Female', text, re.IGNORECASE):
        ped.sex = "FEMALE"

    # DOB - 複数フォーマット対応
    # 日本語形式: 2025年4月14日
    m = re.search(r'(\d{4}年\s*\d{1,2}月\s*\d{1,2}日)', text)
    if m:
        ped.dob = m.group(1)
    else:
        # 西暦形式: 2013/1/1 or 2013-01-01
        m = re.search(r'(?:生年月日|Date of Birth|DOB|D\.O\.B)\s*[:\s]*(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})', text, re.IGNORECASE)
        if m:
            ped.dob = m.group(1)
        else:
            # 生年月日ラベルなしの日付
            m = re.search(r'(?:生\s*年\s*月\s*日)\s*(\d{4}/\d{1,2}/\d{1,2})', text)
            if m:
                ped.dob = m.group(1)

    # Color - 複数ラベル対応
    m = re.search(r'(?:毛\s*色|色|Color|Colour)\s*[:\s]*([A-Za-z\s]+?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        ped.color = m.group(1).strip()

    # Microchip - 各国の番号形式
    m = re.search(r'(?:マイクロチップ|Microchip|MC|ID)\s*[番号:\s]*(\d{10,15})', text, re.IGNORECASE)
    if m:
        ped.microchip = m.group(1)

    # Owner
    m = re.search(r'(?:所\s*有\s*者|Owner)\s*[:\s]*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        ped.owner = m.group(1).strip()

    # Breeder
    m = re.search(r'(?:繁殖者|Breeder)\s*[:\s]*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        ped.breeder = m.group(1).strip()

    # Breed - 犬種
    m = re.search(r'(?:犬\s*種|Breed)\s*[:\s]*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if m:
        ped.breed = m.group(1).strip()


def _extract_ancestor_name(text_block: str) -> str:
    """テキストブロックから祖先の犬名を抽出（1行目を犬名として取得）"""
    lines = [l.strip() for l in text_block.strip().split('\n') if l.strip()]
    if not lines:
        return ""
    # 最初の非空行が犬名
    name = lines[0]
    # ラベルやノイズを除去
    name = re.sub(r'^(?:SIRE|DAM|G\.?SIRE|G\.?DAM|GG\.?SIRE|GG\.?DAM|父犬?|母犬?|祖父|祖母|曾祖父|曾祖母)\s*[:\s]*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^\d+\s*[\|\{]?\s*', '', name)  # 番号プレフィックス除去
    name = name.strip()
    return name


def _parse_jkc_ancestors(text: str, ped: Pedigree):
    """JKC形式の祖先名を抽出（番号ベース + 犬舎名パターン）"""
    lines = text.split('\n')
    ancestors = {}

    # まず番号付きの祖先を探す
    for line in lines:
        m = re.match(r'\s*(\d{1,2})\s*[\|\{]?\s*(.+)', line)
        if m:
            num = int(m.group(1))
            name_text = m.group(2).strip()
            # 任意の犬名パターン（全角大文字のケンネル名）
            # JKCは通常 "KENNEL NAME DOG NAME" 形式
            name_text = re.sub(r'\s*JKC-PT.*$', '', name_text).strip()
            name_text = re.sub(r'\s*CH/\d+.*$', '', name_text).strip()
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


def _parse_labeled_ancestors(text: str, ped: Pedigree):
    """ラベルベースの祖先抽出（SIRE/DAM/G.SIRE/G.DAM形式 — ALAJ等）"""
    lines = text.split('\n')

    # ラベルと対応するPedigreeフィールドのマッピング
    # ALAJ形式: SIRE, DAM, G.SIRE(父方), G.DAM(父方), G.SIRE(母方), G.DAM(母方)
    # GG.SIRE/GG.DAM は曾祖父母

    # ブロック単位で解析: ラベル行の後に犬名が続く
    label_patterns = [
        # (regex, position, context_required)
        (r'(?:^|\n)\s*(?:SIRE|父犬)\s*(?:\n|$)', "sire"),
        (r'(?:^|\n)\s*(?:DAM|母犬)\s*(?:\n|$)', "dam"),
    ]

    # まずSIRE/DAMの位置を特定してコンテキストを分割
    sire_match = re.search(r'(?:^|\n)\s*SIRE\b', text, re.IGNORECASE)
    dam_match = re.search(r'(?:^|\n)\s*DAM\b', text, re.IGNORECASE)

    # G.SIRE / G.DAM パターンでの祖先抽出
    # テキスト内の位置関係で父方/母方を判定
    gsire_positions = [(m.start(), m.end()) for m in re.finditer(r'G\.?SIRE\b|父方祖父|祖父犬', text, re.IGNORECASE)]
    gdam_positions = [(m.start(), m.end()) for m in re.finditer(r'G\.?DAM\b|父方祖母|祖母犬', text, re.IGNORECASE)]

    def get_name_after_label(text: str, label_end: int, max_chars: int = 200) -> str:
        """ラベルの後のテキストから犬名を抽出"""
        remaining = text[label_end:label_end + max_chars]
        lines = [l.strip() for l in remaining.split('\n') if l.strip()]
        for line in lines:
            # ラベル自体やメタデータをスキップ
            if re.match(r'^(?:SIRE|DAM|G\.?SIRE|G\.?DAM|GG|父犬|母犬|祖父|祖母|曾祖|犬種|性別|サイズ|毛色|生年月日|所有者)', line, re.IGNORECASE):
                continue
            # 犬名らしい行（英字で始まる名前、3文字以上）
            cleaned = re.sub(r'^\d+\s*', '', line).strip()
            if len(cleaned) >= 3 and not re.match(r'^\d{4}[/\-]', cleaned):
                return cleaned
        return ""

    # SIRE（父犬）名の抽出
    if sire_match:
        sire_end = sire_match.end()
        # "SIRE" ラベルの次の行に犬名
        name = get_name_after_label(text, sire_end)
        if name:
            ped.sire = Ancestor(position="sire", name=name)

    # DAM（母犬）名の抽出
    if dam_match:
        dam_end = dam_match.end()
        name = get_name_after_label(text, dam_end)
        if name:
            ped.dam = Ancestor(position="dam", name=name)

    # DAMの位置を基準に父方/母方を判定
    dam_pos = dam_match.start() if dam_match else len(text) // 2

    # G.SIRE / G.DAM を父方・母方に振り分け
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

    # GG.SIRE / GG.DAM (曾祖父母) パターン
    gg_sire_positions = [(m.start(), m.end()) for m in re.finditer(r'GG\.?SIRE\b|G\.G\.SIRE|曾祖父', text, re.IGNORECASE)]
    gg_dam_positions = [(m.start(), m.end()) for m in re.finditer(r'GG\.?DAM\b|G\.G\.DAM|曾祖母', text, re.IGNORECASE)]

    # 曾祖父母は位置関係で4グループに分ける（父方祖父側、父方祖母側、母方祖父側、母方祖母側）
    # 簡易的に出現順で割り当て
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

    # === 基本情報（共通）===
    _extract_basic_info(text, ped)

    # === フォーマット固有の情報 ===
    if fmt == "jkc":
        # JKC固有: 犬名・登録番号
        m = re.search(r'(?:Name of Dog|犬名)\s*\n?\s*(.+?)(?:\n|$)', text)
        if m:
            ped.dog_name = m.group(1).strip()
        m = re.search(r'(JKC-PT\s*-?\s*\d+/\d+)', text)
        if m:
            ped.registration = m.group(1)
        # JKC番号ベースの祖先抽出
        _parse_jkc_ancestors(text, ped)

    elif fmt == "alaj":
        # ALAJ固有: 犬名・登録番号
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

        # ALAJ: ラベルベースの祖先抽出
        _parse_labeled_ancestors(text, ped)

    else:
        # 汎用フォーマット: 犬名を複数パターンで探す
        m = re.search(r'(?:Name of Dog|犬名|Dog Name|名前)\s*[:\s]*\n?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if m:
            ped.dog_name = m.group(1).strip()
        else:
            # 最初の行を犬名とみなす
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if lines:
                ped.dog_name = lines[0]

        # 汎用登録番号
        m = re.search(r'(?:登録番号|Registration|Reg\.?\s*No\.?)\s*[:\s]*([A-Z0-9\-/]+)', text, re.IGNORECASE)
        if m:
            ped.registration = m.group(1)

        # 両方の祖先抽出を試行（ラベルベース → 番号ベース）
        _parse_labeled_ancestors(text, ped)
        # ラベルベースで取れなかった分を番号ベースで補完
        if not ped.sire:
            _parse_jkc_ancestors(text, ped)

    # 犬名がまだ空なら最終手段
    if not ped.dog_name:
        lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 5]
        if lines:
            ped.dog_name = lines[0]

    return ped


# ============================================================
# COI計算 (Wright's method)
# ============================================================

def calc_coi_3gen(ped: Pedigree) -> dict:
    """3世代の血統データからCOIを算出"""
    # Build ancestor lists for sire and dam sides
    sire_ancestors = []
    dam_ancestors = []

    def add_if_exists(lst, ancestor, gen):
        if ancestor and ancestor.name:
            lst.append({"name": ancestor.name.strip().upper(), "gen": gen})

    # Sire side
    add_if_exists(sire_ancestors, ped.sire, 1)
    add_if_exists(sire_ancestors, ped.ss, 2)
    add_if_exists(sire_ancestors, ped.sd, 2)
    add_if_exists(sire_ancestors, ped.sss, 3)
    add_if_exists(sire_ancestors, ped.ssd, 3)
    add_if_exists(sire_ancestors, ped.sds, 3)
    add_if_exists(sire_ancestors, ped.sdd, 3)

    # Dam side
    add_if_exists(dam_ancestors, ped.dam, 1)
    add_if_exists(dam_ancestors, ped.ds, 2)
    add_if_exists(dam_ancestors, ped.dd, 2)
    add_if_exists(dam_ancestors, ped.dss, 3)
    add_if_exists(dam_ancestors, ped.dsd, 3)
    add_if_exists(dam_ancestors, ped.dds, 3)
    add_if_exists(dam_ancestors, ped.ddd, 3)

    # Find common ancestors
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
    # For cross COI, the sire's pedigree ancestors become the sire side
    # and the dam's pedigree ancestors become the dam side
    sire_all = []
    dam_all = []

    def collect(lst, ped, prefix, base_gen=0):
        """血統書の全祖先を収集"""
        ancestors_data = [
            (ped.sire, 1), (ped.dam, 1),
            (ped.ss, 2), (ped.sd, 2), (ped.ds, 2), (ped.dd, 2),
            (ped.sss, 3), (ped.ssd, 3), (ped.sds, 3), (ped.sdd, 3),
            (ped.dss, 3), (ped.dsd, 3), (ped.dds, 3), (ped.ddd, 3),
        ]
        # The dog itself
        if ped.dog_name:
            lst.append({"name": ped.dog_name.strip().upper(), "gen": base_gen})
        for anc, gen in ancestors_data:
            if anc and anc.name:
                lst.append({"name": anc.name.strip().upper(), "gen": base_gen + gen})

    collect(sire_all, sire_ped, "sire", 0)
    collect(dam_all, dam_ped, "dam", 0)

    # Find common ancestors
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


# ============================================================
# レポート出力
# ============================================================

def generate_pedigree_html(pedigrees: list, output_path: str):
    """血統書データ + COI結果のHTMLレポートを生成"""
    html_parts = []

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
                if color_dot == "#9ca3af" and _c:
                    for k, v in _color_map.items():
                        if k in _c or _c in k:
                            color_dot = v
                            break
                ancestors_html += f"""<tr>
                    <td>{label}</td>
                    <td style="font-weight:700;">{anc.name}</td>
                    <td>{anc.registration}</td>
                    <td><span style="display:inline-block;width:16px;height:16px;border-radius:50%;background:{color_dot};border:1px solid #bbb;vertical-align:middle;margin-right:6px;"></span>{anc.color}</td>
                    <td style="font-size:0.8em;">{anc.titles}</td>
                    <td style="font-size:0.8em;">{anc.dna_number}</td>
                </tr>"""

        html_parts.append(f"""
        <div class="card">
            <h2>{ped.dog_name}</h2>
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

            <h3>3世代血統表</h3>
            <table>
                <tr><th>位置</th><th>犬名</th><th>登録番号</th><th>毛色</th><th>タイトル</th><th>DNA番号</th></tr>
                {ancestors_html}
            </table>

            <h3>近親交配係数 (COI) — 個体分析</h3>
            <div class="coi-display">
                <div class="coi-value" style="color:{'#22c55e' if coi_result['coi_pct'] < 6.25 else '#eab308' if coi_result['coi_pct'] < 12.5 else '#ef4444'};">
                    {coi_result['coi_pct']:.2f}%
                </div>
                <div class="coi-label">Wright's COI (3世代)</div>
            </div>
            {"<p>共通祖先: " + ", ".join([c['name'] for c in coi_result['common_ancestors']]) + "</p>" if coi_result['common_ancestors'] else "<p>3世代以内に共通祖先は検出されませんでした。</p>"}
        </div>
        """)

    # Cross COI if multiple pedigrees
    cross_html = ""
    if len(pedigrees) >= 2:
        cross_result = calc_coi_cross(pedigrees[0], pedigrees[1])
        cross_html = f"""
        <div class="card">
            <h2>交配COI予測: {pedigrees[0].dog_name} × {pedigrees[1].dog_name}</h2>
            <div class="coi-display">
                <div class="coi-value" style="color:{'#22c55e' if cross_result['coi_pct'] < 6.25 else '#eab308' if cross_result['coi_pct'] < 12.5 else '#ef4444'};">
                    {cross_result['coi_pct']:.2f}%
                </div>
                <div class="coi-label">予想される子犬のCOI</div>
            </div>
            {"<h3>共通祖先</h3><ul>" + "".join([f"<li>{c['name']} (父方{c['sire_gen']}世代 / 母方{c['dam_gen']}世代 → 寄与: {c['contribution']*100:.3f}%)</li>" for c in cross_result['common_ancestors']]) + "</ul>" if cross_result['common_ancestors'] else "<p>共通祖先は検出されませんでした。</p>"}
        </div>
        """

    full_html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>血統書解析 + COI算出レポート</title>
<style>
body {{ font-family:'Segoe UI','Hiragino Sans',sans-serif; background:#f8f9fa; color:#1f2937; line-height:1.6; margin:0; }}
.container {{ max-width:1100px; margin:0 auto; padding:20px; }}
header {{ background:linear-gradient(135deg,#4a1a7a,#e6007e); color:white; padding:24px 0; border-radius:0 0 20px 20px; margin-bottom:24px; }}
header h1 {{ font-size:1.5em; margin:0 20px; }}
.card {{ background:white; border-radius:16px; padding:24px; margin-bottom:20px; box-shadow:0 2px 12px rgba(0,0,0,0.06); }}
.card h2 {{ color:#4a1a7a; font-size:1.2em; margin-bottom:16px; border-left:4px solid #e6007e; padding-left:10px; }}
.card h3 {{ color:#4a1a7a; margin:16px 0 10px; }}
.info-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:16px; font-size:0.9em; }}
table {{ width:100%; border-collapse:collapse; font-size:0.85em; margin:10px 0; }}
th {{ background:#4a1a7a; color:white; padding:8px 10px; text-align:left; }}
td {{ padding:6px 10px; border-bottom:1px solid #f3f4f6; }}
.coi-display {{ text-align:center; margin:20px 0; }}
.coi-value {{ font-size:3em; font-weight:800; }}
.coi-label {{ color:#6b7280; }}
</style></head><body>
<header><div class="container"><h1>JKC血統書解析 + 近親交配係数(COI) レポート</h1></div></header>
<div class="container">
{"".join(html_parts)}
{cross_html}
</div></body></html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"レポート出力: {output_path}")


# ============================================================
# メイン
# ============================================================

def main():
    print("=" * 55)
    print("  JKC血統書 解析 + COI算出ツール")
    print("=" * 55)

    pedigrees = []

    if len(sys.argv) < 2:
        # Demo mode with known pedigree
        print("\n引数なし → Sevenの血統書データでデモ実行します。")
        print("  使い方: python pedigree_ocr.py pedigree_photo.jpg")
        pedigrees.append(KNOWN_PEDIGREES["seven"])
    else:
        for arg in sys.argv[1:]:
            if arg.lower() in KNOWN_PEDIGREES:
                pedigrees.append(KNOWN_PEDIGREES[arg.lower()])
            elif os.path.isfile(arg):
                print(f"\n画像を解析中: {arg}")
                text = try_ocr(arg)
                if text:
                    ped = parse_jkc_pedigree_text(text)
                    if ped and ped.dog_name:
                        pedigrees.append(ped)
                        print(f"  → {ped.dog_name} の血統書を解析しました。")
                    else:
                        print(f"  → 血統書データの解析に失敗しました。OCR精度が不足している可能性があります。")
                else:
                    print(f"  → テキスト抽出に失敗しました。")

    if not pedigrees:
        print("\n血統書データがありません。")
        sys.exit(1)

    # Calculate and report
    for ped in pedigrees:
        result = calc_coi_3gen(ped)
        print(f"\n{'='*40}")
        print(f"犬名: {ped.dog_name}")
        print(f"COI (3世代): {result['coi_pct']:.2f}%")
        if result['common_ancestors']:
            print(f"共通祖先: {', '.join([c['name'] for c in result['common_ancestors']])}")
        else:
            print("共通祖先: なし（3世代以内）")

    output_path = os.path.join(os.getcwd(), "pedigree_report.html")
    # Check for -o flag
    for i, arg in enumerate(sys.argv):
        if arg in ('-o', '--output') and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "pedigree_report.html")
            break

    generate_pedigree_html(pedigrees, output_path)
    print(f"\n完了! レポート: {output_path}")


if __name__ == "__main__":
    main()
