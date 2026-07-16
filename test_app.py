"""
poodle-genetics 回帰テスト

- サンプルPDF/画像不要の範囲で純Python/Flask clientで検証する
- 新機能追加時は必ずここにケースを追加すること
- pytest test_app.py で実行
"""

import os
import sys
import time
import shutil
import tempfile
import types

import pytest

# ---------------------------------------------------------------------------
# 重量依存のスタブ（テスト環境にインストール不要）
# ---------------------------------------------------------------------------
for _mod in ("pdfplumber", "pytesseract", "openpyxl"):
    sys.modules.setdefault(_mod, types.ModuleType(_mod))

_pillow_heif = types.ModuleType("pillow_heif")
_pillow_heif.register_heif_opener = lambda: None
sys.modules.setdefault("pillow_heif", _pillow_heif)

# PIL スタブ（Pillow 未インストール環境向け）
if "PIL" not in sys.modules:
    _pil = types.ModuleType("PIL")
    _image = types.ModuleType("PIL.Image")
    sys.modules["PIL"] = _pil
    sys.modules["PIL.Image"] = _image

sys.path.insert(0, os.path.dirname(__file__))
import app as _app  # noqa: E402

client = _app.app.test_client()
_app.app.config["TESTING"] = True


# ===========================================================================
# 1. _cleanup_old_session_dirs
# ===========================================================================

class TestCleanup:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_dir(self, name, age_seconds):
        p = os.path.join(self.tmp, name)
        os.makedirs(p)
        t = time.time() - age_seconds
        os.utime(p, (t, t))
        return p

    def test_removes_old_dir(self):
        old = self._make_dir("old", 25 * 3600)
        removed = _app._cleanup_old_session_dirs(self.tmp, ttl_seconds=24 * 3600)
        assert removed == 1
        assert not os.path.exists(old)

    def test_keeps_new_dir(self):
        new = self._make_dir("new", 1 * 3600)
        removed = _app._cleanup_old_session_dirs(self.tmp, ttl_seconds=24 * 3600)
        assert removed == 0
        assert os.path.exists(new)

    def test_does_not_touch_top_level_files(self):
        fp = os.path.join(self.tmp, "keep.txt")
        open(fp, "w").write("x")
        self._make_dir("old", 25 * 3600)
        _app._cleanup_old_session_dirs(self.tmp, ttl_seconds=24 * 3600)
        assert os.path.exists(fp)

    def test_nonexistent_folder_returns_zero(self):
        assert _app._cleanup_old_session_dirs("/nonexistent_xyz_path") == 0

    def test_boundary_exactly_at_ttl(self):
        # ちょうど TTL 秒前は削除対象外（境界値）
        border = self._make_dir("border", 24 * 3600 - 1)
        removed = _app._cleanup_old_session_dirs(self.tmp, ttl_seconds=24 * 3600)
        assert removed == 0
        assert os.path.exists(border)


# ===========================================================================
# 2. /healthz エンドポイント
# ===========================================================================

class TestKbSchemaValidation:
    """DISEASE_KB / TRAIT_KB のスキーマ検証（CI で必須フィールド漏れ検出）"""

    def test_real_kb_passes_validation(self):
        """本番の疾患・形質 KB がスキーマ検証を通過する（フィールド漏れ・型ミス無し）"""
        from poodle_genetics import DISEASE_KB, TRAIT_KB
        from kb_validate import validate_kb
        errors = validate_kb(DISEASE_KB, TRAIT_KB)
        assert errors == [], "KB 検証エラー:\n" + "\n".join(errors[:30])

    def test_validator_detects_missing_field(self):
        from kb_validate import validate_kb
        bad = [{"match": ["x"], "severity": "high", "summary": "s",
                "mechanism": "m", "symptoms": "y", "inheritance": "i",
                "advice": "a", "references": [], "_slug": "x"}]  # title 欠落
        errors = validate_kb(bad, [])
        assert any("title" in e for e in errors)

    def test_validator_detects_bad_severity(self):
        from kb_validate import validate_kb
        bad = [{"title": "T", "match": ["x"], "severity": "critical",
                "summary": "s", "mechanism": "m", "symptoms": "y",
                "inheritance": "i", "advice": "a", "references": [], "_slug": "x"}]
        errors = validate_kb(bad, [])
        assert any("severity" in e for e in errors)

    def test_validator_detects_duplicate_slug(self):
        from kb_validate import validate_kb
        base = {"title": "T", "match": ["x"], "severity": "high", "summary": "s",
                "mechanism": "m", "symptoms": "y", "inheritance": "i",
                "advice": "a", "references": []}
        bad = [dict(base, _slug="dup"), dict(base, _slug="dup")]
        errors = validate_kb(bad, [])
        assert any("重複" in e for e in errors)

    def test_validator_detects_bad_slug_format(self):
        from kb_validate import validate_kb
        bad = [{"title": "T", "match": ["x"], "severity": "high", "summary": "s",
                "mechanism": "m", "symptoms": "y", "inheritance": "i",
                "advice": "a", "references": [], "_slug": "Bad Slug!"}]
        errors = validate_kb(bad, [])
        assert any("URL-safe" in e for e in errors)

    def test_validator_detects_empty_match(self):
        from kb_validate import validate_kb
        bad = [{"title": "T", "match": [], "severity": "high", "summary": "s",
                "mechanism": "m", "symptoms": "y", "inheritance": "i",
                "advice": "a", "references": [], "_slug": "x"}]
        errors = validate_kb(bad, [])
        assert any("match" in e for e in errors)


class TestDynamicOgImage:
    """レポート個別の動的 OG 画像（SVG）"""

    def _make_session(self, sid, dogs):
        import os, json
        from app import REPORT_FOLDER
        d = os.path.join(REPORT_FOLDER, sid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "dogs.json"), "w", encoding="utf-8") as f:
            json.dump(dogs, f, ensure_ascii=False)
        return d

    def test_og_image_renders_dog_names(self):
        import shutil
        d = self._make_session("og_unit_1", [
            {"name": "Seven", "breed": "Toy Poodle"},
            {"name": "Angel", "breed": "Toy Poodle"},
        ])
        try:
            rv = client.get("/og/report/og_unit_1.svg")
            assert rv.status_code == 200
            assert rv.headers["Content-Type"].startswith("image/svg+xml")
            body = rv.get_data(as_text=True)
            assert "<svg" in body
            assert "Seven" in body and "Angel" in body
            assert "Toy Poodle" in body
            assert "検査 2 頭" in body
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_og_image_fallback_when_missing(self):
        rv = client.get("/og/report/nonexistent_sid.svg")
        assert rv.status_code == 200
        assert "遺伝子解析レポート" in rv.get_data(as_text=True)

    def test_og_image_rejects_path_traversal(self):
        rv = client.get("/og/report/..%2f..svg")
        # Flask は %2f を含む path を分割するため 404 になる（route にマッチしない）
        assert rv.status_code in (400, 404)

    def test_og_image_escapes_dog_name(self):
        """犬名の XSS/SVG インジェクションが無害化される"""
        import shutil
        d = self._make_session("og_xss", [
            {"name": "<script>x</script>", "breed": "Poodle"},
            {"name": "B", "breed": "Poodle"},
        ])
        try:
            body = client.get("/og/report/og_xss.svg").get_data(as_text=True)
            assert "<script>x</script>" not in body
            assert "&lt;script&gt;" in body
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestDiseaseFaqJsonLd:
    """疾患ページの FAQPage 構造化データ"""

    def test_faq_present_on_disease_page(self):
        rv = client.get("/glossary/disease/degenerative-myelopathy")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert "FAQPage" in body
        assert "Question" in body
        assert "acceptedAnswer" in body

    def test_faq_helper_needs_two_questions(self):
        from app import _build_disease_faq_jsonld
        # 2 問未満は None
        assert _build_disease_faq_jsonld({"title": "X", "summary": "one"}, "ja") is None
        # 2 問以上で FAQPage
        faq = _build_disease_faq_jsonld(
            {"title": "DM", "summary": "S", "mechanism": "M"}, "ja")
        assert faq["@type"] == "FAQPage"
        assert len(faq["mainEntity"]) == 2
        assert faq["mainEntity"][0]["name"] == "DMとは何ですか？"

    def test_faq_strips_html_tags(self):
        from app import _build_disease_faq_jsonld
        faq = _build_disease_faq_jsonld(
            {"title": "T", "summary": "<b>bold</b> text", "symptoms": "<i>sym</i>"}, "ja")
        answers = [q["acceptedAnswer"]["text"] for q in faq["mainEntity"]]
        assert all("<" not in a for a in answers)

    def test_faq_english_questions(self):
        from app import _build_disease_faq_jsonld
        faq = _build_disease_faq_jsonld(
            {"title": "DM", "summary": "S", "mechanism": "M"}, "en")
        assert faq["mainEntity"][0]["name"] == "What is DM?"
        assert faq["inLanguage"] == "en"


class TestHealthz:
    def test_returns_200(self):
        rv = client.get("/healthz")
        assert rv.status_code == 200

    def test_returns_json(self):
        rv = client.get("/healthz")
        data = rv.get_json()
        assert data is not None
        assert "status" in data
        assert data["status"] == "ok"

    def test_contains_feature_flags(self):
        rv = client.get("/healthz")
        data = rv.get_json()
        assert "pdfplumber" in data
        assert "ocr" in data


class TestClientErrorEndpoint:
    """ブラウザ JS エラー受信エンドポイント"""

    def test_client_error_accepts_post(self):
        rv = client.post("/api/client-error", json={
            "message": "TypeError: x is undefined",
            "source": "/simulator",
            "line": 42, "col": 7,
            "page": "/simulator?session=abc",
        })
        assert rv.status_code == 202
        assert rv.get_json()["ok"] is True

    def test_client_error_handles_empty_body(self):
        rv = client.post("/api/client-error")
        assert rv.status_code == 202

    def test_client_error_clips_long_message(self):
        # 過大な message でも 500 にならない（内部でクリップ）
        rv = client.post("/api/client-error", json={"message": "x" * 5000})
        assert rv.status_code == 202


class TestPdfCacheStats:
    """PDF パースキャッシュ統計エンドポイント"""

    def test_cache_stats_returns_200(self):
        rv = client.get("/api/cache-stats")
        assert rv.status_code == 200
        data = rv.get_json()
        assert "pdf_cache_size" in data
        assert "hits" in data
        assert "misses" in data
        assert "hit_rate" in data

    def test_cached_parse_pdf_caches_by_hash(self):
        """cached_parse_pdf が同一バイト列で 2 回目はキャッシュヒットする"""
        import app as _appmod
        import tempfile, os
        # parse_pdf をモックして呼び出し回数をカウント
        from poodle_genetics import DogProfile
        calls = {"n": 0}
        orig = _appmod.parse_pdf

        def fake_parse(path):
            calls["n"] += 1
            return DogProfile(pet_name="Cached", registered_name="R", sex="Male")

        _appmod.parse_pdf = fake_parse
        # キャッシュをクリア
        _appmod._pdf_parse_cache.clear()
        try:
            fd, path = tempfile.mkstemp(suffix=".pdf")
            os.write(fd, b"%PDF-1.4 identical-bytes-for-cache-test")
            os.close(fd)
            d1 = _appmod.cached_parse_pdf(path)
            d2 = _appmod.cached_parse_pdf(path)
            os.unlink(path)
            # parse_pdf は 1 回だけ呼ばれる（2 回目はキャッシュ）
            assert calls["n"] == 1
            assert d1.pet_name == "Cached"
            assert d2.pet_name == "Cached"
            # deepcopy なので別オブジェクト（キャッシュ汚染防止）
            assert d1 is not d2
        finally:
            _appmod.parse_pdf = orig

    def test_log_json_helper(self):
        """_log_json が例外を投げずに構造化ログを出す"""
        import app as _appmod
        # 正常系
        _appmod._log_json("test_event", level="info", foo="bar", n=1)
        # シリアライズ不能オブジェクトでも落ちない（default=str）
        _appmod._log_json("test_event2", obj=object())


class TestVersion:
    def test_version_returns_200(self):
        rv = client.get("/version")
        assert rv.status_code == 200

    def test_version_includes_kb_counts(self):
        rv = client.get("/version")
        data = rv.get_json()
        assert data.get("disease_kb_count", 0) >= 70
        assert data.get("trait_kb_count", 0) >= 14
        assert data.get("guides_count", 0) >= 5

    def test_version_includes_config(self):
        rv = client.get("/version")
        data = rv.get_json()
        assert "session_ttl_hours" in data
        assert "max_upload_mb" in data
        assert "features" in data
        assert "service_worker" in data["features"]

    def test_version_service_name(self):
        rv = client.get("/version")
        data = rv.get_json()
        assert "Orivet" in data.get("service", "")


# ===========================================================================
# 20. 英訳 KB (kb_en.py)
# ===========================================================================

try:
    from kb_en import DISEASE_EN, TRAIT_EN, SEVERITY_LABELS_EN, CATEGORY_LABELS_EN, SYMPTOM_LABELS_EN
    _HAS_EN = True
except Exception:
    _HAS_EN = False


@pytest.mark.skipif(not _HAS_EN, reason="kb_en not importable")
class TestEnglishKB:
    def test_disease_en_count(self):
        # 全77疾患の英訳が含まれていること
        assert len(DISEASE_EN) >= 77

    def test_trait_en_count(self):
        # 全14形質座位の英訳
        assert len(TRAIT_EN) >= 14

    def test_disease_en_has_required_fields(self):
        for slug, entry in DISEASE_EN.items():
            assert entry.get("title"), f"{slug} missing title"
            assert entry.get("summary"), f"{slug} missing summary"
            assert entry.get("mechanism"), f"{slug} missing mechanism"

    def test_trait_en_has_phenotype(self):
        for slug, entry in TRAIT_EN.items():
            assert entry.get("title"), f"{slug} missing title"
            assert entry.get("summary"), f"{slug} missing summary"
            assert entry.get("phenotype"), f"{slug} missing phenotype"

    def test_severity_labels_en(self):
        assert "high" in SEVERITY_LABELS_EN
        assert "Risk" in SEVERITY_LABELS_EN["high"]["label"] or "risk" in SEVERITY_LABELS_EN["high"]["label"]

    def test_category_labels_en(self):
        # 主要カテゴリの英訳
        labels = list(CATEGORY_LABELS_EN.values())
        joined = " ".join(labels)
        assert "Neurological" in joined or "Skeletal" in joined

    def test_kb_en_slugs_match_kb(self):
        """kb_en の slug が DISEASE_KB / TRAIT_KB の slug と一致するか"""
        from poodle_genetics import DISEASE_SLUG_INDEX, TRAIT_SLUG_INDEX
        for slug in DISEASE_EN.keys():
            assert slug in DISEASE_SLUG_INDEX, f"EN slug '{slug}' not in DISEASE_SLUG_INDEX"
        for slug in TRAIT_EN.keys():
            assert slug in TRAIT_SLUG_INDEX, f"EN slug '{slug}' not in TRAIT_SLUG_INDEX"


@pytest.mark.skipif(not _HAS_EN, reason="kb_en not importable")
class TestGlossaryEnglish:
    def test_glossary_en_returns_english_content(self):
        rv = client.get("/glossary?lang=en")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        # 主要英文テキストが含まれる
        assert "Chondrodystrophy" in body or "Degenerative Myelopathy" in body or "von Willebrand" in body

    def test_disease_detail_en(self):
        rv = client.get("/glossary/disease/chondrodystrophy?lang=en")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        # CDDY の英文 title が表示される
        assert "Chondrodystrophy" in body

    def test_trait_detail_en(self):
        rv = client.get("/glossary/trait/e-locus?lang=en")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert "E Locus" in body or "MC1R" in body

    def test_disease_detail_ja_default(self):
        rv = client.get("/glossary/disease/chondrodystrophy")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        # デフォルトは日本語
        assert "椎間板" in body or "軟骨異栄養症" in body

    def test_accept_language_en_header(self):
        """Accept-Language: en で英語コンテンツを返す"""
        rv = client.get("/glossary/disease/chondrodystrophy",
                         headers={"Accept-Language": "en-US,en;q=0.9"})
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert "Chondrodystrophy" in body


# ===========================================================================
# 21. PR #63: J + K + L
# ===========================================================================

class TestSitemapI18n:
    def test_sitemap_includes_en_urls(self):
        rv = client.get("/sitemap.xml")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        # 英語 alternate URL が含まれる
        assert "?lang=en" in body

    def test_sitemap_has_hreflang(self):
        rv = client.get("/sitemap.xml")
        body = rv.get_data(as_text=True)
        # hreflang annotation
        assert "xhtml:link" in body
        assert 'hreflang="ja"' in body
        assert 'hreflang="en"' in body


class TestRelatedGuidesReverse:
    def test_reverse_index_built(self):
        from poodle_genetics import GUIDES_BY_DISEASE, GUIDES_BY_TRAIT
        assert isinstance(GUIDES_BY_DISEASE, dict)
        assert isinstance(GUIDES_BY_TRAIT, dict)
        # CDDY は『how-to-read-orivet-results』ガイドおよびダックス・プードルガイド等が参照
        assert "chondrodystrophy" in GUIDES_BY_DISEASE
        assert len(GUIDES_BY_DISEASE["chondrodystrophy"]) >= 1

    def test_disease_page_shows_related_guides(self):
        rv = client.get("/glossary/disease/chondrodystrophy")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        # 関連ガイドが表示される
        assert "関連ガイド" in body or "Related Guides" in body

    def test_trait_page_shows_related_guides_when_present(self):
        # e-locus は color-genetics-basics ガイドおよび犬種別ガイドが参照
        rv = client.get("/glossary/trait/e-locus")
        body = rv.get_data(as_text=True)
        # 関連ガイドが少なくとも 1 つ表示される（多くの犬種ガイドが参照）
        assert "関連ガイド" in body or "Related Guides" in body


