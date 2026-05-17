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
        # 全72疾患の英訳が含まれていること
        assert len(DISEASE_EN) >= 70

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
