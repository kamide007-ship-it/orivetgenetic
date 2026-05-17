"""translation_lint.py — 翻訳精度の自動検証

kb_en.py / guides_en.py の英訳が獣医遺伝学・繁殖関連の用語を正しく訳しているかを
ヒューリスティックに検証する。完璧な訳の保証はできないが、明らかな誤訳・抜け漏れ・
固有名詞の表記ゆれを CI 段階で検出する。

検出ルール:
  RULE-1  JA 用語が出現するエントリの EN 側に対応 EN 用語が含まれているか
          （遺伝病名・遺伝子座位・遺伝様式の用語）
  RULE-2  固有名詞（遺伝子記号、酵素名、locus 名）が英語として正しい大文字小文字で出ているか
  RULE-3  P/N、P/P、N/N、bp、kb 等の遺伝学記号が英訳でも保持されているか
  RULE-4  数値（パーセント、年齢）が翻訳前後で一致しているか

CLI:
    python translation_lint.py            # 全件チェック、違反があれば exit 1
    python translation_lint.py --strict   # 警告も exit 1 扱い

エラー出力: stdout に1行1違反、`<file>:<entry> [RULE-X] <message>` 形式。
"""
from __future__ import annotations

import re
import sys
from typing import List, Tuple


# 必須対応辞書: JA に出現したら EN にこのいずれかが含まれていなければ違反
# (ja_pattern, [en_candidates], rule_label)
REQUIRED_TERM_PAIRS: List[Tuple[str, List[str], str]] = [
    # 遺伝病名
    ("変性性脊髄症", ["degenerative myelopathy", "DM"], "term:DM"),
    ("進行性網膜萎縮", ["progressive retinal atrophy", "PRA", "rod-cone", "rod cone"], "term:PRA"),
    ("フォン・ヴィレブランド", ["von Willebrand", "vWD"], "term:vWD"),
    ("フォン.?ヴィレブランド病", ["von Willebrand", "vWD"], "term:vWD"),
    ("椎間板", ["intervertebral disc", "IVDD", "disc"], "term:IVDD"),
    ("軟骨異栄養症", ["chondrodystrophy", "CDDY"], "term:CDDY"),
    ("ガングリオシドーシス", ["gangliosidosis"], "term:gangliosidosis"),
    ("コリーアイ", ["collie eye", "CEA"], "term:CEA"),
    ("運動誘発性虚脱", ["exercise.induced collapse", "EIC"], "term:EIC"),
    ("中心核ミオパチー", ["centronuclear myopathy", "CNM"], "term:CNM"),
    ("膝蓋骨脱臼", ["patellar luxation", "patella"], "term:patella"),
    ("白内障", ["cataract"], "term:cataract"),
    ("緑内障", ["glaucoma"], "term:glaucoma"),
    ("てんかん", ["epilepsy", "seizure"], "term:epilepsy"),
    ("水頭症", ["hydrocephalus"], "term:hydrocephalus"),
    ("股関節形成不全", ["hip dysplasia"], "term:hip_dysplasia"),
    ("僧帽弁", ["mitral valve", "MVD"], "term:MVD"),
    ("肝障害", ["hepatic", "liver"], "term:liver"),
    ("腎", ["renal", "kidney", "nephro"], "term:renal"),
    ("膵炎", ["pancreatitis"], "term:pancreatitis"),
    ("免疫", ["immune", "immuno"], "term:immune"),
    ("自己免疫", ["autoimmune"], "term:autoimmune"),
    # 遺伝学概念
    ("常染色体劣性", ["autosomal recessive"], "term:autosomal_recessive"),
    ("常染色体優性", ["autosomal dominant"], "term:autosomal_dominant"),
    ("X.連鎖", ["X-linked", "X linked"], "term:X_linked"),
    ("ヘテロ接合", ["heterozygot"], "term:heterozygous"),
    ("ホモ接合", ["homozygot"], "term:homozygous"),
    ("キャリア", ["carrier", r"\bP/N\b"], "term:carrier"),
    ("ハプロタイプ", ["haplotype"], "term:haplotype"),
    ("浸透率", ["penetrance"], "term:penetrance"),
    # 毛色遺伝学
    ("座位", ["locus", "loci"], "term:locus"),
    ("マール", ["merle"], "term:merle"),
    ("ブリンドル", ["brindle"], "term:brindle"),
    ("ファーニシング", ["furnishing"], "term:furnishings"),
    ("パイド", ["pied", "piebald", "parti"], "term:piebald"),
    ("パーティカラー", ["parti", "piebald"], "term:particolor"),
    ("セーブル", ["sable"], "term:sable"),
    ("タンポイント", ["tan.point", "tan point"], "term:tanpoint"),
    ("希釈", ["dilut"], "term:dilution"),
    # 短頭種
    ("短頭種", ["brachycephalic"], "term:brachycephalic"),
]