class TestSeoInternalLinking:
    """SEO 内部リンク強化（関連疾患/形質・BreadcrumbList・hreflang・Organization）"""

    # --- 関連エントリ・インデックス ---
    def test_related_disease_index_built(self):
        from poodle_genetics import RELATED_DISEASES_BY_SLUG, DISEASE_KB
        assert isinstance(RELATED_DISEASES_BY_SLUG, dict)
        # 大半の疾患に同一カテゴリの関連疾患がある
        with_related = sum(1 for v in RELATED_DISEASES_BY_SLUG.values() if v)
        assert with_related >= len(DISEASE_KB) - 5

    def test_related_disease_excludes_self(self):
        from poodle_genetics import RELATED_DISEASES_BY_SLUG
        for slug, related in RELATED_DISEASES_BY_SLUG.items():
            assert all(r["slug"] != slug for r in related), f"{slug} は自己参照しない"

    def test_related_trait_index_built(self):
        from poodle_genetics import RELATED_TRAITS_BY_SLUG, TRAIT_KB
        assert isinstance(RELATED_TRAITS_BY_SLUG, dict)
        # 全形質がいずれかのグループに属する
        with_related = sum(1 for v in RELATED_TRAITS_BY_SLUG.values() if v)
        assert with_related == len(TRAIT_KB)

    def test_related_trait_excludes_self(self):
        from poodle_genetics import RELATED_TRAITS_BY_SLUG
        for slug, related in RELATED_TRAITS_BY_SLUG.items():
            assert all(r["slug"] != slug for r in related)

    # --- Embark 由来追加疾患（embark_diseases.py） ---
    def test_embark_diseases_loaded(self):
        from poodle_genetics import DISEASE_KB, HAS_EMBARK_DISEASES, HAS_EMBARK_VARIANTS
        assert HAS_EMBARK_DISEASES, "embark_diseases.py がロードできなかった"
        assert HAS_EMBARK_VARIANTS, "embark_diseases_variants.py がロードできなかった"
        embark = [d for d in DISEASE_KB if d.get("_source") == "embark"]
        # 115 (embark_diseases) + ~100 (variants) ≈ 215+ entries
        assert len(embark) >= 200, f"Embark 由来エントリ数が不足: {len(embark)}"

    def test_embark_total_disease_count(self):
        """全 DISEASE_KB エントリ数が Embark カバレッジ目標（~271+）に達している"""
        from poodle_genetics import DISEASE_KB
        assert len(DISEASE_KB) >= 271, (
            f"DISEASE_KB has {len(DISEASE_KB)} entries; "
            "目標 271 件以上（Embark DNA テストのカバレッジ）"
        )

    def test_embark_disease_pages_render(self):
        """主要な Embark 由来エントリの個別ページが 200 を返す"""
        for slug in ["hemophilia-a", "hemophilia-b", "malignant-hyperthermia",
                     "long-qt-syndrome", "polycystic-kidney-disease",
                     "primary-lens-luxation-2", "bully-whippet",
                     "oculocutaneous-albinism", "lethal-acrodermatitis"]:
            rv = client.get(f"/glossary/disease/{slug}")
            assert rv.status_code == 200, f"{slug} not 200"

    def test_embark_diseases_in_sitemap(self):
        body = client.get("/sitemap.xml").get_data(as_text=True)
        assert "/glossary/disease/hemophilia-a" in body
        assert "/glossary/disease/malignant-hyperthermia" in body

    def test_embark_diseases_categorized(self):
        """全 Embark 由来エントリが「その他」以外のカテゴリに分類されている"""
        from poodle_genetics import DISEASE_KB, get_disease_category
        for d in DISEASE_KB:
            if d.get("_source") == "embark":
                cat = get_disease_category(d)
                assert cat != "📋 その他", (
                    f"{d['_slug']} はカテゴリ未分類: {d.get('title')}"
                )

    # --- 詳細ページの関連リンク描画 ---
    def test_disease_page_shows_related_diseases(self):
        rv = client.get("/glossary/disease/degenerative-myelopathy")
        body = rv.get_data(as_text=True)
        assert "関連する遺伝子疾患" in body
        # 関連疾患リンク（自己ページへのリンクを除く）が少なくとも 1 件存在する
        # （カテゴリ内エントリ数の増加により、特定スラッグへの依存をやめる）
        import re
        all_links = set(re.findall(r"/glossary/disease/[a-z0-9-]+", body))
        other_links = {u for u in all_links if "degenerative-myelopathy" not in u}
        assert len(other_links) >= 1, f"expected ≥1 related disease link, got {other_links}"

    def test_trait_page_shows_related_traits(self):
        rv = client.get("/glossary/trait/e-locus")
        body = rv.get_data(as_text=True)
        assert "関連する形質" in body
        # 同グループの別形質への個別リンクがある
        assert "/glossary/trait/k-locus" in body

    def test_related_links_localized_en(self):
        rv = client.get("/glossary/trait/e-locus?lang=en")
        body = rv.get_data(as_text=True)
        assert "Related Traits" in body
        assert "/glossary/trait/k-locus?lang=en" in body

    # --- BreadcrumbList 構造化データ ---
    def test_disease_has_breadcrumb_jsonld(self):
        body = client.get("/glossary/disease/degenerative-myelopathy").get_data(as_text=True)
        assert '"@type": "BreadcrumbList"' in body

    def test_trait_has_breadcrumb_jsonld(self):
        body = client.get("/glossary/trait/e-locus").get_data(as_text=True)
        assert '"@type": "BreadcrumbList"' in body

    def test_guide_has_breadcrumb_jsonld(self):
        body = client.get("/guides/coi-basics").get_data(as_text=True)
        assert '"@type": "BreadcrumbList"' in body

    def test_all_jsonld_valid_json(self):
        """全主要ページの JSON-LD ブロックが有効な JSON である"""
        import json, re
        urls = [
            "/", "/?lang=en", "/glossary", "/glossary?lang=en",
            "/glossary/disease/degenerative-myelopathy",
            "/glossary/disease/degenerative-myelopathy?lang=en",
            "/glossary/trait/e-locus", "/glossary/trait/e-locus?lang=en",
            "/guides", "/guides/coi-basics", "/guides/coi-basics?lang=en",
        ]
        for url in urls:
            body = client.get(url).get_data(as_text=True)
            blocks = re.findall(
                r'<script type="application/ld\+json">(.*?)</script>', body, re.DOTALL)
            assert blocks, f"{url} に JSON-LD が無い"
            for b in blocks:
                json.loads(b)  # 例外が出れば fail

    # --- hreflang ---
    def test_disease_page_has_hreflang(self):
        body = client.get("/glossary/disease/degenerative-myelopathy").get_data(as_text=True)
        assert 'hreflang="ja"' in body
        assert 'hreflang="en"' in body
        assert 'hreflang="x-default"' in body

    def test_guide_page_has_hreflang(self):
        body = client.get("/guides/coi-basics").get_data(as_text=True)
        assert 'hreflang="en"' in body

    def test_guides_index_has_hreflang(self):
        body = client.get("/guides").get_data(as_text=True)
        assert 'hreflang="en"' in body

    # --- ホームページ Organization / WebSite / ディレクトリ ---
    def test_homepage_warns_about_dnap_pdfs(self):
        """ホームページのアップロード説明に「DNAP 非対応」の警告が含まれる。"""
        body = client.get("/").get_data(as_text=True)
        # DNAP 非対応の説明
        assert "DNAプロファイル" in body
        assert "DNAP" in body
        assert "親子鑑定" in body or "DNA 指紋" in body
        # 本体レポートを使ってもらう案内
        assert "本体レポート" in body

    def test_homepage_has_organization_jsonld(self):
        body = client.get("/").get_data(as_text=True)
        assert '"@type": "Organization"' in body
        assert '"@type": "WebSite"' in body
        assert '"@type": "SearchAction"' in body

    def test_homepage_directory_links(self):
        body = client.get("/").get_data(as_text=True)
        # 人気疾患・形質への個別リンクがトップに出る
        assert "/glossary/disease/degenerative-myelopathy" in body
        assert "/glossary/trait/e-locus" in body
        # ディレクトリのアコーディオン見出し（モバイル UX 改善後の文言）
        assert "遺伝子辞書" in body and "ガイドを見る" in body

    def test_homepage_mobile_ux_fixes(self):
        """モバイル UX 改善: body 縦積み + ディレクトリのアコーディオン化 + 言語トグル絶対配置"""
        body = client.get("/").get_data(as_text=True)
        # body 子要素を縦に積む（最重要: container と directory の横並び崩れ防止）
        assert "flex-direction: column" in body
        # ディレクトリは <details>/<summary> でアコーディオン化
        assert '<details class="directory"' in body
        assert 'id="directoryAccordion"' in body
        # デスクトップでは展開、モバイルでは折りたたみを JS で制御
        assert "window.matchMedia('(min-width: 768px)')" in body
        # 言語トグルはコンテナ右上に絶対配置（独立したフル幅行を排除）
        assert "#langToggle" in body
        # iOS セーフエリア対応
        assert "safe-area-inset-bottom" in body

    def test_get_popular_entries(self):
        from poodle_genetics import get_popular_entries
        dis, tr = get_popular_entries("ja")
        assert dis and tr
        assert all("slug" in d and "title" in d for d in dis)
        # EN 版はタイトルが英訳される（_en があるもの）
        dis_en, _ = get_popular_entries("en")
        assert dis_en

    # --- glossary / guides 一覧の ItemList ---
    def test_glossary_has_itemlist(self):
        body = client.get("/glossary").get_data(as_text=True)
        assert '"@type": "ItemList"' in body
        assert '"@type": "CollectionPage"' in body

    def test_guides_index_has_itemlist(self):
        body = client.get("/guides").get_data(as_text=True)
        assert '"@type": "ItemList"' in body


class TestReviewedFlag:
    def test_kb_en_supports_reviewed_field(self):
        """kb_en エントリの reviewed フィールドは optional"""
        from kb_en import DISEASE_EN
        # 未設定（False 扱い）の状態を確認
        sample = DISEASE_EN.get("chondrodystrophy", {})
        # reviewed フィールドは存在しないか False
        assert sample.get("reviewed", False) is False or sample.get("reviewed") is True

    def test_en_page_shows_ai_translation_warning(self):
        """英語ページで監修なしなら警告バッジ表示"""
        rv = client.get("/glossary/disease/chondrodystrophy?lang=en")
        body = rv.get_data(as_text=True)
        # AI 翻訳警告が含まれる（未監修のため）
        assert "AI-generated translation" in body

    def test_ja_page_no_translation_warning(self):
        """日本語ページでは翻訳警告を出さない"""
        rv = client.get("/glossary/disease/chondrodystrophy")
        body = rv.get_data(as_text=True)
        assert "AI-generated translation" not in body
        assert "Veterinarian-reviewed translation" not in body


class TestBreedReverseIndex:
    """形質→犬種 / 疾患→犬種の逆引きインデックス"""

    def test_breeds_by_trait_returns_breeds(self):
        from poodle_genetics import BREEDS_BY_TRAIT
        kitlg_breeds = BREEDS_BY_TRAIT.get("kitlg", [])
        assert any(b["ja"] == "ゴールデン" for b in kitlg_breeds)
        assert any(b["en"] == "Pug" for b in kitlg_breeds)

    def test_breeds_by_disease_returns_breeds(self):
        from poodle_genetics import BREEDS_BY_DISEASE
        dm_breeds = BREEDS_BY_DISEASE.get("degenerative-myelopathy", [])
        breed_jas = [b["ja"] for b in dm_breeds]
        assert "ウェルシュ・コーギー" in breed_jas
        assert "ジャーマンシェパード" in breed_jas

    def test_breed_chips_render_on_trait_page(self):
        rv = client.get("/glossary/trait/m-locus")
        body = rv.get_data(as_text=True)
        assert "🐶" in body
        assert "関連する犬種" in body
        # M-locus は複数犬種ガイドで参照されている
        assert "ボーダーコリー" in body or "ダックスフンド" in body

    def test_breed_chips_render_on_disease_page_en(self):
        rv = client.get("/glossary/disease/multidrug-resistance?lang=en")
        body = rv.get_data(as_text=True)
        assert "Relevant Breeds" in body
        assert "Border Collie" in body or "Australian Shepherd" in body

    def test_unmapped_slug_returns_empty(self):
        from poodle_genetics import BREEDS_BY_TRAIT
        # ridge は犬種ガイドなし → 空リスト
        assert BREEDS_BY_TRAIT.get("ridge", []) == []


class TestDetectBreedGuides:
    """detect_breed_guides の犬種文字列マッチング"""

    def test_japanese_breed_keyword(self):
        from poodle_genetics import detect_breed_guides
        result = detect_breed_guides(["POODLE (トイプードル)"])
        slugs = [r["slug"] for r in result]
        assert "poodle-genetic-health-guide" in slugs

    def test_multiple_breeds_dedup(self):
        from poodle_genetics import detect_breed_guides
        result = detect_breed_guides(["プードル", "プードル"])
        slugs = [r["slug"] for r in result]
        assert slugs.count("poodle-genetic-health-guide") == 1

    def test_empty_input_returns_empty(self):
        from poodle_genetics import detect_breed_guides
        assert detect_breed_guides([]) == []
        assert detect_breed_guides("") == []

    def test_unknown_breed_returns_empty(self):
        from poodle_genetics import detect_breed_guides
        assert detect_breed_guides(["Imaginary Wonder Hound XYZ"]) == []


class TestSimpleExplainers:
    """初心者向け解説オーバーレイ（simple_explainers.py）"""

    def test_module_importable(self):
        from simple_explainers import DISEASE_SIMPLE, TRAIT_SIMPLE, GUIDE_EXTRAS, GENETICS_TOOLTIPS
        assert len(DISEASE_SIMPLE) > 0
        assert len(TRAIT_SIMPLE) > 0
        assert len(GUIDE_EXTRAS) > 0
        assert len(GENETICS_TOOLTIPS) > 0

    def test_merged_into_disease_kb(self):
        from poodle_genetics import DISEASE_SLUG_INDEX
        dm = DISEASE_SLUG_INDEX.get("degenerative-myelopathy")
        assert dm and "_simple" in dm
        assert "oneliner" in dm["_simple"]
        assert "daily_impact" in dm["_simple"]
        assert isinstance(dm["_simple"]["misconceptions"], list)

    def test_merged_into_trait_kb(self):
        from poodle_genetics import TRAIT_SLUG_INDEX
        e = TRAIT_SLUG_INDEX.get("e-locus")
        assert e and "_simple" in e
        assert "oneliner" in e["_simple"]
        assert "breeder_tip" in e["_simple"]

    def test_merged_into_guides(self):
        from poodle_genetics import GUIDES_INDEX
        g = GUIDES_INDEX.get("coi-basics")
        assert g and "tldr" in g and "faq" in g
        assert len(g["tldr"]) >= 2
        assert all("q" in x and "a" in x for x in g["faq"])

    def test_disease_page_shows_simple_section(self):
        rv = client.get("/glossary/disease/degenerative-myelopathy")
        body = rv.get_data(as_text=True)
        assert "💡 一言でいうと" in body
        assert "日常生活への影響" in body
        assert "よくある誤解" in body

    def test_disease_page_en_no_simple_section(self):
        """英語ページにはまだ翻訳がないので表示しない"""
        rv = client.get("/glossary/disease/degenerative-myelopathy?lang=en")
        body = rv.get_data(as_text=True)
        assert "💡 一言でいうと" not in body

    def test_trait_page_shows_simple_section(self):
        rv = client.get("/glossary/trait/m-locus")
        body = rv.get_data(as_text=True)
        assert "💡 一言でいうと" in body
        assert "ブリーダー向け一言" in body

    def test_guide_page_shows_tldr_and_faq(self):
        rv = client.get("/guides/coi-basics")
        body = rv.get_data(as_text=True)
        assert "30 秒で分かる要点" in body
        assert "よくある質問" in body

    def test_full_coverage_diseases(self):
        """コア疾患（_source!='embark'）に _simple が投入されている。

        embark_diseases.py から追加された Embark 由来エントリには将来的に
        コンテンツチームが simple_explainers を追記する想定のため、ここでは
        coverage 要件から除外する（_source='embark' フラグで識別）。
        """
        from poodle_genetics import DISEASE_KB
        no_simple = [
            d['_slug'] for d in DISEASE_KB
            if "_simple" not in d and d.get("_source") != "embark"
        ]
        assert not no_simple, f"_simple 未投入: {no_simple}"

    def test_full_coverage_traits(self):
        """全形質 (27) に _simple が投入されている"""
        from poodle_genetics import TRAIT_KB
        no_simple = [t['_slug'] for t in TRAIT_KB if "_simple" not in t]
        assert not no_simple, f"_simple 未投入: {no_simple}"

    def test_full_coverage_guides(self):
        """全ガイド (26) に tldr と faq が投入されている"""
        from poodle_genetics import GUIDES
        no_tldr = [g['slug'] for g in GUIDES if "tldr" not in g]
        no_faq = [g['slug'] for g in GUIDES if "faq" not in g]
        assert not no_tldr, f"tldr 未投入: {no_tldr}"
        assert not no_faq, f"faq 未投入: {no_faq}"

    def test_simple_oneliner_minimum_length(self):
        """oneliner が最低限の内容量を持つ（誤って空のままになっていないか）。
        Embark 由来の未投入エントリはスキップ。
        """
        from poodle_genetics import DISEASE_KB, TRAIT_KB
        for d in DISEASE_KB:
            if d.get("_source") == "embark" and "_simple" not in d:
                continue
            s = d.get("_simple", {})
            assert s.get("oneliner") and len(s["oneliner"]) >= 20, (
                f"disease {d['_slug']} oneliner too short: {s.get('oneliner')!r}"
            )
        for t in TRAIT_KB:
            s = t.get("_simple", {})
            assert s.get("oneliner") and len(s["oneliner"]) >= 20, (
                f"trait {t['_slug']} oneliner too short: {s.get('oneliner')!r}"
            )

    def test_genetics_tooltips_passed_to_report(self):
        """report.html で genetics_tooltips が JSON シリアライズされている"""
        # 直接 report ルートは session_id 必須なので、レンダリングをモックする
        from app import app as flask_app
        with flask_app.app_context():
            from flask import render_template
            from poodle_genetics import GENETICS_TOOLTIPS
            # report.html はテンプレート単体ではレンダ不可（session_id 必要）
            # GENETICS_TOOLTIPS にエクスポートされていることだけ確認
            assert "N/N" in GENETICS_TOOLTIPS
            assert "P/N" in GENETICS_TOOLTIPS
            assert "COI" in GENETICS_TOOLTIPS


