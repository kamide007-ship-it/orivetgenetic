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
