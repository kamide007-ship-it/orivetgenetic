#!/usr/bin/env python3
"""KB レビュー用エクスポーター — Orivet 獣医チームのレビュー workflow 向け

DISEASE_KB / TRAIT_KB を Markdown 形式でエクスポートし、
Orivet の veterinary geneticist チームがレビュー・修正できるようにする。

Usage:
    python export_kb_review.py [--out FILE] [--diseases-only] [--traits-only]

Default output: kb_review_YYYY-MM-DD.md

レビュー workflow:
    1. このスクリプトで Markdown 出力
    2. Orivet 獣医チームに送信（Google Docs / GitHub PR 等）
    3. レビュー修正コメントを受領
    4. DISEASE_KB / TRAIT_KB に反映
    5. テスト再実行・デプロイ
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path


def _h(value):
    """Markdown でそのまま使えるよう整形（None → 空文字、改行を保持）"""
    if value is None:
        return ""
    return str(value).strip()


def disease_to_md(entry: dict) -> str:
    """疾患エントリを Markdown 化"""
    lines = []
    lines.append(f"### {_h(entry.get('title', '(タイトル未設定)'))}")
    lines.append("")
    lines.append(f"- **slug**: `{_h(entry.get('_slug', '?'))}`")
    lines.append(f"- **match パターン**: `{', '.join(entry.get('match', []))}`")
    severity = entry.get('severity', '(自動推定)')
    lines.append(f"- **重症度 (severity)**: `{severity}`")
    lines.append("")
    for field, label in [
        ("summary",     "📋 概要"),
        ("mechanism",   "🧬 メカニズム"),
        ("symptoms",    "⚠️ 症状"),
        ("inheritance", "🧪 遺伝様式"),
        ("advice",      "💡 アドバイス"),
    ]:
        val = _h(entry.get(field, ""))
        if val:
            lines.append(f"**{label}**")
            lines.append("")
            lines.append(val)
            lines.append("")
    refs = entry.get("references") or []
    if refs:
        lines.append("**🔗 参考リンク**")
        lines.append("")
        for ref in refs:
            lines.append(f"- [{ref.get('label', '?')}]({ref.get('url', '#')})")
        lines.append("")
    # レビューチェックリスト
    lines.append("> **レビュアーへ**: 以下を確認してください")
    lines.append("> - [ ] 疾患名 (title) は Orivet 公式表記と整合しているか")
    lines.append("> - [ ] 遺伝子記号・変異名は最新文献に準拠しているか")
    lines.append("> - [ ] 症状・予後の記述は不正確な誇張・断定がないか")
    lines.append("> - [ ] 飼育・繁殖アドバイスは Orivet の推奨方針と整合しているか")
    lines.append("> - [ ] 参考リンクは権威ある情報源（OMIA / PubMed / Orivet 公式）に置換可能か")
    lines.append("> - [ ] 重症度判定は適切か（明示 override 推奨）")
    lines.append("")
    lines.append("---")
    return "\n".join(lines)


def trait_to_md(entry: dict) -> str:
    """形質エントリを Markdown 化"""
    lines = []
    lines.append(f"### {_h(entry.get('title', '(タイトル未設定)'))}")
    lines.append("")
    lines.append(f"- **slug**: `{_h(entry.get('_slug', '?'))}`")
    lines.append(f"- **match パターン**: `{', '.join(entry.get('match', []))}`")
    lines.append("")
    for field, label in [
        ("summary",   "📋 概要"),
        ("mechanism", "🧬 メカニズム"),
        ("phenotype", "🎨 表現型"),
        ("advice",    "💡 アドバイス"),
    ]:
        val = _h(entry.get(field, ""))
        if val:
            lines.append(f"**{label}**")
            lines.append("")
            lines.append(val)
            lines.append("")
    refs = entry.get("references") or []
    if refs:
        lines.append("**🔗 参考リンク**")
        lines.append("")
        for ref in refs:
            lines.append(f"- [{ref.get('label', '?')}]({ref.get('url', '#')})")
        lines.append("")
    lines.append("> **レビュアーへ**:")
    lines.append("> - [ ] 座位名・遺伝子記号は標準的表記か")
    lines.append("> - [ ] 表現型の説明は遺伝学的に正確か")
    lines.append("> - [ ] アドバイスは犬種特有の事情を考慮しているか")
    lines.append("")
    lines.append("---")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None, help="出力ファイル (default: kb_review_YYYY-MM-DD.md)")
    parser.add_argument("--diseases-only", action="store_true", help="疾患のみエクスポート")
    parser.add_argument("--traits-only", action="store_true", help="形質のみエクスポート")
    args = parser.parse_args()

    # KB をロード
    try:
        from poodle_genetics import (
            DISEASE_KB, TRAIT_KB,
            get_disease_severity, SEVERITY_LABELS,
            group_diseases_by_category,
        )
    except ImportError as e:
        print(f"ERROR: poodle_genetics モジュールを読み込めませんでした: {e}", file=sys.stderr)
        return 1

    today = datetime.utcnow().strftime("%Y-%m-%d")
    out_path = Path(args.out or f"kb_review_{today}.md")

    out = []
    out.append(f"# Orivet 遺伝子検査 KB レビュードキュメント")
    out.append("")
    out.append(f"**生成日**: {today}")
    out.append(f"**疾患エントリ数**: {len(DISEASE_KB)}")
    out.append(f"**形質エントリ数**: {len(TRAIT_KB)}")
    out.append("")
    out.append("## 📋 レビュー目的")
    out.append("")
    out.append("本ドキュメントは、Orivet 遺伝子解析アプリケーションに含まれる")
    out.append("KB（疾患・形質）コンテンツを Orivet 獣医遺伝学チームがレビューするための資料です。")
    out.append("")
    out.append("**現状の KB は AI モデル (Claude) によって生成されており、獣医監修を経ていません**。")
    out.append("Orivet 名で公開する前に、専門家による以下の確認が必要です:")
    out.append("")
    out.append("1. 疾患名・遺伝子記号の正確性")
    out.append("2. メカニズム・症状の医学的正確性")
    out.append("3. アドバイスが Orivet の推奨方針と整合しているか")
    out.append("4. 参考リンクを権威ある情報源（OMIA / PubMed / Orivet 公式）に置換")
    out.append("5. 重症度判定の妥当性")
    out.append("")
    out.append("修正コメントは GitHub Issue または別途指定の方法で受領します。")
    out.append("")
    out.append("---")
    out.append("")

    if not args.traits_only:
        out.append("## 🩺 疾患エントリ (DISEASE_KB)")
        out.append("")
        groups = group_diseases_by_category(DISEASE_KB)
        for cat, items in groups:
            out.append(f"## {cat} ({len(items)} 件)")
            out.append("")
            for entry in items:
                out.append(disease_to_md(entry))
                out.append("")

    if not args.diseases_only:
        out.append("## 🎨 形質エントリ (TRAIT_KB)")
        out.append("")
        for entry in TRAIT_KB:
            out.append(trait_to_md(entry))
            out.append("")

    out.append("---")
    out.append("")
    out.append(f"_End of document. Generated by export_kb_review.py on {today}._")

    out_path.write_text("\n".join(out), encoding="utf-8")
    print(f"✅ KB レビュードキュメントを書き出しました: {out_path}")
    print(f"   - 疾患: {len(DISEASE_KB)} 件")
    print(f"   - 形質: {len(TRAIT_KB)} 件")
    print(f"   - 行数: {len(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