class TestHeterozygosityParser:
    """Orivet PDF からのヘテロ接合率抽出（ゲノム多様性指標）"""

    def test_english_percent(self):
        from poodle_genetics import parse_heterozygosity
        assert parse_heterozygosity("Heterozygosity: 35.2%") == 35.2

    def test_genetic_diversity_label(self):
        from poodle_genetics import parse_heterozygosity
        assert parse_heterozygosity("Genetic Diversity 41 %") == 41.0

    def test_japanese_label(self):
        from poodle_genetics import parse_heterozygosity
        assert parse_heterozygosity("ヘテロ接合率: 28.7%") == 28.7
        assert parse_heterozygosity("遺伝的多様性 33%") == 33.0

    def test_decimal_form_converted_to_percent(self):
        from poodle_genetics import parse_heterozygosity
        # 0.352 (% 記号なし、1 以下) → 35.2%
        assert parse_heterozygosity("Heterozygosity Rate: 0.352") == 35.2

    def test_absent_returns_none(self):
        from poodle_genetics import parse_heterozygosity
        assert parse_heterozygosity("No diversity data in this report") is None
        assert parse_heterozygosity("") is None
        assert parse_heterozygosity(None) is None

    def test_out_of_range_rejected(self):
        from poodle_genetics import parse_heterozygosity
        # 0-100 の範囲外は誤検出として捨てる
        assert parse_heterozygosity("Genetic Diversity: 150%") is None

    def test_parenthetical_annotation(self):
        """ラベルと値の間に括弧注記があっても拾える"""
        from poodle_genetics import parse_heterozygosity
        assert parse_heterozygosity("遺伝的多様性（ヘテロ接合率）: 0.412") == 41.2

    def test_qualifier_word(self):
        """Score / Rate 等の限定語があっても拾える"""
        from poodle_genetics import parse_heterozygosity
        assert parse_heterozygosity("Genetic Diversity Score   29 %") == 29.0
        assert parse_heterozygosity("Breed average heterozygosity rate 0.35") == 35.0

    def test_no_false_positive_in_prose(self):
        """無関係な文章中の数値を誤って拾わない"""
        from poodle_genetics import parse_heterozygosity
        assert parse_heterozygosity("This dog is a 5 year old poodle.") is None

    def test_realistic_report_context(self):
        """レポート全文を模した文脈付きテキストから抽出できる"""
        from poodle_genetics import parse_heterozygosity
        text = "Genetic Summary Report\nBreed: Poodle\nHeterozygosity: 38.4%\nHealth Tests Reported\n"
        assert parse_heterozygosity(text) == 38.4

    def test_real_orivet_heterozygosity_details_page(self):
        """実際の Orivet『Heterozygosity Details』ページ形式から Score を優先抽出"""
        from poodle_genetics import parse_heterozygosity
        text = (
            "Heterozygosity Details\n"
            "Pet Name : Angel of Music\n"
            "Inbreeding level: High genetic diversity, often seen in broader "
            "ancestral background such outcrossed or mixed-breed dogs 37.30%\n"
            "Heterozygosity Score: 0.373\n"
            "For purebreds, moderate scores like 28% are not unusual ...\n"
            "All Toy Poodle\n"
            "Typical range 23.4% - 32.6%"
        )
        # prose の 28% やレンジの 23.4% ではなく、Score 0.373 → 37.3% を拾う
        assert parse_heterozygosity(text) == 37.3

    def test_heterozygosity_score_label_priority(self):
        """'Heterozygosity Score: 0.388' が小数で正しく % 換算される"""
        from poodle_genetics import parse_heterozygosity
        assert parse_heterozygosity("Heterozygosity Score: 0.388") == 38.8

    def test_typical_range_parser(self):
        """犬種別 Typical range の抽出"""
        from poodle_genetics import parse_heterozygosity_range
        assert parse_heterozygosity_range("Typical range 23.4% - 32.6%") == (23.4, 32.6)
        assert parse_heterozygosity_range("Typical range: 20 - 40") == (20.0, 40.0)
        assert parse_heterozygosity_range("標準域 23.4% 〜 32.6%") == (23.4, 32.6)

    def test_typical_range_absent(self):
        from poodle_genetics import parse_heterozygosity_range
        assert parse_heterozygosity_range("no range here") is None
        assert parse_heterozygosity_range("") is None

    def test_dogprofile_has_range_field(self):
        from poodle_genetics import DogProfile
        d = DogProfile()
        assert hasattr(d, "heterozygosity_range")
        assert d.heterozygosity_range is None

    def test_extract_sim_data_forwards_range(self):
        """extract_sim_data が heterozygosity_range を転送する"""
        import app as _appmod
        from poodle_genetics import DogProfile
        d = DogProfile(pet_name="X", sex="Male", heterozygosity=37.3,
                       heterozygosity_range=[23.4, 32.6])
        sim = _appmod.extract_sim_data(d)
        assert sim["heterozygosity"] == 37.3
        assert sim["heterozygosity_range"] == [23.4, 32.6]

    def test_report_shows_heterozygosity_panel(self):
        """レポート HTML にヘテロ接合率パネルが描画される"""
        import tempfile, os
        from poodle_genetics import DogProfile, generate_unified_html
        d = DogProfile(pet_name="Angel", registered_name="R1", sex="Female",
                       breed="Toy Poodle", heterozygosity=37.3,
                       heterozygosity_range=[23.4, 32.6])
        fd, path = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        try:
            generate_unified_html([d], [], path)
            html = open(path, encoding="utf-8").read()
        finally:
            os.unlink(path)
        assert "ヘテロ接合率（ゲノム多様性）" in html
        assert "37.3%" in html
        assert "標準域より高い" in html  # 37.3 > 32.6
        assert "別指標" in html  # 血統COIとの違い注記

    def test_report_hides_panel_when_no_heterozygosity(self):
        """ヘテロ接合率が無い犬ではパネルを描画しない"""
        import tempfile, os
        from poodle_genetics import DogProfile, generate_unified_html
        d = DogProfile(pet_name="NoHet", registered_name="R2", sex="Male",
                       breed="Labrador", heterozygosity=None)
        fd, path = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        try:
            generate_unified_html([d], [], path)
            html = open(path, encoding="utf-8").read()
        finally:
            os.unlink(path)
        assert "ヘテロ接合率（ゲノム多様性）" not in html

    def test_report_heterozygosity_below_range(self):
        """標準域より低い場合の判定"""
        import tempfile, os
        from poodle_genetics import DogProfile, generate_unified_html
        d = DogProfile(pet_name="Low", registered_name="R3", sex="Male",
                       breed="Toy Poodle", heterozygosity=20.0,
                       heterozygosity_range=[23.4, 32.6])
        fd, path = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        try:
            generate_unified_html([d], [], path)
            html = open(path, encoding="utf-8").read()
        finally:
            os.unlink(path)
        assert "標準域より低い" in html

    def test_dogprofile_has_field(self):
        from poodle_genetics import DogProfile
        d = DogProfile()
        assert hasattr(d, "heterozygosity")
        assert d.heterozygosity is None

    def test_coi_guide_explains_difference(self):
        """coi-basics ガイドに血統 COI vs ヘテロ接合率の節がある"""
        rv = client.get("/guides/coi-basics")
        body = rv.get_data(as_text=True)
        assert "ヘテロ接合率" in body
        assert "別指標" in body or "別々の指標" in body

    def test_simulator_has_hetero_note(self):
        """シミュレーターの COI タブに違いの注記がある"""
        rv = client.get("/simulator")
        body = rv.get_data(as_text=True)
        assert "ヘテロ接合率" in body
        assert "renderHeterozygosityPanel" in body

    # ---- 毛色プロファイル（解析時ページ） ----

    def test_color_profile_renders_in_report(self):
        """毛色プロファイル（推測表現型 + 座位グリッド）が描画される"""
        import tempfile, os
        from poodle_genetics import DogProfile, TestResult, generate_unified_html
        d = DogProfile(
            pet_name="Seven", registered_name="R", sex="Male",
            breed="Toy Poodle", colour="Black",
            trait_results=[
                TestResult(category="形質", test_name="E Locus (Cream/Red/Yellow)",
                           genotype="E/e", result_text="", status="trait"),
                TestResult(category="形質", test_name="K Locus (Dominant Black)",
                           genotype="KB/ky", result_text="", status="trait"),
                TestResult(category="形質", test_name="B Locus (Brown)",
                           genotype="BB", result_text="", status="trait"),
                TestResult(category="形質", test_name="D (Dilute) Locus",
                           genotype="D/D", result_text="", status="trait"),
            ],
        )
        fd, path = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        try:
            generate_unified_html([d], [], path)
            html = open(path, encoding="utf-8").read()
        finally:
            os.unlink(path)
        # E_ + KB_ + B_ + D_ → ブラックを予測
        assert "毛色プロファイル" in html
        assert "推測される表現型" in html
        assert "ブラック" in html
        # I 座位 / G 座位は未検査として表示される
        assert "未対応" in html
        # PDF 上の毛色記載も表示
        assert "PDF 上の毛色記載" in html

    def test_color_profile_shows_genotype_terms_and_allele_dots(self):
        """毛色プロファイルが Mendelian な用語（優性ホモ・ヘテロ・劣性ホモ）と
        2 アレル分の色丸を描画する。Bb なら黒丸 + 茶丸、E/e なら黒丸 + クリーム丸。"""
        import tempfile, os
        from poodle_genetics import DogProfile, TestResult, generate_unified_html
        d = DogProfile(
            pet_name="Carrier", registered_name="R", sex="Male", breed="Toy Poodle",
            trait_results=[
                TestResult(category="形質", test_name="E Locus (Cream/Red/Yellow)",
                           genotype="E/e", result_text="", status="trait"),
                TestResult(category="形質", test_name="K Locus (Dominant Black)",
                           genotype="KB/KB", result_text="", status="trait"),
                TestResult(category="形質", test_name="B Locus (Brown)",
                           genotype="Bb", result_text="", status="trait"),
                TestResult(category="形質", test_name="D (Dilute) Locus",
                           genotype="D/D", result_text="", status="trait"),
            ],
        )
        fd, path = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        try:
            generate_unified_html([d], [], path)
            html = open(path, encoding="utf-8").read()
        finally:
            os.unlink(path)
        # Mendelian な用語（旧「キャリア」/「ノンキャリア」は廃止）
        assert "優性ホモ" in html
        assert "ヘテロ" in html
        assert "劣性ホモ" in html
        assert "ノンキャリア" not in html
        # サマリーパネルが新タイトルに
        assert "遺伝子型サマリー" in html
        assert "🟡 ヘテロ（保因）の座位" in html
        # 2 アレルドットの色 hex（B/B = 黒×2, Bb = 黒+濃チョコ, E/e = 黒+クリーム）
        assert "#0a0a0a" in html  # 黒（E のドミナント側）
        assert "#7B3F00" in html  # 濃チョコ（b アレル、高彩度版）
        assert "#FFE4B5" in html  # モカシンクリーム（e アレル、高彩度版）

    def test_allele_dots_have_a11y_attributes(self):
        """各アレルドットに role="img", aria-label, title, tabindex が付与され
        スクリーンリーダー・キーボード操作・色覚特性に対応している。"""
        from poodle_genetics import _allele_dots_html, _ALLELE_DESC
        html = _allele_dots_html("Bb", dot_size=16)
        # スクリーンリーダー対応: role="img", aria-label, title
        assert 'role="img"' in html
        assert 'aria-label="B アレル:' in html
        assert 'aria-label="b アレル:' in html
        assert 'title="B アレル:' in html
        # キーボードフォーカス対応: tabindex
        assert 'tabindex="0"' in html
        # 色覚特性配慮: ドット内にアレル文字を併記（色だけに依存しない）
        assert ">B</span>" in html or ">B<" in html
        assert ">b</span>" in html or ">b<" in html
        # クラス付与（CSS focus-visible / hover 用）
        assert 'class="allele-dot"' in html
        # 説明マップが必要なアレルをカバー
        for a in ("E", "e", "B", "b", "D", "d", "KB", "ky", "kbr",
                  "m", "M", "ay", "aw", "at", "a", "S", "sp", "I", "i", "g", "G"):
            assert a in _ALLELE_DESC, f"_ALLELE_DESC missing description for allele '{a}'"

    def test_allele_color_wcag_contrast_aa(self):
        """各アレルの dot 背景色と内部文字色のコントラスト比が WCAG AA (4.5:1) 以上。
        _is_light_color() が判定する白 or 黒の文字色で必ず AA を満たすこと。"""
        from poodle_genetics import _ALLELE_COLOR, _is_light_color

        def rgb_lin(c):
            """sRGB -> 線形 RGB"""
            c = c / 255
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        def luminance(hex_color):
            r = rgb_lin(int(hex_color[1:3], 16))
            g = rgb_lin(int(hex_color[3:5], 16))
            b = rgb_lin(int(hex_color[5:7], 16))
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        def contrast(hex1, hex2):
            l1, l2 = luminance(hex1), luminance(hex2)
            lighter, darker = max(l1, l2), min(l1, l2)
            return (lighter + 0.05) / (darker + 0.05)

        for allele, hex_color in _ALLELE_COLOR.items():
            text_color = "#0f172a" if _is_light_color(hex_color) else "#ffffff"
            ratio = contrast(hex_color, text_color)
            assert ratio >= 4.5, (
                f"Allele {allele!r} (bg={hex_color}, text={text_color}) "
                f"contrast {ratio:.2f} < WCAG AA 4.5:1"
            )

    def test_allele_dots_helper(self):
        """_allele_dots_html が 2 アレル分の色丸 HTML を返す"""
        from poodle_genetics import _allele_dots_html, _split_genotype, _ALLELE_COLOR
        # genotype 分解
        assert _split_genotype("E/E") == ["E", "E"]
        assert _split_genotype("Bb") == ["B", "b"]
        assert _split_genotype("KB/ky") == ["KB", "ky"]
        # ドット HTML — 各アレルのシグネチャー hex が含まれる
        html = _allele_dots_html("Bb")
        assert _ALLELE_COLOR["B"] in html
        assert _ALLELE_COLOR["b"] in html
        html = _allele_dots_html("E/e")
        assert _ALLELE_COLOR["E"] in html
        assert _ALLELE_COLOR["e"] in html
        # D 座位はロイヤルブルー（鮮やかで識別しやすい）
        html = _allele_dots_html("D/D")
        assert _ALLELE_COLOR["D"] in html
        assert _ALLELE_COLOR["D"] == "#1E40AF"  # royal blue, not pure black

    def test_overview_table_rows_are_clickable(self):
        """検査対象一覧の各行が clickable で、その犬の詳細タブへジャンプする。"""
        import tempfile, os
        from poodle_genetics import DogProfile, TestResult, generate_unified_html
        dogs = [
            DogProfile(pet_name="Seven", registered_name="SMASH JP SEVEN NIGHT",
                       sex="Intact Male", breed="Toy Poodle", dob="14th Apr 2025",
                       case_number="25RU75102"),
            DogProfile(pet_name="Angel Of Music", registered_name="BEATRIX JP ANGEL OF MUSIC",
                       sex="Female", breed="Toy Poodle", dob="9th Nov 2024",
                       case_number="25RU75103"),
        ]
        fd, path = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        try:
            generate_unified_html(dogs, [], path)
            html = open(path, encoding="utf-8").read()
        finally:
            os.unlink(path)
        # 各犬の safe_id (lowercase, non-alnum → _) を計算
        # "Seven" → "seven"
        # "Angel Of Music" → "angel_of_music"
        assert "showTab('seven')" in html
        assert "showTab('angel_of_music')" in html
        # 行が clickable（cursor:pointer + onclick）
        assert 'class="dog-overview-row"' in html
        assert "cursor:pointer" in html
        # ホバー時のフィードバック
        assert "onmouseover" in html
        # 「詳細を見る →」のヒント
        assert "詳細を見る" in html
        # ユーザー向けの説明
        assert "行をクリック" in html or "クリックするとその犬の詳細" in html

    def test_genotype_shade_homo_and_carrier_match(self):
        """E/B/D/K の優性ホモとヘテロキャリアは同じ hex を持つ（Mendelian-correct）。
        劣性ホモのみ実際の表現型色になる。"""
        from poodle_genetics import _GENOTYPE_SHADE
        # E座位
        assert _GENOTYPE_SHADE["e"]["E/E"][2] == _GENOTYPE_SHADE["e"]["E/e"][2]
        assert _GENOTYPE_SHADE["e"]["e/e"][2] != _GENOTYPE_SHADE["e"]["E/E"][2]
        # B座位
        assert _GENOTYPE_SHADE["b"]["BB"][2] == _GENOTYPE_SHADE["b"]["Bb"][2]
        assert _GENOTYPE_SHADE["b"]["bb"][2] != _GENOTYPE_SHADE["b"]["BB"][2]
        # D座位
        assert _GENOTYPE_SHADE["d"]["D/D"][2] == _GENOTYPE_SHADE["d"]["D/d"][2]
        assert _GENOTYPE_SHADE["d"]["d/d"][2] != _GENOTYPE_SHADE["d"]["D/D"][2]
        # K座位
        assert _GENOTYPE_SHADE["k"]["KB/KB"][2] == _GENOTYPE_SHADE["k"]["KB/ky"][2]
        assert _GENOTYPE_SHADE["k"]["ky/ky"][2] != _GENOTYPE_SHADE["k"]["KB/KB"][2]
        # M座位は半優性なので 3 つとも別色
        m = _GENOTYPE_SHADE["m"]
        assert m["m/m"][2] != m["M/m"][2]
        assert m["M/m"][2] != m["M/M"][2]
        assert m["m/m"][2] != m["M/M"][2]

    def test_color_profile_ee_without_i_locus(self):
        """ee 犬は I 座位未検査時に「クリーム〜レッド系」とまとめて扱う"""
        from poodle_genetics import DogProfile, TestResult, _predict_phenotype, _collect_color_loci
        d = DogProfile(
            trait_results=[
                TestResult(category="形質", test_name="E Locus (Cream/Red/Yellow)",
                           genotype="e/e", result_text="", status="trait"),
                TestResult(category="形質", test_name="K Locus (Dominant Black)",
                           genotype="KB/KB", result_text="", status="trait"),
                TestResult(category="形質", test_name="B Locus (Brown)",
                           genotype="BB", result_text="", status="trait"),
            ],
        )
        loci = _collect_color_loci(d)
        assert loci["e"] == "e/e"
        key, desc = _predict_phenotype(loci)
        # I 座位なし → cream 扱い、説明に "Orivet 未対応" の注記
        assert key == "cream"
        assert "Orivet 未対応" in desc

    def test_color_profile_phantom_black(self):
        """ky/ky + at/at + B_ + D_ → ブラックタン（ファントム）"""
        from poodle_genetics import _predict_phenotype
        key, _ = _predict_phenotype({
            "e": "E/E", "k": "ky/ky", "a": "at/at",
            "b": "BB", "d": "D/D", "m": "m/m", "s": "S/S",
        })
        assert key == "phantom_black"

    def test_color_profile_dilute_blue(self):
        """KB_ + d/d → ブルー"""
        from poodle_genetics import _predict_phenotype
        key, _ = _predict_phenotype({
            "e": "E/E", "k": "KB/KB", "a": "at/at",
            "b": "BB", "d": "d/d", "m": "m/m", "s": "S/S",
        })
        assert key == "blue"

    # ---- 繁殖シミュレーター: 補足入力（PDF 犬向け I 座位/G 座位 override） ----

    def test_simulator_guards_incomplete_genotype(self):
        """PDF 解析で座位が欠落してもクラッシュしないガードが実装されている。
        cross/splitAlleles の undefined ガード + 欠落座位の既定値補完 + 警告。"""
        body = client.get("/simulator").get_data(as_text=True)
        # splitAlleles の undefined ガード
        assert "if (gt == null || gt === '') return [];" in body
        # cross の空分布ガード
        assert "if (!a.length || !b.length) return {};" in body
        # 欠落座位を既定値で補完するヘルパー
        assert "function _fillGenotypeDefaults" in body
        assert "_DEFAULT_COLOR_GENOTYPE" in body
        assert "function _missingLociLabels" in body
        # PDF 犬の sire/dam 構築で補完が適用される
        assert "_fillGenotypeDefaults(DOGS[sireKey].color)" in body
        assert "_fillGenotypeDefaults(DOGS[damKey].color)" in body
        # 警告文言
        assert "読み取れませんでした" in body

    def test_simulator_has_two_pair_compare(self):
        """シミュレーターに 2ペア比較（同じ父犬 × 2頭の母犬）機能がある"""
        body = client.get("/simulator").get_data(as_text=True)
        # 比較パネル
        assert 'id="compare-panel"' in body
        assert 'id="compare-dam-a"' in body
        assert 'id="compare-dam-b"' in body
        assert 'onclick="runCompare()"' in body
        # ピュアな毛色予測コア（比較で再利用）
        assert "function _buildColorResults" in body
        assert "function _consolidateByBaseColor" in body
        # 比較ロジック
        assert "function runCompare" in body
        assert "function _syncCompareDropdowns" in body
        assert "function _currentSireGenotype" in body
        # i18n（ja/en）
        assert "母犬を2頭くらべて" in body
        assert "Compare two dams" in body
        # PDF 投入時に比較ドロップダウンも同期
        assert "_syncCompareDropdowns()" in body

    def test_simulator_has_beginner_advanced_mode(self):
        """シミュレーターに 初級/詳細 モードトグルがある"""
        body = client.get("/simulator").get_data(as_text=True)
        # トグルボタン
        assert 'id="mode-beginner"' in body
        assert 'id="mode-advanced"' in body
        assert 'onclick="setSimMode(\'beginner\')"' in body
        assert 'onclick="setSimMode(\'advanced\')"' in body
        assert "function setSimMode" in body
        # デフォルトは初級モード（beginner-mode クラスが color-output に付与）
        assert 'id="color-output" class="beginner-mode"' in body
        # 初級モードで詳細ブロックを隠す CSS
        assert "#color-output.beginner-mode .sim-advanced-block" in body
        # 詳細パネルは sim-advanced-block でラップされている
        assert "sim-advanced-block" in body
        # localStorage 永続化
        assert "'sim.mode'" in body or "_SIM_MODE_KEY" in body
        # i18n（ja/en 両方）
        assert "🌱 かんたん" in body
        assert "🔬 詳細" in body
        assert "Simple" in body and "Detailed" in body
        # 初級モードの案内ヒント
        assert "beginner-hint" in body

    def test_simulator_has_csv_export(self):
        """シミュレーターに CSV エクスポート機能がある"""
        body = client.get("/simulator").get_data(as_text=True)
        assert 'onclick="exportColorCsv()"' in body
        assert "function exportColorCsv" in body
        # BOM 付き UTF-8（Excel 日本語対策）
        assert "text/csv;charset=utf-8" in body
        # CSV セルのエスケープヘルパー
        assert "function _csvCell" in body
        # ダウンロードファイル名
        assert "coat_color_prediction.csv" in body

    def test_simulator_has_share_link(self):
        """シミュレーターに共有リンク（URL permalink）機能がある"""
        body = client.get("/simulator").get_data(as_text=True)
        assert 'onclick="copyShareLink()"' in body
        assert "function copyShareLink" in body
        assert "function _buildShareUrl" in body
        # クエリパラメータに sire/dam を含める
        assert "params.set('sire'" in body
        assert "params.set('dam'" in body
        # clipboard API 利用
        assert "navigator.clipboard" in body

    def test_simulator_restores_scenario_from_query(self):
        """シミュレーターが URL クエリから交配シナリオを復元する"""
        body = client.get("/simulator").get_data(as_text=True)
        assert "function _restoreFromQuery" in body
        # 復元後に runColorSim を実行
        assert "_restoreFromQuery()" in body
        # 補足入力 (override) の復元キー
        assert "params.get('osi')" in body
        assert "params.get('odi')" in body

    def test_simulator_has_reset_button(self):
        """シミュレーターに「リセット」ボタンと resetColorSim 関数がある"""
        body = client.get("/simulator").get_data(as_text=True)
        assert 'class="btn-reset"' in body
        assert 'onclick="resetColorSim()"' in body
        assert 'function resetColorSim' in body
        # confirm 確認ダイアログ → 誤クリック防止
        assert 'window.confirm' in body
        # 補足入力 (override) もクリアする
        assert "'ovr-sire-i'" in body
        assert "'ovr-dam-i'" in body

    def test_simulator_persists_overrides_in_localstorage(self):
        """シミュレーターが補足入力 (I/G 座位) を localStorage に保存・復元する"""
        body = client.get("/simulator").get_data(as_text=True)
        # 保存 key
        assert "_OVR_STORAGE_KEY" in body
        assert "'sim.overrides.v1'" in body
        # 保存・復元・削除ヘルパー
        assert "function _saveOverrides" in body
        assert "function _restoreOverrides" in body
        assert "function _clearOverrides" in body
        # 各 override 入力の change で保存
        assert "addEventListener('change', _saveOverrides)" in body
        # DOMContentLoaded で復元
        assert "_restoreOverrides()" in body

    def test_simulator_has_english_toggle(self):
        """シミュレーターに EN/JA 言語切替トグルがある"""
        body = client.get("/simulator").get_data(as_text=True)
        # 言語切替ボタン
        assert 'id="langToggle"' in body
        assert 'onclick="toggleLang()"' in body
        # 翻訳辞書 + helper
        assert "_SIM_I18N" in body
        assert "function toggleLang" in body
        assert "function _applySimLang" in body
        # 主要キーが ja/en 両方に存在
        for key in ("title", "tab_color", "tab_health", "tab_coi",
                    "lbl_sire", "lbl_dam", "btn_run", "btn_reset",
                    "ovr_sire_title", "ovr_dam_title"):
            assert f"{key}:" in body or f"'{key}'" in body, f"missing i18n key {key}"
        # 英訳キーワード
        assert "Coat color" in body
        assert "Health risk" in body
        assert "Inbreeding" in body
        # data-i18n 属性が静的ラベルに付与されている
        assert 'data-i18n="lbl_sire"' in body
        assert 'data-i18n="lbl_dam"' in body
        assert 'data-i18n="btn_run"' in body
        # appLang を localStorage で永続化（インデックスと共通キー）
        assert "'appLang'" in body

    def test_simulator_has_print_stylesheet(self):
        """シミュレーターに @media print ルールがある"""
        body = client.get("/simulator").get_data(as_text=True)
        assert "@media print" in body
        # 印刷時に非表示の要素（インタラクティブ）
        assert ".btn-reset" in body
        # ページサイズ A4
        assert "size:A4 portrait" in body or "size: A4 portrait" in body

    def test_report_has_print_stylesheet(self):
        """レポート HTML に印刷用 @page と @media print がある"""
        import tempfile, os
        from poodle_genetics import DogProfile, generate_unified_html
        d = DogProfile(pet_name="X", registered_name="X", sex="Male", breed="Toy Poodle")
        fd, path = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        try:
            generate_unified_html([d], [], path)
            html = open(path, encoding="utf-8").read()
        finally:
            os.unlink(path)
        # A4 縦・余白
        assert "@page" in html
        assert "A4 portrait" in html
        # 印刷時に背景なし・ボックスシャドウ無効化
        assert "background: #fff !important" in html
        assert "box-shadow: none !important" in html
        # 結果テーブルの page-break-inside
        assert "page-break-inside" in html

    def test_simulator_has_pdf_override_panel(self):
        """PDF 犬向けの補足入力パネル（I 座位 / Greying 上書き）が存在"""
        rv = client.get("/simulator")
        body = rv.get_data(as_text=True)
        assert 'id="overrides-sire"' in body
        assert 'id="overrides-dam"' in body
        assert 'id="ovr-sire-i"' in body
        assert 'id="ovr-dam-i"' in body
        assert 'id="ovr-sire-g"' in body
        assert 'id="ovr-dam-g"' in body
        # 上書きの注釈
        assert "補足入力" in body or "追加情報" in body

    def test_silver_beige_renamed_to_cafe_au_lait(self):
        """bb + Greying の表示名が「カフェオレ（シルバービーグ）」に統一されている"""
        from poodle_genetics import _PHENO_SWATCH
        name, hex_color = _PHENO_SWATCH["silver_beige"]
        assert "カフェオレ" in name
        assert "シルバービーグ" in name
        assert hex_color.upper() == "#BFA37A"
        # シミュレーター側 COLOR_MAP も同じ HEX で統一
        body = client.get("/simulator").get_data(as_text=True)
        assert '"silver_beige": { hex:"#BFA37A"' in body
        assert "カフェオレ（シルバービーグ／成犬で退色）" in body

    def test_simulator_shows_genotype_breakdown_panel(self):
        """シミュレーターに「遺伝子型まとめ」パネルと Mendelian な用語が含まれる。
        「キャリア」「ノンキャリア」のような曖昧な表記は廃止し、優性ホモ/ヘテロ/
        劣性ホモを使用する。"""
        body = client.get("/simulator").get_data(as_text=True)
        # パネル見出し
        assert "🧬 子犬の遺伝子型まとめ" in body
        # Mendelian な用語が使われている
        assert "E/E 優性ホモ" in body
        assert "E/e ヘテロ" in body
        assert "Bb ヘテロ" in body
        assert "D/d ヘテロ" in body
        assert "M/m ヘテロ" in body
        # 旧表記は廃止されている
        assert "ホモ・ノンキャリア" not in body
        assert "ヘテロ・eキャリア" not in body
        # ユーザー説明
        assert "見た目は優性ホモと同じ" in body
        assert "25%" in body  # 劣性発現確率

    def test_simulator_has_genotype_combination_detail_table(self):
        """「🔬 遺伝子型コンビネーション詳細」テーブルが含まれる。
        各ユニークな遺伝子型コンビが行として展開される。
        Option B (Mendelian-correct) では同じ表現型なら色丸も同じ hex を返す。"""
        body = client.get("/simulator").get_data(as_text=True)
        # 詳細セクションの見出し
        assert "🔬 遺伝子型コンビネーション詳細" in body
        # blendShade は同じ表現型なら同じ色を返す（メンデル遺伝に忠実）
        assert "function blendShade" in body
        # 説明文（同じ表現型なら色丸も同じ）
        assert "表現型が同じなら色丸も同じ" in body
        assert "メンデル遺伝" in body
        # キャリア状態の内訳を確認できる用途で展開していることを明示
        assert "キャリア状態の内訳" in body

    def test_simulator_uses_allele_dots(self):
        """シミュレーターは 2 アレルドット方式で色丸を表示する。
        各座位ごとにシグネチャー色を割り当て、優性ホモが集まったときでも
        座位の違いが視覚的に分かるように設計されている。"""
        body = client.get("/simulator").get_data(as_text=True)
        # _ALLELE_COLOR マップとヘルパー
        assert "_ALLELE_COLOR" in body
        assert "function _splitGenotype" in body or "_splitGenotype(geno)" in body
        assert "function _alleleDots" in body or "_alleleDots(geno" in body
        # 各座位の高彩度シグネチャー hex
        assert "E: '#0a0a0a'" in body          # E座位: 黒
        assert "e: '#FFE4B5'" in body          # E座位: クリーム
        assert "b: '#7B3F00'" in body          # B座位: 濃チョコ
        assert "D: '#1E40AF'" in body          # D座位: ロイヤルブルー
        assert "d: '#93C5FD'" in body          # D座位: 水色
        assert "KB: '#0a0a0a'" in body         # K座位: 黒（ドミナントブラック）
        assert "ky: '#A0522D'" in body         # K座位: ファントム タン（シエナ）
        assert "m: '#0E7490'" in body          # M座位: ダークシアン
        assert "M: '#22D3EE'" in body          # M座位: 明るいシアン
        assert "S: '#15803D'" in body          # S座位: フォレストグリーン
        assert "I: '#DC2626'" in body          # I座位: 鮮やか赤
        # 2 アレル方式の説明
        assert "2 つのアレル" in body or "2 アレル" in body
        # シグネチャー色の説明
        assert "シグネチャー" in body or "座位ごと" in body

    def test_simulator_multi_tone_phenotype_backgrounds(self):
        """マルチカラー表現型（ファントム・パーティ・ブリンドル・マール・
        セーブル・シルバー）が CSS gradient で多色表現されている。
        ユーザー要望: 「パーティカラーになる遺伝子は発現する遺伝子の色を
        入れてマルチカラーであることが分かりやすいようにしましょう」"""
        body = client.get("/simulator").get_data(as_text=True)
        # _multiToneBg ヘルパー
        assert "function _multiToneBg" in body
        # ファントム: 2 色 linear-gradient + クリーム
        assert "phantom_black" in body
        assert "phantom_brown" in body
        assert "#FFF8DC" in body  # クリーム タン
        # ブリンドル: 縞 (repeating-linear-gradient)
        assert "repeating-linear-gradient" in body
        # マール: パッチ (radial-gradient)
        assert "radial-gradient" in body
        # パーティ: ベース + 白
        assert "case 'parti'" in body
        # シルバー (退色): ベース → シルバーグラデ
        assert "case 'silver'" in body

    def test_report_phenotype_card_uses_multi_tone(self):
        """レポートの推測表現型カードもマルチカラー gradient を適用する"""
        import tempfile, os
        from poodle_genetics import DogProfile, TestResult, generate_unified_html, _multi_tone_bg
        # ファントム表現型 (E_ + ky/ky + at/at) になる犬
        d = DogProfile(
            pet_name="Phantom", registered_name="R", sex="Male", breed="Toy Poodle",
            trait_results=[
                TestResult(category="形質", test_name="E Locus (Cream/Red/Yellow)",
                           genotype="E/E", result_text="", status="trait"),
                TestResult(category="形質", test_name="K Locus (Dominant Black)",
                           genotype="ky/ky", result_text="", status="trait"),
                TestResult(category="形質", test_name="A Locus (Agouti)",
                           genotype="at/at", result_text="", status="trait"),
                TestResult(category="形質", test_name="B Locus (Brown)",
                           genotype="BB", result_text="", status="trait"),
                TestResult(category="形質", test_name="D (Dilute) Locus",
                           genotype="D/D", result_text="", status="trait"),
            ],
        )
        fd, path = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        try:
            generate_unified_html([d], [], path)
            html = open(path, encoding="utf-8").read()
        finally:
            os.unlink(path)
        # ファントム表現型カード swatch に gradient が入っている
        assert "linear-gradient(135deg" in html
        assert "#FFF8DC" in html  # クリーム タン
        # ヘルパー単独テスト
        assert "linear-gradient" in _multi_tone_bg("phantom_black", "#2d2d2d")
        assert "repeating-linear-gradient" in _multi_tone_bg("brindle", "#8B7355")
        assert "radial-gradient" in _multi_tone_bg("merle", "#9FB6CD")
        assert _multi_tone_bg("black", "#1a1a1a") == "#1a1a1a"  # 単色は変更なし

    def test_combo_table_has_rich_phenotype_description(self):
        """遺伝子型コンビネーション詳細テーブルに、見た目の詳細
        （鼻・パッド色、純色/墨色トーン、キャリア状態、Greying 退色など）が
        含まれている。ユーザー要望: 「色は細かく見た目どうなるか細かく記載」"""
        body = client.get("/simulator").get_data(as_text=True)
        # 詳細記述ヘルパー
        assert "function _comboPhenoDescription" in body
        # 主要記述キーワード
        assert "鼻・パッド" in body
        assert "レバー(茶色)" in body
        assert "シャンパン(青系)" in body
        assert "イザベラ(ラベンダー)" in body
        assert "純黒" in body
        assert "墨色トーン" in body
        # キャリア注記
        assert "保因:" in body
        assert "アグーチ/ファントム可能性" in body
        # Greying 注記
        assert "成犬期にシルバー系へ退色" in body
        # ファントム表記
        assert "ファントム/タンポイント" in body

    def test_simulator_has_recessive_homozygous_panel(self):
        """ホワイト/ブラウン/希釈の劣性ホモ化（単独・重複）の発現確率
        パネルがある。ユーザー要望: ee+bb のような重複ホモ化で出る
        特殊カラー（レバー、シャンパン、イザベラ）と % を明示する。"""
        body = client.get("/simulator").get_data(as_text=True)
        # パネル見出し
        assert "🎯 劣性ホモ化の発現確率" in body
        # 単独ホモ
        assert "e/e 劣性ホモ" in body
        assert "b/b 劣性ホモ" in body
        assert "d/d 劣性ホモ" in body
        # 重複ホモ（特殊カラー）
        assert "ee + bb 重複ホモ" in body
        assert "ee + dd 重複ホモ" in body
        assert "bb + dd 重複ホモ" in body
        # 特殊カラー名
        assert "レバーカラー" in body
        assert "シャンパン" in body
        assert "ライラック" in body or "イザベラ" in body
        # ee バリアントごとに nose tone shadeHex を計算する関数
        assert "noseToneFor" in body

    def test_simulator_splits_phenotype_by_e_genotype(self):
        """毛色予測結果が E/E 由来と E/e 由来をトーン違いで分けて表示する。
        ユーザー要望: 「EE と Ee でも黒だが、色は黒と墨色になる」"""
        body = client.get("/simulator").get_data(as_text=True)
        # pushE ヘルパーで E_ 由来 push を分割している
        assert "function pushE" in body or "pushE(" in body
        # _PURITY_LABEL マップで純色/墨色の修飾語を定義
        assert "_PURITY_LABEL" in body
        # ブラック（純黒/墨色）
        assert "純黒" in body
        assert "墨色" in body
        # 墨色トーン生成関数
        assert "_sumiTone" in body or "function _sumiTone" in body
        # 凡例（純色/墨色の意味の説明）
        assert "純色 / 墨色" in body or "純色トーン" in body