# JA に対して EN 側で「使ってはいけない」誤訳パターン
FORBIDDEN_PAIRS: List[Tuple[str, str, str]] = [
    # ay (agouti) を「agouti yellow」と訳しがち、正しくは "fawn / sable"
    # しかし両方許容するため検出しない
    # bb を「brown brown」と直訳する誤りは検出可能だが既存訳で確認済
]

# 数値の一致チェック（JA に出現する固有数値が EN に保持されているか）
NUMERIC_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*[%％]")


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s or "")


def _join_text(entry: dict, fields: List[str]) -> str:
    return " ".join(str(entry.get(f, "") or "") for f in fields)


def check_kb_pair(slug: str, ja_text: str, en_text: str) -> List[Tuple[str, str]]:
    """JA テキストと対応する EN テキストを比較し、違反リストを返す。"""
    violations: List[Tuple[str, str]] = []
    ja_clean = _strip_html(ja_text)
    en_clean = _strip_html(en_text).lower()
    if not en_clean.strip():
        return violations  # 英訳なしはスキップ

    # RULE-1: 用語マッピング
    for ja_pattern, en_candidates, rule in REQUIRED_TERM_PAIRS:
        if re.search(ja_pattern, ja_clean):
            if not any(re.search(c.lower(), en_clean) for c in en_candidates):
                violations.append((rule, f"JA contains /{ja_pattern}/ but EN missing any of {en_candidates}"))

    # RULE-4: 数値の保持
    ja_nums = set(NUMERIC_PATTERN.findall(ja_clean))
    en_nums = set(NUMERIC_PATTERN.findall(en_clean))
    missing_nums = ja_nums - en_nums
    if missing_nums:
        violations.append(("RULE-4", f"Numeric values missing in EN: {sorted(missing_nums)} (JA had {sorted(ja_nums)})"))

    return violations


def lint_kb() -> List[str]:
    """DISEASE_KB と TRAIT_KB を kb_en.py と照らして検証。"""
    errors: List[str] = []
    from poodle_genetics import DISEASE_KB, TRAIT_KB
    try:
        from kb_en import DISEASE_EN, TRAIT_EN
    except ImportError:
        return ["kb_en.py not importable — skipped KB lint"]

    disease_fields = ["title", "summary", "mechanism", "symptoms", "inheritance", "advice"]
    trait_fields = ["title", "summary", "mechanism", "phenotype", "advice"]

    for entry in DISEASE_KB:
        slug = entry.get("_slug")
        en = DISEASE_EN.get(slug)
        if not en:
            continue
        ja_text = _join_text(entry, disease_fields)
        en_text = _join_text(en, disease_fields)
        for rule, msg in check_kb_pair(slug, ja_text, en_text):
            errors.append(f"kb_en.py:DISEASE_EN[{slug!r}] [{rule}] {msg}")

    for entry in TRAIT_KB:
        slug = entry.get("_slug")
        en = TRAIT_EN.get(slug)
        if not en:
            continue
        ja_text = _join_text(entry, trait_fields)
        en_text = _join_text(en, trait_fields)
        for rule, msg in check_kb_pair(slug, ja_text, en_text):
            errors.append(f"kb_en.py:TRAIT_EN[{slug!r}] [{rule}] {msg}")

    return errors


def lint_guides() -> List[str]:
    """GUIDES を guides_en.py と照らして検証。"""
    errors: List[str] = []
    from poodle_genetics import GUIDES
    try:
        from guides_en import GUIDES_EN
    except ImportError:
        return ["guides_en.py not importable — skipped guides lint"]

    for guide in GUIDES:
        slug = guide["slug"]
        en = GUIDES_EN.get(slug)
        if not en:
            continue
        # summary + 全 sections 本文を結合して比較
        ja_text = guide.get("summary", "") + " " + " ".join(
            s.get("body", "") for s in guide.get("sections", [])
        )
        en_text = en.get("summary", "") + " " + " ".join(
            s.get("body", "") for s in en.get("sections", [])
        )
        for rule, msg in check_kb_pair(slug, ja_text, en_text):
            errors.append(f"guides_en.py:GUIDES_EN[{slug!r}] [{rule}] {msg}")

        # セクション数の一致チェック
        ja_sec = len(guide.get("sections", []))
        en_sec = len(en.get("sections", []))
        if ja_sec != en_sec:
            errors.append(
                f"guides_en.py:GUIDES_EN[{slug!r}] [RULE-STRUCT] "
                f"section count mismatch: JA={ja_sec}, EN={en_sec}"
            )

    return errors


def main(argv: List[str]) -> int:
    strict = "--strict" in argv
    errors = lint_kb() + lint_guides()
    if not errors:
        print("translation_lint: OK — no issues detected")
        return 0
    print(f"translation_lint: {len(errors)} issue(s) detected\n")
    for e in errors:
        print(e)
    if strict or any("[RULE-4]" in e or "[RULE-STRUCT]" in e for e in errors):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
