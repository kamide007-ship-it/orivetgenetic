"""
KB（疾患・形質辞書）スキーマ検証。

DISEASE_KB / TRAIT_KB の各エントリが必須フィールドを正しい型で持つかを
チェックし、問題があればエラーメッセージのリストを返す。CI（pytest）で
実行し、KB 追加・編集時のフィールド漏れ・型ミス・slug 重複を検出する。

外部依存（jsonschema 等）を持たず標準ライブラリのみで実装 — どの環境でも
動作し、CI に軽量に組み込める。
"""

import re

_SLUG_RE = re.compile(r"^[a-z0-9-]+$")
_VALID_SEVERITY = {"high", "medium", "low"}

# (フィールド名, 期待する型) — 全エントリで必須
_DISEASE_REQUIRED = [
    ("match", list),
    ("title", str),
    ("severity", str),
    ("summary", str),
    ("mechanism", str),
    ("symptoms", str),
    ("inheritance", str),
    ("advice", str),
    ("references", list),
    ("_slug", str),
]
_TRAIT_REQUIRED = [
    ("match", list),
    ("title", str),
    ("summary", str),
    ("mechanism", str),
    ("phenotype", str),
    ("inheritance", str),
    ("advice", str),
    ("references", list),
    ("_slug", str),
    ("_en", dict),
    ("_simple", dict),
]

# 空文字を許さない str フィールド（match/references はリストなので別扱い）
_NONEMPTY_STR_FIELDS = {
    "title", "summary", "mechanism", "symptoms", "phenotype",
    "inheritance", "advice", "_slug",
}


def _validate_entry(entry, required, kind, idx, seen_slugs, errors):
    label = None
    if isinstance(entry, dict):
        label = entry.get("title") or entry.get("_slug")
    prefix = f"{kind}[{idx}]" + (f" ({label})" if label else "")

    if not isinstance(entry, dict):
        errors.append(f"{prefix}: エントリが dict ではありません（{type(entry).__name__}）")
        return

    # 必須フィールド + 型
    for field, expected_type in required:
        if field not in entry:
            errors.append(f"{prefix}: 必須フィールド '{field}' がありません")
            continue
        val = entry[field]
        if not isinstance(val, expected_type):
            errors.append(
                f"{prefix}: '{field}' の型が {expected_type.__name__} ではありません"
                f"（実際: {type(val).__name__}）"
            )
            continue
        # 空文字チェック
        if field in _NONEMPTY_STR_FIELDS and isinstance(val, str) and not val.strip():
            errors.append(f"{prefix}: '{field}' が空文字です")

    # match: 非空の文字列リスト
    match = entry.get("match")
    if isinstance(match, list):
        if not match:
            errors.append(f"{prefix}: 'match' が空リストです（検索キーワードが必要）")
        for i, m in enumerate(match):
            if not isinstance(m, str) or not m.strip():
                errors.append(f"{prefix}: 'match'[{i}] が空文字または非文字列です")

    # severity: 疾患は必須で有効値、形質は任意だが値があれば有効値
    sev = entry.get("severity")
    if kind == "disease":
        if sev not in _VALID_SEVERITY:
            errors.append(f"{prefix}: 'severity' が不正です（{sev!r}、期待: {_VALID_SEVERITY}）")
    elif sev is not None and sev not in _VALID_SEVERITY:
        errors.append(f"{prefix}: 'severity' が不正です（{sev!r}、期待: {_VALID_SEVERITY} または省略）")

    # _slug: 形式 + 重複
    slug = entry.get("_slug")
    if isinstance(slug, str):
        if not _SLUG_RE.match(slug):
            errors.append(f"{prefix}: '_slug' が URL-safe ではありません（{slug!r}、期待: ^[a-z0-9-]+$）")
        if slug in seen_slugs:
            errors.append(f"{prefix}: '_slug' が重複しています（{slug!r}）")
        else:
            seen_slugs.add(slug)

    # references: 各要素が label + url を持つ dict
    refs = entry.get("references")
    if isinstance(refs, list):
        for i, r in enumerate(refs):
            if not isinstance(r, dict):
                errors.append(f"{prefix}: 'references'[{i}] が dict ではありません")
                continue
            if not r.get("label"):
                errors.append(f"{prefix}: 'references'[{i}] に 'label' がありません")
            if not r.get("url"):
                errors.append(f"{prefix}: 'references'[{i}] に 'url' がありません")

    # _en（任意）: dict
    if "_en" in entry and not isinstance(entry["_en"], dict):
        errors.append(f"{prefix}: '_en' が dict ではありません")


def validate_kb(disease_kb, trait_kb):
    """DISEASE_KB / TRAIT_KB を検証しエラーメッセージのリストを返す。空なら問題なし。"""
    errors = []
    seen_disease_slugs = set()
    for idx, entry in enumerate(disease_kb):
        _validate_entry(entry, _DISEASE_REQUIRED, "disease", idx, seen_disease_slugs, errors)
    seen_trait_slugs = set()
    for idx, entry in enumerate(trait_kb):
        _validate_entry(entry, _TRAIT_REQUIRED, "trait", idx, seen_trait_slugs, errors)
    return errors