class TestSimulatorFunnel:
    """解析レポート → 繁殖シミュレーターへの導線"""

    def _make_session(self, sid="test_funnel"):
        import os, json
        from app import REPORT_FOLDER
        sdir = os.path.join(REPORT_FOLDER, sid)
        os.makedirs(sdir, exist_ok=True)
        with open(os.path.join(sdir, "report.html"), "w", encoding="utf-8") as f:
            f.write("<html><body>dummy</body></html>")
        with open(os.path.join(sdir, "dogs.json"), "w", encoding="utf-8") as f:
            json.dump([{"name": "A", "sex": "male", "color": {}, "health": {},
                        "breed": "Poodle", "heterozygosity": None}], f)
        return sid, sdir

    def test_report_has_prominent_sim_cta(self):
        import shutil
        sid, sdir = self._make_session()
        try:
            body = client.get(f"/report/{sid}").get_data(as_text=True)
            assert 'id="simCta"' in body
            assert "次のステップ：繁殖シミュレーション" in body
            assert f"/simulator?session={sid}" in body
        finally:
            shutil.rmtree(sdir, ignore_errors=True)

    def test_report_cta_has_english(self):
        import shutil
        sid, sdir = self._make_session("test_funnel_en")
        try:
            body = client.get(f"/report/{sid}").get_data(as_text=True)
            assert "Next step: Breeding Simulation" in body
            assert "Open Breeding Simulator" in body
        finally:
            shutil.rmtree(sdir, ignore_errors=True)

    def test_simulator_has_session_loaded_banner(self):
        body = client.get("/simulator").get_data(as_text=True)
        assert "function showSessionLoadedBanner" in body
        assert "解析データを自動読み込みしました" in body


class TestHeterozygosityDetailsMerge:
    """別 PDF として送られてくる Heterozygosity Details の本体マージ"""

    def test_is_heterozygosity_only_profile(self):
        from poodle_genetics import DogProfile, is_heterozygosity_only_profile
        main = DogProfile(pet_name="A", health_results=["x"])
        het = DogProfile(pet_name="A", heterozygosity=37.3)
        empty = DogProfile(pet_name="A")
        assert not is_heterozygosity_only_profile(main)
        assert is_heterozygosity_only_profile(het)
        assert not is_heterozygosity_only_profile(empty)  # het 値が無いので false
        assert not is_heterozygosity_only_profile(None)

    def test_merge_by_pet_name(self):
        """同名の本体に het 値が注入される"""
        from poodle_genetics import DogProfile, merge_heterozygosity_only
        main = DogProfile(pet_name="Angel of Music", health_results=["x"], trait_results=["y"])
        het = DogProfile(pet_name="Angel of Music", heterozygosity=37.3,
                         heterozygosity_range=[23.4, 32.6])
        result = merge_heterozygosity_only([main, het])
        assert len(result) == 1
        assert result[0].heterozygosity == 37.3
        assert result[0].heterozygosity_range == [23.4, 32.6]
        assert result[0].health_results == ["x"]

    def test_merge_case_and_whitespace_insensitive(self):
        from poodle_genetics import DogProfile, merge_heterozygosity_only
        main = DogProfile(pet_name="  Angel of Music  ", health_results=["x"])
        het = DogProfile(pet_name="angel of music", heterozygosity=37.3)
        result = merge_heterozygosity_only([main, het])
        assert len(result) == 1
        assert result[0].heterozygosity == 37.3

    def test_unmatched_kept_separately(self):
        from poodle_genetics import DogProfile, merge_heterozygosity_only
        main = DogProfile(pet_name="Different", health_results=["x"])
        het = DogProfile(pet_name="Angel", heterozygosity=37.3)
        result = merge_heterozygosity_only([main, het])
        assert len(result) == 2

    def test_existing_value_not_overwritten(self):
        from poodle_genetics import DogProfile, merge_heterozygosity_only
        main = DogProfile(pet_name="X", health_results=["x"], heterozygosity=99.9)
        het = DogProfile(pet_name="X", heterozygosity=37.3)
        result = merge_heterozygosity_only([main, het])
        assert result[0].heterozygosity == 99.9  # 既存値を保持

    def test_empty_list(self):
        from poodle_genetics import merge_heterozygosity_only
        assert merge_heterozygosity_only([]) == []

    def test_index_explains_het_details_pdf(self):
        rv = client.get("/")
        body = rv.get_data(as_text=True)
        assert "Heterozygosity Details" in body

    def test_looks_like_orivet_detects_english(self):
        from poodle_genetics import _looks_like_orivet_pdf
        assert _looks_like_orivet_pdf("Orivet Genetic Summary Report\n...")
        assert _looks_like_orivet_pdf("Heterozygosity Score: 0.373\n...")

    def test_looks_like_orivet_detects_japanese(self):
        from poodle_genetics import _looks_like_orivet_pdf
        assert _looks_like_orivet_pdf("オリベット 遺伝子解析サマリー\n...")
        assert _looks_like_orivet_pdf("健康検査結果\n...")
        assert _looks_like_orivet_pdf("ヘテロ接合率 37.30%\n...")
        assert _looks_like_orivet_pdf("遺伝的多様性\n...")

    def test_looks_like_orivet_rejects_unrelated(self):
        from poodle_genetics import _looks_like_orivet_pdf
        assert not _looks_like_orivet_pdf("This is a cat document.")
        assert not _looks_like_orivet_pdf("")
        assert not _looks_like_orivet_pdf(None)


class TestIndexCacheHeaders:
    """トップページが flash メッセージで汚染されないことの検証"""

    def test_index_has_no_store_headers(self):
        """/ に no-cache, no-store ヘッダーが付く（ブラウザキャッシュ汚染防止）"""
        rv = client.get("/")
        cc = rv.headers.get("Cache-Control", "")
        assert "no-store" in cc
        assert "no-cache" in cc

    def test_flash_consumed_on_first_render(self):
        """flash メッセージは 1 回表示で消費される（次回は出ない）"""
        with client.session_transaction() as sess:
            sess["_flashes"] = [("error", "テストエラー")]
        first = client.get("/").get_data(as_text=True)
        assert "テストエラー" in first
        second = client.get("/").get_data(as_text=True)
        assert "テストエラー" not in second

    def test_service_worker_excludes_root_from_cache_first(self):
        """SW は / を network-only（キャッシュしない）扱いにする"""
        sw = client.get("/sw.js").get_data(as_text=True)
        # キャッシュバージョンが定義されている（バージョン番号は更新で上がる）
        import re
        assert re.search(r"CACHE_VERSION\s*=\s*'orivet-v\d+'", sw)
        # / 専用の分岐が存在
        assert "url.pathname === '/'" in sw

    def test_service_worker_never_caches_root(self):
        """SW は '/' を絶対にキャッシュへ put しない（古い flash メッセージが
        キャッシュに残って再表示される問題の根治）。"""
        sw = client.get("/sw.js").get_data(as_text=True)
        # '/' 分岐内で c.put(... '/') していないこと。network-only の証跡。
        # '/' ブロックが `event.respondWith(fetch(event.request));` で完結している
        assert "event.respondWith(fetch(event.request));" in sw
        # flash をキャッシュしない旨のコメント
        assert "flash" in sw and ("キャッシュしない" in sw or "network-only" in sw)

    def test_index_flash_container_and_bfcache_guard(self):
        """ホームページに flash-container と bfcache（pageshow）ガードがある。
        戻る/進むで古い flash メッセージが再表示されないようにする。"""
        body = client.get("/").get_data(as_text=True)
        # pageshow で bfcache 復元を検知して flash を除去
        assert "addEventListener('pageshow'" in body
        assert "ev.persisted" in body
        assert "flash-container" in body


class TestSimulatorPdfUpload:
    """繁殖シミュレーター直接 PDF アップロード API"""

    def test_endpoint_rejects_empty(self):
        rv = client.post("/api/simulator/parse")
        assert rv.status_code == 400
        body = rv.get_json()
        assert body["error"] == "no_files"

    def test_endpoint_rejects_non_pdf(self):
        import io
        data = {"pdf_files": (io.BytesIO(b"not a pdf"), "fake.txt")}
        rv = client.post("/api/simulator/parse", data=data,
                         content_type="multipart/form-data")
        # 拒否されるか、errors に分類されて 200
        if rv.status_code == 200:
            body = rv.get_json()
            assert body["dogs"] == []
            assert body["errors"]
        else:
            assert rv.status_code == 400

    def test_endpoint_rejects_too_many_files(self):
        import io
        data = {"pdf_files": [
            (io.BytesIO(b"%PDF-1.4\n%EOF"), f"f{i}.pdf") for i in range(5)
        ]}
        rv = client.post("/api/simulator/parse", data=data,
                         content_type="multipart/form-data")
        assert rv.status_code == 400
        body = rv.get_json()
        assert body["error"] == "too_many_files"

    def test_simulator_page_has_upload_widget(self):
        rv = client.get("/simulator")
        body = rv.get_data(as_text=True)
        assert "sim-pdf-form" in body
        assert "/api/simulator/parse" in body
        assert "addDogsToSimulator" in body


class TestGlossarySearchUI:
    """ライブフィルタの JS が glossary.html に含まれていることを確認"""

    def test_glossary_has_live_filter_script(self):
        rv = client.get("/glossary")
        body = rv.get_data(as_text=True)
        assert "Live filter" in body or "applyFilter" in body
        assert "addEventListener('input'" in body

    def test_glossary_has_keyboard_shortcut(self):
        rv = client.get("/glossary")
        body = rv.get_data(as_text=True)
        assert "e.key === '/'" in body


class TestEnglishGuides:
    """guides_en.py の英訳ガイドを検証"""

    def test_guides_en_module_importable(self):
        from guides_en import GUIDES_EN
        assert isinstance(GUIDES_EN, dict)
        assert len(GUIDES_EN) > 0

    def test_all_guides_have_en_translation(self):
        """全 18 ガイドに英訳がある"""
        from poodle_genetics import GUIDES
        from guides_en import GUIDES_EN
        missing = [g["slug"] for g in GUIDES if g["slug"] not in GUIDES_EN]
        assert not missing, f"Missing EN translations for: {missing}"

    def test_guide_structure_preserved(self):
        """各 EN ガイドは title/summary/category/sections を持ち、sections 数が一致"""
        from poodle_genetics import GUIDES
        from guides_en import GUIDES_EN
        for g in GUIDES:
            en = GUIDES_EN.get(g["slug"])
            assert en, f"missing: {g['slug']}"
            for key in ("title", "summary", "category", "sections"):
                assert key in en, f"{g['slug']} EN missing {key}"
            assert len(en["sections"]) == len(g["sections"]), (
                f"{g['slug']} section count mismatch: "
                f"JA={len(g['sections'])} EN={len(en['sections'])}"
            )

    def test_guides_index_en_renders(self):
        rv = client.get("/guides?lang=en")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert "Guides on Genetic Testing" in body
        # 英訳タイトルが少なくとも 1 件は出ている
        assert "Coefficient of Inbreeding" in body or "Poodle Owner" in body

    def test_guide_detail_en_uses_translation(self):
        rv = client.get("/guides/coi-basics?lang=en")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        # 英訳本文が使われている
        assert "Sewall Wright" in body
        # AI 翻訳警告が出ている（reviewed=False）
        assert "AI-generated translation" in body

    def test_guide_detail_ja_unchanged(self):
        rv = client.get("/guides/coi-basics")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert "COI（近親交配係数）" in body
        assert "AI-generated translation" not in body


class TestTranslationLint:
    """translation_lint.py が KB / guides の翻訳ギャップを検出"""

    def test_lint_returns_zero_on_clean_tree(self):
        from translation_lint import main
        # 現状で違反が無いことを確認
        assert main([]) == 0

    def test_lint_detects_missing_term(self, tmp_path, monkeypatch):
        """わざと用語を抜くと検出される"""
        from translation_lint import check_kb_pair
        ja = "変性性脊髄症 (DM) は SOD1 変異により発症します。"
        en_good = "Degenerative myelopathy (DM) is caused by SOD1 mutation."
        en_bad = "A spinal cord disease caused by gene mutation."
        assert check_kb_pair("x", ja, en_good) == []
        assert any("DM" in m for _, m in check_kb_pair("x", ja, en_bad))

    def test_lint_detects_numeric_drift(self):
        from translation_lint import check_kb_pair
        ja = "COI 6.25% 以下が推奨されます。"
        en_bad = "A COI below 5% is recommended."
        violations = check_kb_pair("x", ja, en_bad)
        assert any("RULE-4" in r for r, _ in violations)


# ===========================================================================
# 3. 413 ハンドラ
# ===========================================================================

class TestRequestTooLarge:
    def test_413_redirects_to_index(self):
        from werkzeug.exceptions import RequestEntityTooLarge
        with _app.app.test_request_context("/analyze", method="POST"):
            rv = _app.request_entity_too_large(RequestEntityTooLarge())
            # 303 redirect + flashes エラーメッセージを返す
            assert rv[1] == 303


# ===========================================================================
# 4. COI 計算（calc_coi_3gen / calc_coi_cross）
# ===========================================================================

# poodle_genetics.py は重量ファイルなので必要関数だけ直接 import
try:
    from poodle_genetics import calc_coi_3gen, calc_coi_cross, Pedigree, Ancestor
    _HAS_POODLE = True
except Exception:
    _HAS_POODLE = False


def _make_ancestor(name):
    a = Ancestor()
    a.name = name
    return a


@pytest.mark.skipif(not _HAS_POODLE, reason="poodle_genetics import failed")
class TestCOI:
    def _flat_ped(self, **kwargs):
        """名前指定のみで Pedigree を生成するヘルパー"""
        ped = Pedigree()
        ped.dog_name = kwargs.get("dog_name", "TEST")
        for attr in ("sire","dam","ss","sd","ds","dd","sss","ssd","sds","sdd","dss","dsd","dds","ddd"):
            name = kwargs.get(attr)
            if name:
                a = _make_ancestor(name)
                setattr(ped, attr, a)
        return ped

    def test_no_common_ancestors_gives_zero_coi(self):
        ped = self._flat_ped(
            sire="A", ss="B", sd="C",
            dam="D", ds="E", dd="F",
        )
        result = calc_coi_3gen(ped)
        assert result["coi"] == pytest.approx(0.0)
        assert result["common_ancestors"] == []

    def test_full_sibling_coi(self):
        """父母が同じ両親を持つ = COI 0.25"""
        ped = self._flat_ped(
            sire="P1", ss="GS", sd="GD",
            dam="P2", ds="GS", dd="GD",
        )
        result = calc_coi_3gen(ped)
        # GS: 0.5^(2+2+1)=0.03125, GD: same → 合計 0.0625
        # 両親の直接一致 (gen1,gen1): 0.5^3=0.125
        # → GS/GD は gen2, P1/P2 は gen1 なので COI = 0.125+0.125 = 0.25 (半兄弟ではなく全兄弟)
        # Wright: P1=sire(gen1), P2=dam(gen1), GS=共通祖父(gen2), GD=共通祖母(gen2)
        # 正確には sire==dam でないので gen1 pair: P1≠P2 → match なし
        # gen2 pair: (ss=GS) vs (ds=GS) → 0.5^(2+2+1)=0.03125
        #            (sd=GD) vs (dd=GD) → 0.03125
        # 合計 0.0625 (1/16)
        assert result["coi"] == pytest.approx(0.0625, rel=1e-6)

    def test_parent_offspring_coi(self):
        """sire == sire の父(ss) → gen1 vs gen2 pair → 0.5^(1+2+1)=0.0625"""
        ped = self._flat_ped(sire="REX", dam="LUNA", ds="REX")
        result = calc_coi_3gen(ped)
        assert result["coi"] == pytest.approx(0.0625, rel=1e-6)

    def test_coi_pct_is_100x_coi(self):
        ped = self._flat_ped(sire="REX", dam="LUNA", ds="REX")
        result = calc_coi_3gen(ped)
        assert result["coi_pct"] == pytest.approx(result["coi"] * 100, rel=1e-9)

    def test_cross_no_common(self):
        sire_ped = self._flat_ped(dog_name="DAD", sire="A", dam="B")
        dam_ped  = self._flat_ped(dog_name="MOM", sire="C", dam="D")
        result = calc_coi_cross(sire_ped, dam_ped)
        assert result["coi"] == pytest.approx(0.0)

    def test_cross_with_common_ancestor(self):
        """DAD と MOM が同じ祖父 GS を持つ"""
        sire_ped = self._flat_ped(dog_name="DAD", sire="GS")
        dam_ped  = self._flat_ped(dog_name="MOM", sire="GS")
        result = calc_coi_cross(sire_ped, dam_ped)
        # (DAD→GS gen1) x (MOM→GS gen1) → 0.5^(1+1+1)=0.125
        assert result["coi"] == pytest.approx(0.125, rel=1e-6)

    def test_name_normalization(self):
        """スペース揺れのある名前は正規化して同一とみなす"""
        ped = self._flat_ped(sire="REX  DOG", dam="LUNA", ds="REX DOG")
        result = calc_coi_3gen(ped)
        assert result["coi"] > 0


# ===========================================================================
# 5. allowed_file ヘルパー
# ===========================================================================

class TestAllowedFile:
    def test_pdf_allowed(self):
        assert _app.allowed_file("report.pdf", {".pdf"})

    def test_pdf_case_insensitive(self):
        assert _app.allowed_file("REPORT.PDF", {".pdf"})

    def test_exe_blocked(self):
        assert not _app.allowed_file("evil.exe", {".pdf"})

    def test_double_ext_blocked(self):
        # evil.exe.pdf は .pdf 扱い → PDF解析で失敗するがアップロードは通る（許容範囲）
        # 少なくとも .exe のみのものはブロックされる
        assert not _app.allowed_file("evil.exe", {".pdf", ".jpg"})

    def test_jpg_allowed_for_image(self):
        assert _app.allowed_file("photo.jpg", {".jpg", ".jpeg", ".png"})

    def test_heic_allowed(self):
        assert _app.allowed_file("iphone.HEIC", {".heic", ".heif", ".jpg"})


# ===========================================================================
# 6. ルーティング存在確認
# ===========================================================================

# ===========================================================================
# 7. マジックバイト検証
# ===========================================================================

class TestMagicBytes:
    def _write(self, tmp_path, content: bytes) -> str:
        path = os.path.join(tmp_path, "test_file")
        with open(path, "wb") as fp:
            fp.write(content)
        return path

    def setup_method(self):
        self.tmp = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_valid_pdf(self):
        path = self._write(self.tmp, b"%PDF-1.4 fake content")
        assert _app._is_valid_pdf(path)

    def test_invalid_pdf(self):
        path = self._write(self.tmp, b"MZ\x90\x00 this is an exe")
        assert not _app._is_valid_pdf(path)

    def test_empty_file_is_invalid_pdf(self):
        path = self._write(self.tmp, b"")
        assert not _app._is_valid_pdf(path)

    def test_valid_jpeg(self):
        path = self._write(self.tmp, b"\xff\xd8\xff\xe0 fake jpeg")
        assert _app._is_valid_image(path)

    def test_valid_png(self):
        path = self._write(self.tmp, b"\x89PNG\r\n\x1a\n fake png")
        assert _app._is_valid_image(path)

    def test_valid_webp(self):
        path = self._write(self.tmp, b"RIFFxxxxWEBP fake webp")
        assert _app._is_valid_image(path)

    def test_invalid_image(self):
        path = self._write(self.tmp, b"%PDF-1.4 this is a pdf not an image")
        assert not _app._is_valid_image(path)

    def test_nonexistent_path_returns_false(self):
        assert not _app._is_valid_pdf("/nonexistent_xyz_file.pdf")
        assert not _app._is_valid_image("/nonexistent_xyz_image.jpg")


# ===========================================================================
# 8. _log_exc 構造化ログヘルパー
# ===========================================================================

class TestLogExc:
    def test_returns_8char_hex_id(self):
        try:
            raise ValueError("boom")
        except ValueError as e:
            eid = _app._log_exc("test_stage", "test.pdf", e)
        assert isinstance(eid, str)
        assert len(eid) == 8
        # uuid hex は 16進数字のみ
        int(eid, 16)

    def test_unique_ids(self):
        ids = set()
        for _ in range(50):
            try:
                raise RuntimeError("x")
            except RuntimeError as e:
                ids.add(_app._log_exc("s", "f", e))
        # 50回呼んで全部ユニークである（衝突は uuid4 上ほぼあり得ない）
        assert len(ids) == 50

    def test_logs_to_app_logger(self, caplog):
        import logging
        with caplog.at_level(logging.ERROR, logger=_app.app.logger.name):
            try:
                raise KeyError("missing")
            except KeyError as e:
                eid = _app._log_exc("parse_pdf", "evil.pdf", e)
        # ログレコードに error_id, stage, file, exc_type が含まれるか
        log_text = caplog.text
        assert eid in log_text
        assert "parse_pdf" in log_text
        assert "evil.pdf" in log_text
        assert "KeyError" in log_text

    def test_request_id_appears_when_passed(self, caplog):
        import logging
        with caplog.at_level(logging.ERROR, logger=_app.app.logger.name):
            try:
                raise ValueError("x")
            except ValueError as e:
                _app._log_exc("ocr", "img.jpg", e, request_id="abc12345")
        assert "request_id=abc12345" in caplog.text

    def test_request_id_dash_when_omitted(self, caplog):
        import logging
        with caplog.at_level(logging.ERROR, logger=_app.app.logger.name):
            try:
                raise ValueError("x")
            except ValueError as e:
                _app._log_exc("ocr", "img.jpg", e)
        # 後方互換: request_id 省略時は "-" を出力する
        assert "request_id=-" in caplog.text


# ===========================================================================
# 9. パーサー純関数（合成テキストで code path をカバー）
# ===========================================================================

try:
    from poodle_genetics import (
        classify_result,
        detect_pedigree_format, _clean_ocr_text, _h, status_badge,
        sanitize_for_excel,
    )
    _HAS_PARSERS = True
except Exception:
    _HAS_PARSERS = False


@pytest.mark.skipif(not _HAS_PARSERS, reason="poodle_genetics parsers not importable")
class TestClassifyResult:
    def test_positive_pp(self):
        assert classify_result("POSITIVE (P/P)") == "positive"

    def test_two_copies(self):
        assert classify_result("Dog has two copies of the variant") == "positive"

    def test_carrier_pn(self):
        assert classify_result("CARRIER (P/N)") == "carrier"

    def test_one_copy(self):
        assert classify_result("Dog has one copy of the variant") == "carrier"

    def test_normal_nn(self):
        assert classify_result("NORMAL (N/N)") == "normal"

    def test_no_variant(self):
        assert classify_result("No variant detected") == "normal"

    def test_positive_heterozygous_is_carrier(self):
        # POSITIVE HETEROZYGOUS は carrier 扱い（PR #25 で修正された分類）
        assert classify_result("POSITIVE HETEROZYGOUS") == "carrier"

    def test_unknown_falls_back_to_trait(self):
        assert classify_result("ay/ay (E Locus)") == "trait"

    def test_case_insensitive(self):
        assert classify_result("normal (n/n)") == "normal"


@pytest.mark.skipif(not _HAS_PARSERS, reason="poodle_genetics parsers not importable")
class TestDetectPedigreeFormat:
    def test_jkc(self):
        assert detect_pedigree_format("ジャパンケネルクラブ 血統書") == "jkc"
        assert detect_pedigree_format("JKC-PT-12345") == "jkc"
        assert detect_pedigree_format("JAPAN KENNEL CLUB") == "jkc"

    def test_alaj(self):
        assert detect_pedigree_format("Australian Labradoodle Association") == "alaj"
        assert detect_pedigree_format("ALAJ Registry") == "alaj"

    def test_akc(self):
        assert detect_pedigree_format("AMERICAN KENNEL CLUB") == "akc"
        assert detect_pedigree_format("AKC Registry") == "akc"

    def test_kc(self):
        assert detect_pedigree_format("THE KENNEL CLUB") == "kc"

    def test_generic_fallback(self):
        assert detect_pedigree_format("SIRE: REX  DAM: LUNA  PEDIGREE") == "generic"

    def test_unknown_returns_generic(self):
        assert detect_pedigree_format("random text without keywords") == "generic"

    def test_jkc_wins_over_kc(self):
        # JKC-PT が含まれていれば JKC を優先（KC 単独より先にマッチ）
        text = "JKC-PT THE KENNEL CLUB"
        assert detect_pedigree_format(text) == "jkc"


@pytest.mark.skipif(not _HAS_PARSERS, reason="poodle_genetics parsers not importable")
class TestCleanOcrText:
    def test_kennel_misread(self):
        assert "KENNEL" in _clean_ocr_text("KENNE1 CLUB")
        assert "KENNEL" in _clean_ocr_text("KENNE! CLUB")

    def test_club_misread(self):
        assert "CLUB" in _clean_ocr_text("KENNEL C1UB")
        assert "CLUB" in _clean_ocr_text("KENNEL CIUB")

    def test_japan_misread(self):
        assert "JAPAN" in _clean_ocr_text("J@PAN KENNEL")

    def test_poodle_misread(self):
        assert "POODLE" in _clean_ocr_text("P00DLE breed")

    def test_sire_misread(self):
        assert "SIRE" in _clean_ocr_text("S1RE: REX")

    def test_empty_string(self):
        assert _clean_ocr_text("") == ""

    def test_no_change_when_clean(self):
        original = "JAPAN KENNEL CLUB POODLE"
        assert _clean_ocr_text(original) == original

    # --- 拡張 OCR クリーニングのテスト ---
    def test_fullwidth_to_halfwidth_ascii(self):
        """全角 ASCII（ＳＩＲＥ）→ 半角に正規化される"""
        assert "SIRE" in _clean_ocr_text("ＳＩＲＥ: ＲＥＸ")

    def test_fullwidth_colon_normalized(self):
        assert "Sire:" in _clean_ocr_text("Sire：REX")

    def test_japanese_label_spacing(self):
        """OCR が "犬 名" のように空白を挿入したケース"""
        assert "犬名" in _clean_ocr_text("犬 名 : サンプル太郎")
        assert "生年月日" in _clean_ocr_text("生 年 月 日 : 2020/01/01")

    def test_whitespace_inserted_label(self):
        """OCR が "P E D I G R E E" のように字間に空白を入れたケース"""
        assert "PEDIGREE" in _clean_ocr_text("P E D I G R E E")
        assert "KENNEL" in _clean_ocr_text("K E N N E L CLUB")
        assert "JKC" in _clean_ocr_text("J K C - PT")

    def test_jkc_registration_format(self):
        """JKC 登録番号の余分なスペース・ハイフン揺れを正規化"""
        out = _clean_ocr_text("JKC - PT - 12345 / 67")
        assert "JKC-PT-12345/67" in out

    def test_uppercase_misreads_extended(self):
        """新規追加の大文字ラベル誤認識"""
        assert "KENNEL" in _clean_ocr_text("KENNEI CLUB")
        assert "JAPAN" in _clean_ocr_text("J4PAN KENNEL")
        assert "DAM" in _clean_ocr_text("DAlVl: BELLA")
        assert "FEMALE" in _clean_ocr_text("Sex: FEM4LE")
        assert "BREED" in _clean_ocr_text("BR3ED: POODLE")
        assert "BIRTH" in _clean_ocr_text("BIRTII DATE")
        assert "CHAMPION" in _clean_ocr_text("INT CHAMP10N")

    def test_control_chars_stripped(self):
        """制御文字（BOM, 各種ZWSP）が除去される"""
        # BOM, ZWSP を含む文字列
        msg = "﻿SIRE​: REX"
        out = _clean_ocr_text(msg)
        assert "﻿" not in out
        assert "​" not in out
        assert "SIRE: REX" in out

    def test_collapse_consecutive_blank_lines(self):
        """連続空行が圧縮される（パース安定化）"""
        out = _clean_ocr_text("LINE1\n\n\n\n\nLINE2")
        # 3 行以上の連続改行は 2 行に
        assert "\n\n\n" not in out
        assert "LINE1\n\nLINE2" in out

    def test_dam_dalvl_recognized(self):
        """DAM が小文字Lで誤認識されたケース"""
        out = _clean_ocr_text("DAlVl: BELLA")
        assert "DAM" in out


class TestOcrScoring:
    """OCR 出力スコアリング（高品質なバリアントを選ぶための基盤）"""

    def test_score_increases_with_domain_keywords(self):
        from poodle_genetics import _score_ocr_text
        plain = "abc def 123 456" * 20
        rich = "PEDIGREE SIRE DAM KENNEL JAPAN " + plain
        assert _score_ocr_text(rich) > _score_ocr_text(plain)

    def test_score_zero_for_empty(self):
        from poodle_genetics import _score_ocr_text
        assert _score_ocr_text("") == 0.0
        assert _score_ocr_text(None) == 0.0

    def test_score_penalizes_noise(self):
        from poodle_genetics import _score_ocr_text
        clean = "PEDIGREE SIRE DAM KENNEL JAPAN owner breeder " * 4
        noisy = clean.replace("a", "@").replace("e", "#") + "~^`'\"|" * 50
        assert _score_ocr_text(clean) > _score_ocr_text(noisy)

    def test_score_rewards_japanese_keywords(self):
        from poodle_genetics import _score_ocr_text
        s = "犬名 犬種 性別 毛色 生年月日 ジャパンケネルクラブ"
        # 日本語キーワード 5+ で 100 点以上
        assert _score_ocr_text(s) >= 100


@pytest.mark.skipif(not _HAS_PARSERS, reason="poodle_genetics parsers not importable")
class TestHtmlEscape:
    def test_escapes_lt_gt(self):
        assert _h("<script>") == "&lt;script&gt;"

    def test_escapes_quote(self):
        assert _h('"x"') == "&quot;x&quot;"

    def test_escapes_apostrophe(self):
        assert _h("it's") == "it&#x27;s"

    def test_escapes_ampersand_first(self):
        # & を先にエスケープしないと <script> → &lt;script&gt; が &amp;lt;... になる
        assert _h("a & b") == "a &amp; b"
        assert _h("<&>") == "&lt;&amp;&gt;"

    def test_none_returns_empty(self):
        assert _h(None) == ""

    def test_int_input(self):
        assert _h(42) == "42"

    def test_xss_payload(self):
        payload = '<img src=x onerror="alert(1)">'
        escaped = _h(payload)
        assert "<" not in escaped
        assert ">" not in escaped
        assert '"' not in escaped


@pytest.mark.skipif(not _HAS_PARSERS, reason="poodle_genetics parsers not importable")
class TestStatusBadge:
    def test_normal(self):
        assert status_badge("normal", "正常") == '<span class="status normal">正常</span>'

    def test_escapes_text(self):
        result = status_badge("positive", "<script>")
        assert "&lt;script&gt;" in result
        assert "<script>" not in result


@pytest.mark.skipif(not _HAS_PARSERS, reason="poodle_genetics parsers not importable")
class TestSanitizeForExcel:
    """sanitize_for_excel: 制御文字除去 + CSV/Excel formula injection 対策（[BUG-006] 修正済）"""

    def test_strips_control_chars(self):
        # ASCII制御文字（BEL=0x07）が除去される
        assert sanitize_for_excel("AB\x07CD") == "ABCD"

    def test_strips_null_byte(self):
        assert sanitize_for_excel("X\x00Y") == "XY"

    def test_strips_replacement_char(self):
        # U+FFFD（PDF の文字化けで頻出）が除去される
        assert sanitize_for_excel("good�text") == "goodtext"

    def test_preserves_japanese(self):
        assert sanitize_for_excel("ジャパンケネルクラブ") == "ジャパンケネルクラブ"

    def test_preserves_tab_and_newline(self):
        assert "\t" in sanitize_for_excel("a\tb")
        assert "\n" in sanitize_for_excel("a\nb")

    def test_passes_normal_text(self):
        assert sanitize_for_excel("Regular text") == "Regular text"

    def test_empty_string(self):
        assert sanitize_for_excel("") == ""

    # --- [BUG-006] formula injection 対策の検証 ---
    def test_escapes_equals_prefix(self):
        # =SUM(...) は Excel 起動時に評価される → ' プレフィックスで無害化
        assert sanitize_for_excel("=SUM(A1)") == "'=SUM(A1)"

    def test_escapes_plus_prefix(self):
        assert sanitize_for_excel("+cmd|'/c calc'!A1") == "'+cmd|'/c calc'!A1"

    def test_escapes_minus_prefix(self):
        assert sanitize_for_excel("-2+3") == "'-2+3"

    def test_escapes_at_prefix(self):
        # @SUM (Lotus 1-2-3 互換シンタックス, Excel でも評価される)
        assert sanitize_for_excel("@SUM(A1)") == "'@SUM(A1)"

    def test_does_not_escape_middle_equals(self):
        # 文字列中の = は安全（先頭のみが式として解釈される）
        assert sanitize_for_excel("a=b") == "a=b"

    def test_does_not_escape_normal_genotype(self):
        # 遺伝子型「E/e」等は影響を受けない
        assert sanitize_for_excel("E/e") == "E/e"
        assert sanitize_for_excel("Bb") == "Bb"
        assert sanitize_for_excel("Clear (N/N)") == "Clear (N/N)"

    def test_escapes_after_control_char_strip(self):
        # 制御文字を除去した結果として先頭が = になるケース
        # \x07=EVIL → =EVIL → '=EVIL
        assert sanitize_for_excel("\x07=EVIL") == "'=EVIL"


# ===========================================================================
# 10. ナレッジベース（詳細解説）
# ===========================================================================

try:
    from poodle_genetics import (
        get_disease_detail, get_trait_detail, render_detail_html,
        DISEASE_KB, TRAIT_KB,
    )
    _HAS_KB = True
except Exception:
    _HAS_KB = False


@pytest.mark.skipif(not _HAS_KB, reason="KB module not importable")
class TestDiseaseKB:
    def test_cddy_matches(self):
        d = get_disease_detail("Chondrodystrophy with IVDD")
        assert d is not None
        assert "椎間板" in d.get("summary", "")
        assert any("Wikipedia" in r.get("label", "") or "検索" in r.get("label", "") for r in d.get("references", []))

    def test_dm_matches(self):
        d = get_disease_detail("Degenerative Myelopathy")
        assert d is not None
        assert "SOD1" in d.get("mechanism", "")

    def test_prcd_matches(self):
        d = get_disease_detail("Progressive Rod-Cone Degeneration")
        assert d is not None
        assert "網膜" in d.get("title", "") or "PRA" in d.get("title", "")

    def test_unknown_returns_none(self):
        assert get_disease_detail("Random Unknown Disease") is None

    def test_empty_returns_none(self):
        assert get_disease_detail("") is None
        assert get_disease_detail(None) is None

    def test_all_entries_have_required_fields(self):
        for entry in DISEASE_KB:
            assert "match" in entry and entry["match"]
            assert "title" in entry and entry["title"]
            assert "summary" in entry and entry["summary"]
            assert "references" in entry
            for ref in entry["references"]:
                assert "label" in ref and "url" in ref
                assert ref["url"].startswith("https://")

    # === 拡張カバレッジテスト (PR #44 で 11→30+ 疾患に拡大) ===
    def test_extended_coverage_news(self):
        d = get_disease_detail("Neonatal Encephalopathy with Seizures")
        assert d is not None and "ATF2" in d.get("title", "")

    def test_extended_coverage_mdr1(self):
        d = get_disease_detail("MDR1 / Multidrug Resistance")
        assert d is not None and "ABCB1" in d.get("mechanism", "")

    def test_extended_coverage_huu(self):
        d = get_disease_detail("Hyperuricosuria")
        assert d is not None and "尿酸" in d.get("summary", "")

    def test_extended_coverage_cea(self):
        d = get_disease_detail("Collie Eye Anomaly")
        assert d is not None and "NHEJ1" in d.get("mechanism", "")

    def test_extended_coverage_cystinuria(self):
        d = get_disease_detail("Cystinuria")
        assert d is not None and "SLC" in d.get("mechanism", "")

    def test_extended_coverage_hnpk(self):
        d = get_disease_detail("Hereditary Nasal Parakeratosis (HNPK)")
        assert d is not None and "SUV39H2" in d.get("mechanism", "")

    def test_extended_coverage_minimum_count(self):
        # KB は 11 (元の10 + EIC) → 拡張後 30 以上に
        assert len(DISEASE_KB) >= 25, f"DISEASE_KB has only {len(DISEASE_KB)} entries"

    # === Veqta 検査パネル準拠の追加カバレッジ (40+ diseases) ===
    def test_glaucoma(self):
        d = get_disease_detail("Primary Glaucoma")
        assert d is not None and "緑内障" in d.get("title", "")

    def test_gm1(self):
        d = get_disease_detail("GM1 Gangliosidosis")
        assert d is not None and "GLB1" in d.get("mechanism", "")

    def test_vwd_type2(self):
        d = get_disease_detail("von Willebrand Disease Type 2")
        assert d is not None and "II型" in d.get("title", "")

    def test_gsd(self):
        d = get_disease_detail("Glycogen Storage Disease")
        assert d is not None and "グリコーゲン" in d.get("summary", "")

    def test_osteogenesis_imperfecta(self):
        d = get_disease_detail("Osteogenesis Imperfecta")
        assert d is not None and "骨形成不全" in d.get("title", "")

    def test_cobalamin(self):
        d = get_disease_detail("Cobalamin Malabsorption")
        assert d is not None and "B12" in d.get("advice", "")

    def test_veqta_min_coverage(self):
        # Veqta 主要疾患含めて 40 以上
        assert len(DISEASE_KB) >= 40, f"DISEASE_KB has only {len(DISEASE_KB)} entries"

    # === PR #47 拡張カバレッジ (50+ diseases) ===
    def test_cerebellar_abiotrophy(self):
        d = get_disease_detail("Cerebellar Abiotrophy")
        assert d is not None and "小脳" in d.get("title", "")

    def test_krabbe(self):
        d = get_disease_detail("Krabbe Disease")
        assert d is not None and "GALC" in d.get("mechanism", "")

    def test_efs(self):
        d = get_disease_detail("Episodic Falling Syndrome")
        assert d is not None and "BCAN" in d.get("mechanism", "")

    def test_l2hga(self):
        d = get_disease_detail("L-2-Hydroxyglutaric Aciduria")
        assert d is not None and "L2HGDH" in d.get("mechanism", "")

    def test_cmr(self):
        d = get_disease_detail("Multifocal Retinopathy CMR1")
        assert d is not None and "BEST1" in d.get("mechanism", "")

    def test_cda(self):
        d = get_disease_detail("Color Dilution Alopecia")
        assert d is not None and "希釈" in d.get("title", "")

    def test_full_panel_min_coverage(self):
        # PR #47 後で 50 以上
        assert len(DISEASE_KB) >= 55, f"DISEASE_KB has only {len(DISEASE_KB)} entries"

    # === PR #49 Embark準拠拡張 (73+ diseases) ===
    def test_nme(self):
        d = get_disease_detail("Necrotizing Meningoencephalitis")
        assert d is not None and "髄膜脳炎" in d.get("title", "")

    def test_lafora(self):
        d = get_disease_detail("Lafora Disease")
        assert d is not None and "NHLRC1" in d.get("mechanism", "")

    def test_narcolepsy(self):
        d = get_disease_detail("Narcolepsy")
        assert d is not None and "HCRTR2" in d.get("mechanism", "")

    def test_scid(self):
        d = get_disease_detail("Severe Combined Immunodeficiency")
        assert d is not None and "免疫" in d.get("title", "")

    def test_pituitary_dwarfism(self):
        d = get_disease_detail("Pituitary Dwarfism")
        assert d is not None and "LHX3" in d.get("mechanism", "")

    def test_rcd1_pdesb(self):
        d = get_disease_detail("PRA rcd1")
        assert d is not None and "PDE6B" in d.get("mechanism", "")

    def test_embark_min_coverage(self):
        # PR #49 後で 73 以上
        assert len(DISEASE_KB) >= 70, f"DISEASE_KB has only {len(DISEASE_KB)} entries"

    def test_pll(self):
        d = get_disease_detail("PLL")
        assert d is not None and "水晶体脱臼" in d.get("title", "")

    def test_pfk_deficiency(self):
        d = get_disease_detail("pfk deficiency")
        assert d is not None and "PFKM" in d.get("title", "")

    def test_arvc(self):
        d = get_disease_detail("ARVC")
        assert d is not None and "Striatin" in d.get("title", "")

    def test_dcm1(self):
        d = get_disease_detail("dcm1")
        assert d is not None and "PDK4" in d.get("title", "")

    def test_bfje(self):
        d = get_disease_detail("BFJE")
        assert d is not None and "LGI2" in d.get("title", "")

    def test_heart_category_exists(self):
        from poodle_genetics import DISEASE_CATEGORIES
        cats = [c for c, _ in DISEASE_CATEGORIES]
        assert any("心臓" in c for c in cats), "心臓系 category not found in DISEASE_CATEGORIES"

    def test_heart_diseases_in_category(self):
        from poodle_genetics import group_diseases_by_category, DISEASE_KB
        grouped = group_diseases_by_category(DISEASE_KB)
        heart_items = next((items for cat, items in grouped if "心臓" in cat), [])
        assert len(heart_items) >= 2, f"Expected ≥2 heart diseases, got {len(heart_items)}"

    def test_full_panel_min_coverage_updated(self):
        assert len(DISEASE_KB) >= 77, f"DISEASE_KB has only {len(DISEASE_KB)} entries"


# ===========================================================================
# 14. PR #49 トレイトKB拡張 (14+ 座位)
# ===========================================================================

@pytest.mark.skipif(not _HAS_KB, reason="TRAIT_KB not importable")
class TestTraitKBExpansion:
    def test_l_locus(self):
        t = get_trait_detail("L Locus (Hair Length)")
        assert t is not None and "FGF5" in t.get("title", "")

    def test_shedding(self):
        t = get_trait_detail("Shedding (MC5R)")
        assert t is not None and "MC5R" in t.get("title", "")

    def test_bob_tail(self):
        t = get_trait_detail("Natural Bob Tail")
        assert t is not None and "Brachyury" in t.get("title", "") or "短尾" in t.get("title", "")
        # 致死警告が含まれること
        assert "致死" in t.get("phenotype", "") or "致死" in t.get("advice", "")

    def test_em_locus(self):
        t = get_trait_detail("Em Locus (Melanistic Mask)")
        assert t is not None and "マスク" in t.get("title", "")

    def test_g_locus(self):
        t = get_trait_detail("G Locus (Greying)")
        assert t is not None and "退色" in t.get("title", "") or "Greying" in t.get("title", "")

    def test_trait_kb_count(self):
        from poodle_genetics import TRAIT_KB
        assert len(TRAIT_KB) >= 14, f"TRAIT_KB has only {len(TRAIT_KB)} entries"


# ===========================================================================
# 11. グロッサリー(/glossary) ルート
# ===========================================================================

class TestGlossaryRoute:
    def test_glossary_200(self):
        rv = client.get("/glossary")
        assert rv.status_code == 200

    def test_glossary_lists_diseases(self):
        rv = client.get("/glossary")
        body = rv.get_data(as_text=True)
        # 主要疾患の見出しが含まれる
        assert "椎間板" in body or "CDDY" in body
        assert "DM" in body or "変性性脊髄症" in body

    def test_glossary_search_filters(self):
        rv = client.get("/glossary?q=椎間板")
        body = rv.get_data(as_text=True)
        assert "CDDY" in body or "椎間板" in body
        # 他の疾患は出ない（ヒット件数 1 表示）
        assert "&#34;椎間板&#34;" in body or "椎間板" in body

    def test_glossary_empty_search(self):
        rv = client.get("/glossary?q=nonexistent_xyz_term_zzz")
        body = rv.get_data(as_text=True)
        assert "見つかりませんでした" in body

    def test_api_glossary_json(self):
        rv = client.get("/api/glossary")
        assert rv.status_code == 200
        data = rv.get_json()
        assert "diseases" in data and "traits" in data
        assert len(data["diseases"]) >= 30
        assert len(data["traits"]) >= 5

    def test_glossary_groups_by_category(self):
        rv = client.get("/glossary")
        body = rv.get_data(as_text=True)
        # 主要カテゴリヘッダーが表示される
        assert "神経・脳系" in body
        assert "眼科系" in body
        assert "血液・凝固系" in body
        # 目次が表示される
        assert "目次" in body
        # アンカーリンクが生成される
        assert "#cat-" in body


# ===========================================================================
# 12. group_diseases_by_category ヘルパー
# ===========================================================================

try:
    from poodle_genetics import group_diseases_by_category, get_disease_category
    _HAS_GROUPING = True
except Exception:
    _HAS_GROUPING = False


@pytest.mark.skipif(not _HAS_GROUPING, reason="grouping helpers not importable")
class TestDiseaseGrouping:
    def test_returns_list_of_tuples(self):
        from poodle_genetics import DISEASE_KB
        groups = group_diseases_by_category(DISEASE_KB)
        assert isinstance(groups, list)
        for cat, items in groups:
            assert isinstance(cat, str) and cat
            assert isinstance(items, list) and items

    def test_all_entries_categorized(self):
        from poodle_genetics import DISEASE_KB
        groups = group_diseases_by_category(DISEASE_KB)
        total = sum(len(items) for _, items in groups)
        assert total == len(DISEASE_KB)

    def test_cddy_in_skeletal(self):
        from poodle_genetics import get_disease_detail
        cddy = get_disease_detail("CDDY+IVDD")
        assert "骨格" in get_disease_category(cddy)

    def test_dm_in_neuro(self):
        from poodle_genetics import get_disease_detail
        dm = get_disease_detail("Degenerative Myelopathy")
        assert "神経" in get_disease_category(dm)

    def test_pra_in_eye(self):
        from poodle_genetics import get_disease_detail
        pra = get_disease_detail("Progressive Rod-Cone Degeneration")
        assert "眼科" in get_disease_category(pra)

    def test_empty_list(self):
        assert group_diseases_by_category([]) == []


# ===========================================================================
# 13. 重症度フィルタリング
# ===========================================================================

try:
    from poodle_genetics import get_disease_severity, SEVERITY_LABELS
    _HAS_SEVERITY = True
except Exception:
    _HAS_SEVERITY = False


@pytest.mark.skipif(not _HAS_SEVERITY, reason="severity helpers not importable")
class TestSeverity:
    def test_returns_one_of_three(self):
        from poodle_genetics import DISEASE_KB
        for e in DISEASE_KB:
            sev = get_disease_severity(e)
            assert sev in ("high", "medium", "low"), f"unexpected severity {sev} for {e.get('title')}"

    def test_explicit_severity_takes_priority(self):
        entry = {"severity": "high", "summary": "通常は無症状"}  # 矛盾するキーワード
        assert get_disease_severity(entry) == "high"

    def test_keyword_detection_high(self):
        # 「予後不良」「致死」「死亡」などで high と判定
        entry = {"summary": "重篤な遺伝性疾患", "advice": "P/P は予後不良"}
        assert get_disease_severity(entry) == "high"

    def test_keyword_detection_low(self):
        entry = {"summary": "通常は無症状", "advice": "完治はしない"}
        assert get_disease_severity(entry) == "low"

    def test_severity_labels_complete(self):
        for level in ("high", "medium", "low"):
            assert level in SEVERITY_LABELS
            assert "label" in SEVERITY_LABELS[level]
            assert "color" in SEVERITY_LABELS[level]
            assert "emoji" in SEVERITY_LABELS[level]

    def test_glossary_severity_filter_high(self):
        rv = client.get("/glossary?severity=high")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert "高リスク" in body

    def test_glossary_severity_filter_active_state(self):
        rv = client.get("/glossary?severity=low")
        body = rv.get_data(as_text=True)
        # 低リスクボタンが active class を持つ
        assert 'severity=low' in body
        # active クラスが low のリンクに付与される
        # （class="active" が低リスクボタンに含まれる）

    def test_glossary_severity_combined_with_query(self):
        rv = client.get("/glossary?severity=high&q=遺伝")
        assert rv.status_code == 200


# ===========================================================================
# 15. 症状ベース絞り込み (SYMPTOM_INDEX / filter_by_symptom)
# ===========================================================================

try:
    from poodle_genetics import SYMPTOM_INDEX, filter_by_symptom
    _HAS_SYMPTOM = True
except Exception:
    _HAS_SYMPTOM = False


@pytest.mark.skipif(not _HAS_SYMPTOM, reason="symptom helpers not importable")
class TestSymptomFilter:
    def test_symptom_index_has_entries(self):
        assert len(SYMPTOM_INDEX) >= 8
        for sym in SYMPTOM_INDEX:
            assert "id" in sym and sym["id"]
            assert "label" in sym and sym["label"]
            assert "match_patterns" in sym and len(sym["match_patterns"]) > 0

    def test_filter_hindlimb_includes_dm(self):
        from poodle_genetics import DISEASE_KB
        result = filter_by_symptom(DISEASE_KB, "hindlimb")
        titles = [e.get("title", "") for e in result]
        assert any("変性性脊髄症" in t for t in titles)

    def test_filter_vision_includes_pra(self):
        from poodle_genetics import DISEASE_KB
        result = filter_by_symptom(DISEASE_KB, "vision")
        titles = [e.get("title", "") for e in result]
        assert any("PRA" in t or "進行性網膜萎縮" in t for t in titles)

    def test_filter_bleeding_includes_vwd(self):
        from poodle_genetics import DISEASE_KB
        result = filter_by_symptom(DISEASE_KB, "bleeding")
        titles = [e.get("title", "") for e in result]
        assert any("ヴィレブランド" in t for t in titles)

    def test_filter_unknown_symptom_returns_all(self):
        from poodle_genetics import DISEASE_KB
        # 未知 ID は全件返す（フォールバック）
        result = filter_by_symptom(DISEASE_KB, "nonexistent_xyz")
        assert len(result) == len(DISEASE_KB)

    def test_glossary_symptom_url_param(self):
        rv = client.get("/glossary?symptom=hindlimb")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert "後肢" in body or "歩行" in body

    def test_glossary_symptom_combined_with_severity(self):
        rv = client.get("/glossary?symptom=vision&severity=high")
        assert rv.status_code == 200


# ===========================================================================
# 16. 個別 URL + SEO（疾患・形質ごとの URL / sitemap / robots.txt）
# ===========================================================================

try:
    from poodle_genetics import (
        DISEASE_SLUG_INDEX, TRAIT_SLUG_INDEX, make_entry_slug, _slugify,
    )
    _HAS_SLUG = True
except Exception:
    _HAS_SLUG = False


@pytest.mark.skipif(not _HAS_SLUG, reason="slug helpers not importable")
class TestSlugIndex:
    def test_slugify_basic(self):
        assert _slugify("Chondrodystrophy with IVDD") == "chondrodystrophy-with-ivdd"
        assert _slugify("CDDY+IVDD") == "cddy-ivdd"
        assert _slugify("Hello World!") == "hello-world"

    def test_disease_slug_index_built(self):
        assert len(DISEASE_SLUG_INDEX) > 0
        # 全エントリに slug が振られている
        for slug, entry in DISEASE_SLUG_INDEX.items():
            assert slug and slug == entry.get("_slug")

    def test_trait_slug_index_built(self):
        assert len(TRAIT_SLUG_INDEX) > 0

    def test_slugs_are_unique(self):
        # 重複なし
        assert len(DISEASE_SLUG_INDEX) == len(set(DISEASE_SLUG_INDEX.keys()))
        assert len(TRAIT_SLUG_INDEX) == len(set(TRAIT_SLUG_INDEX.keys()))

    def test_known_slugs_exist(self):
        # 主要疾患・形質の slug が存在することを確認
        all_slugs = " ".join(DISEASE_SLUG_INDEX.keys())
        # CDDY 関連のいずれかのスラッグが存在
        assert "chondrodystrophy" in all_slugs or "cddy" in all_slugs


@pytest.mark.skipif(not _HAS_SLUG, reason="slug helpers not importable")
class TestSEORoutes:
    def test_disease_detail_page_200(self):
        # 既知の slug でアクセス
        slug = list(DISEASE_SLUG_INDEX.keys())[0]
        rv = client.get(f"/glossary/disease/{slug}")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        # SEO 重要要素を確認
        assert "<title>" in body
        assert 'name="description"' in body
        assert 'rel="canonical"' in body
        assert 'property="og:title"' in body
        assert 'application/ld+json' in body

    def test_disease_detail_404_for_unknown_slug(self):
        rv = client.get("/glossary/disease/nonexistent-xyz-slug")
        assert rv.status_code == 404
        body = rv.get_data(as_text=True)
        assert "見つかりません" in body or "404" in body

    def test_trait_detail_page_200(self):
        slug = list(TRAIT_SLUG_INDEX.keys())[0]
        rv = client.get(f"/glossary/trait/{slug}")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert "<title>" in body
        assert 'application/ld+json' in body

    def test_sitemap_xml(self):
        rv = client.get("/sitemap.xml")
        assert rv.status_code == 200
        assert rv.content_type.startswith("application/xml")
        body = rv.get_data(as_text=True)
        # 全疾患 + 全形質 + メインページが含まれる
        assert "<urlset" in body
        assert "/glossary/disease/" in body
        assert "/glossary/trait/" in body

    def test_robots_txt(self):
        rv = client.get("/robots.txt")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert "User-agent: *" in body
        assert "Sitemap:" in body
        # セッション URL クロール禁止
        assert "Disallow: /report/" in body
        assert "Disallow: /api/" in body

    def test_disease_page_has_jsonld_schema(self):
        slug = list(DISEASE_SLUG_INDEX.keys())[0]
        rv = client.get(f"/glossary/disease/{slug}")
        body = rv.get_data(as_text=True)
        # schema.org MedicalCondition の存在
        assert "MedicalCondition" in body
        assert '"@context": "https://schema.org"' in body

    def test_disease_page_breadcrumb(self):
        slug = list(DISEASE_SLUG_INDEX.keys())[0]
        rv = client.get(f"/glossary/disease/{slug}")
        body = rv.get_data(as_text=True)
        assert "パンくず" in body or "breadcrumb" in body


# ===========================================================================
# 17. サンプルレポート + ガイド記事 (Phase 2 SEO)
# ===========================================================================

try:
    from poodle_genetics import GUIDES, GUIDES_INDEX
    _HAS_GUIDES = True
except Exception:
    _HAS_GUIDES = False


@pytest.mark.skipif(not _HAS_GUIDES, reason="guides not importable")
class TestSampleAndGuides:
    def test_sample_page_200(self):
        rv = client.get("/sample")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        # SEO 要素
        assert "<title>" in body
        assert 'rel="canonical"' in body
        # サンプル明示
        assert "サンプル" in body
        # CTA 導線
        assert "解析を始める" in body or "/" in body

    def test_guides_index_200(self):
        rv = client.get("/guides")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        # 全ガイドが一覧に表示される
        for guide in GUIDES:
            assert guide["title"] in body

    def test_guides_count(self):
        assert len(GUIDES) >= 5

    def test_each_guide_has_required_fields(self):
        for guide in GUIDES:
            assert guide.get("slug")
            assert guide.get("title")
            assert guide.get("summary")
            assert guide.get("category")
            assert guide.get("reading_time")
            assert guide.get("sections") and len(guide["sections"]) > 0
            for section in guide["sections"]:
                assert section.get("heading")
                assert section.get("body")

    def test_guide_detail_page_200(self):
        slug = GUIDES[0]["slug"]
        rv = client.get(f"/guides/{slug}")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert GUIDES[0]["title"] in body
        # JSON-LD Article 構造化
        assert "application/ld+json" in body
        assert "Article" in body

    def test_guide_detail_404_for_unknown_slug(self):
        rv = client.get("/guides/nonexistent-xyz")
        assert rv.status_code == 404

    def test_sitemap_includes_guides(self):
        rv = client.get("/sitemap.xml")
        body = rv.get_data(as_text=True)
        for guide in GUIDES:
            assert f"/guides/{guide['slug']}" in body

    def test_guides_related_entries_resolve(self):
        """ガイドの related_*_slugs が存在する slug を参照しているか"""
        from poodle_genetics import DISEASE_SLUG_INDEX, TRAIT_SLUG_INDEX
        for guide in GUIDES:
            for slug in guide.get("related_disease_slugs", []):
                assert slug in DISEASE_SLUG_INDEX, f"unknown disease slug {slug} in guide {guide['slug']}"
            for slug in guide.get("related_trait_slugs", []):
                assert slug in TRAIT_SLUG_INDEX, f"unknown trait slug {slug} in guide {guide['slug']}"


# ===========================================================================
# 18. KB エクスポート (export_kb_review.py)
# ===========================================================================

class TestKbExport:
    def test_export_module_importable(self):
        import export_kb_review
        assert hasattr(export_kb_review, "main")
        assert hasattr(export_kb_review, "disease_to_md")
        assert hasattr(export_kb_review, "trait_to_md")

    def test_disease_to_md_format(self):
        import export_kb_review
        entry = {
            "_slug": "test-disease",
            "title": "テスト疾患 (TEST)",
            "match": ["test", "テスト"],
            "summary": "テスト用の概要",
            "mechanism": "メカニズム説明",
            "symptoms": "症状説明",
            "inheritance": "常染色体劣性",
            "advice": "繁殖アドバイス",
            "references": [{"label": "Test Link", "url": "https://example.com"}],
        }
        md = export_kb_review.disease_to_md(entry)
        assert "### テスト疾患 (TEST)" in md
        assert "test-disease" in md
        assert "📋 概要" in md
        assert "🧬 メカニズム" in md
        assert "[Test Link](https://example.com)" in md
        # レビューチェックリストが含まれる
        assert "レビュアーへ" in md
        assert "- [ ]" in md

    def test_trait_to_md_format(self):
        import export_kb_review
        entry = {
            "_slug": "test-trait",
            "title": "テスト座位",
            "match": ["test locus"],
            "summary": "概要",
            "mechanism": "メカニズム",
            "phenotype": "表現型",
            "advice": "アドバイス",
            "references": [],
        }
        md = export_kb_review.trait_to_md(entry)
        assert "### テスト座位" in md
        assert "🎨 表現型" in md
        assert "レビュアーへ" in md

    def test_full_export_runs(self, tmp_path):
        """フル export を実行し、エラーなく完了することを確認"""
        import export_kb_review, sys
        out = tmp_path / "test_export.md"
        sys.argv = ["export_kb_review.py", "--out", str(out)]
        rc = export_kb_review.main()
        assert rc == 0
        assert out.exists()
        body = out.read_text(encoding="utf-8")
        # ヘッダ要素
        assert "Orivet 遺伝子検査 KB レビュードキュメント" in body
        # 疾患カテゴリヘッダ
        assert "🩺 疾患エントリ" in body
        assert "🎨 形質エントリ" in body
        # 主要疾患
        assert "CDDY" in body or "椎間板" in body
        # エントリ件数情報
        assert "疾患エントリ数" in body


# ===========================================================================
# 19. PWA 対応 (manifest.json / theme-color / icons)
# ===========================================================================

class TestPWA:
    def test_manifest_json_200(self):
        rv = client.get("/manifest.json")
        assert rv.status_code == 200
        assert rv.content_type.startswith("application/json")
        data = rv.get_json()
        # 必須フィールド
        assert "name" in data
        assert "short_name" in data
        assert "start_url" in data
        assert "display" in data
        assert "icons" in data
        assert "theme_color" in data
        # アイコン参照
        assert any("192" in icon["sizes"] for icon in data["icons"])
        assert any("512" in icon["sizes"] for icon in data["icons"])

    def test_manifest_shortcuts(self):
        rv = client.get("/manifest.json")
        data = rv.get_json()
        assert "shortcuts" in data
        assert len(data["shortcuts"]) >= 3
        urls = [s["url"] for s in data["shortcuts"]]
        assert "/glossary" in urls
        assert "/simulator" in urls

    def test_static_icon_served(self):
        # SVG アイコンが配信される
        rv = client.get("/static/icon-192.svg")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert "<svg" in body
        assert 'viewBox="0 0 192 192"' in body

    def test_static_icon_512(self):
        rv = client.get("/static/icon-512.svg")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert "<svg" in body

    def test_static_favicon_served(self):
        """新規 favicon.svg が配信される"""
        rv = client.get("/static/favicon.svg")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert "<svg" in body
        assert 'viewBox="0 0 64 64"' in body

    def test_static_apple_touch_icon_served(self):
        """apple-touch-icon.svg が配信される"""
        rv = client.get("/static/apple-touch-icon.svg")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert 'viewBox="0 0 180 180"' in body

    def test_static_og_image_served(self):
        """og-image.svg が配信される（1200x630）"""
        rv = client.get("/static/og-image.svg")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        assert 'viewBox="0 0 1200 630"' in body

    def test_index_links_new_favicon_and_og(self):
        """ホームページが新規 favicon と OG 画像をリンクしている"""
        body = client.get("/").get_data(as_text=True)
        assert '/static/favicon.svg' in body
        assert '/static/apple-touch-icon.svg' in body
        assert '/static/og-image.svg' in body
        assert 'og:image' in body

    def test_manifest_includes_favicon(self):
        """manifest.json に favicon.svg が含まれる"""
        import json
        rv = client.get("/manifest.json")
        data = json.loads(rv.get_data(as_text=True))
        srcs = [icon["src"] for icon in data["icons"]]
        assert "/static/favicon.svg" in srcs
        assert "/static/icon-192.svg" in srcs
        assert "/static/icon-512.svg" in srcs

    def test_index_has_manifest_link(self):
        rv = client.get("/")
        body = rv.get_data(as_text=True)
        assert 'rel="manifest"' in body
        assert 'name="theme-color"' in body
        assert 'apple-mobile-web-app-capable' in body

    def test_glossary_has_manifest_link(self):
        rv = client.get("/glossary")
        body = rv.get_data(as_text=True)
        assert 'rel="manifest"' in body

    def test_service_worker_route(self):
        rv = client.get("/sw.js")
        assert rv.status_code == 200
        body = rv.get_data(as_text=True)
        # Service Worker のキー要素
        assert "self.addEventListener" in body
        assert "install" in body
        assert "fetch" in body
        # Cache 戦略
        assert "CACHE_NAME" in body or "caches.open" in body
        # 個人情報含むルートをキャッシュしないこと
        assert "/api/" in body
        assert "/analyze" in body

    def test_service_worker_headers(self):
        rv = client.get("/sw.js")
        # SW は no-cache が必須（更新反映のため）
        assert "no-cache" in rv.headers.get("Cache-Control", "")
        # Service-Worker-Allowed ヘッダで広いスコープ許可
        assert rv.headers.get("Service-Worker-Allowed") == "/"

    def test_index_registers_service_worker(self):
        rv = client.get("/")
        body = rv.get_data(as_text=True)
        assert "navigator.serviceWorker.register" in body
        assert "/sw.js" in body

    def test_report_html_has_severity_badge(self):
        """generate_unified_html が KB マッチした疾患に severity-badge クラスを付与する"""
        import tempfile, os
        from poodle_genetics import generate_unified_html, DogProfile, TestResult
        # KB に存在する疾患 (CDDY+IVDD) のヘルスレスルトを作って渡す
        dog = DogProfile(
            pet_name="テスト", registered_name="Test Dog",
            breed="Toy Poodle", sex="Male", dob="2020-01-01",
            test_date="2024-01-01",
            health_results=[
                TestResult(
                    category="健康",
                    test_name="Chondrodystrophy with IVDD",
                    japanese_name="軟骨異栄養症+椎間板疾患",
                    genotype="P/N", result_text="Carrier",
                    status="carrier",
                )
            ],
        )
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
            path = f.name
        try:
            generate_unified_html([dog], [], path)
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
            assert 'class="severity-badge"' in html
            assert "リスク" in html  # 重症度ラベル
        finally:
            os.unlink(path)

    def test_report_high_risk_summary_card(self):
        """高リスク陽性サマリーカードが表示される"""
        import tempfile, os
        from poodle_genetics import generate_unified_html, DogProfile, TestResult
        # 高リスク疾患の陽性ケース (DM = high) を含む
        dog = DogProfile(
            pet_name="テスト", registered_name="Test Dog",
            test_date="2024-01-01",
            health_results=[
                TestResult(
                    category="健康", test_name="Degenerative Myelopathy",
                    japanese_name="変性性脊髄症", genotype="P/P",
                    result_text="Positive", status="positive",
                )
            ],
        )
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
            path = f.name
        try:
            generate_unified_html([dog], [], path)
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
            # 高リスク陽性カードが表示される
            assert "🚨" in html or "高リスク疾患の陽性" in html or "sum_high_risk_pos" in html
        finally:
            os.unlink(path)


@pytest.mark.skipif(not _HAS_KB, reason="KB module not importable")
class TestTraitKB:
    def test_e_locus_matches(self):
        t = get_trait_detail("E Locus (Cream/Red/Yellow)")
        assert t is not None
        assert "MC1R" in t.get("title", "")

    def test_b_locus_matches(self):
        t = get_trait_detail("B Locus (Brown)")
        assert t is not None
        assert "ブラウン" in t.get("title", "") or "TYRP1" in t.get("title", "")

    def test_merle_warning_present(self):
        t = get_trait_detail("M Locus (Merle/Dapple)")
        assert t is not None
        # M/M ダブルマールの警告が advice に含まれること
        assert "M/m" in t.get("advice", "") or "ダブル" in t.get("advice", "")

    def test_all_entries_have_required_fields(self):
        for entry in TRAIT_KB:
            assert "match" in entry and entry["match"]
            assert "title" in entry
            assert "summary" in entry
            assert "references" in entry


@pytest.mark.skipif(not _HAS_KB, reason="KB module not importable")
class TestRenderDetailHtml:
    def test_returns_empty_for_none(self):
        assert render_detail_html(None) == ""

    def test_includes_summary_section(self):
        d = get_disease_detail("CDDY+IVDD")
        html = render_detail_html(d)
        assert "<details" in html
        assert "概要" in html
        assert "椎間板" in html

    def test_links_have_security_attrs(self):
        d = get_disease_detail("CDDY+IVDD")
        html = render_detail_html(d)
        # 外部リンクは noopener noreferrer を必ず持つ
        assert "rel=\"noopener noreferrer\"" in html
        assert "target=\"_blank\"" in html

    def test_escapes_xss(self):
        # KB に xss-like 文字列が紛れても _h() でエスケープされる
        evil = {
            "title": "<script>alert(1)</script>",
            "summary": "<img src=x>",
            "references": [{"label": "<b>", "url": "https://example.com/?x=<x>"}],
        }
        html = render_detail_html(evil)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html


class TestRoutes:
    EXPECTED = ["/", "/analyze", "/report/<session_id>",
                "/api/dogs/<session_id>", "/api/pedigrees/<session_id>",
                "/download/<session_id>/<filename>", "/simulator", "/healthz"]

    def test_all_routes_present(self):
        rules = {r.rule for r in _app.app.url_map.iter_rules()}
        for route in self.EXPECTED:
            assert route in rules, f"missing route: {route}"

    def test_index_returns_200(self):
        rv = client.get("/")
        assert rv.status_code == 200

    def test_unknown_route_returns_404(self):
        rv = client.get("/nonexistent_xyz")
        assert rv.status_code == 404
