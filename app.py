#!/usr/bin/env python3
"""
Orivet 遺伝子解析 Webアプリ（全犬種対応）
Flask ベースの Web インターフェース
"""

import os
import time
import uuid
import json
import shutil
import logging
import secrets
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
REPORT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

# セッションディレクトリの自動クリーンアップ（ディスク枯渇防止）
# REPORT_TTL_HOURS 環境変数で上書き可能（デフォルト24h）
SESSION_TTL_SECONDS = int(os.environ.get("REPORT_TTL_HOURS", "24")) * 3600


def _cleanup_old_session_dirs(folder: str, ttl_seconds: int = SESSION_TTL_SECONDS) -> int:
    """folder直下のサブディレクトリのうち mtime が ttl 超過のものを削除。削除数を返す。"""
    if not os.path.isdir(folder):
        return 0
    now = time.time()
    removed = 0
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if not os.path.isdir(path):
            continue
        try:
            if (now - os.path.getmtime(path)) > ttl_seconds:
                shutil.rmtree(path, ignore_errors=True)
                removed += 1
        except OSError as e:
            app.logger.warning("cleanup_skip path=%s err=%s", path, e)
    return removed


# 起動時に一度だけ実行（worker毎に走るが多重削除は冪等）
_removed_reports = _cleanup_old_session_dirs(REPORT_FOLDER)
_removed_uploads = _cleanup_old_session_dirs(UPLOAD_FOLDER)
app.logger.info(
    "startup_cleanup ttl_seconds=%d removed_reports=%d removed_uploads=%d",
    SESSION_TTL_SECONDS, _removed_reports, _removed_uploads,
)

ALLOWED_PDF_EXT = {".pdf"}
ALLOWED_IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".heic", ".heif"}

# マジックバイト検証 — 拡張子偽装された悪意あるファイルを弾く
_PDF_MAGIC = b"%PDF-"
_IMG_MAGICS = (
    b"\xff\xd8\xff",           # JPEG
    b"\x89PNG\r\n\x1a\n",      # PNG
    b"GIF8",                   # GIF
    b"BM",                     # BMP
    b"II*\x00", b"MM\x00*",    # TIFF (little/big endian)
    b"RIFF",                   # WEBP (RIFF container)
    b"ftypheic", b"ftypheix",  # HEIC
    b"ftypmif1", b"ftypmsf1",  # HEIF
)


def _is_valid_pdf(path: str) -> bool:
    try:
        with open(path, "rb") as fp:
            return fp.read(5) == _PDF_MAGIC
    except OSError:
        return False


def _is_valid_image(path: str) -> bool:
    try:
        with open(path, "rb") as fp:
            head = fp.read(16)
        return any(head[: len(m)] == m for m in _IMG_MAGICS)
    except OSError:
        return False


def _log_exc(stage: str, filename: str, exc: Exception, request_id: str = "") -> str:
    """例外を構造化ログに記録し、ユーザー提示用の error_id を返す。

    error_id をユーザー向けメッセージに含めることで、サポート問い合わせ時に
    バックエンドログから該当エラーを Grep 可能にする。
    request_id を渡すと analyze_start/success ログとも紐付け可能。
    """
    error_id = uuid.uuid4().hex[:8]
    app.logger.exception(
        "analyze_error error_id=%s request_id=%s stage=%s file=%s exc_type=%s",
        error_id, request_id or "-", stage, filename, type(exc).__name__,
    )
    return error_id


# Import analysis modules
from poodle_genetics import (
    parse_pdf, parse_pedigree_pdf, KNOWN_PEDIGREES,
    generate_unified_html, generate_excel,
    HAS_PDFPLUMBER, HAS_OCR,
    DISEASE_KB, TRAIT_KB, group_diseases_by_category,
    get_disease_severity, SEVERITY_LABELS,
    SYMPTOM_INDEX, filter_by_symptom,
    DISEASE_SLUG_INDEX, TRAIT_SLUG_INDEX, make_entry_slug,
    GUIDES, GUIDES_INDEX, GUIDES_BY_DISEASE, GUIDES_BY_TRAIT,
    get_disease_kb_localized, get_trait_kb_localized,
    HAS_EN_KB, SEVERITY_LABELS_EN, CATEGORY_LABELS_EN, SYMPTOM_LABELS_EN,
)

try:
    from poodle_genetics import try_ocr, parse_jkc_pedigree_text
except ImportError:
    pass


def allowed_file(filename, extensions):
    return os.path.splitext(filename)[1].lower() in extensions


# 遺伝子型テスト名 → シミュレーター用キーのマッピング
_TRAIT_TO_SIM_KEY = {
    "E Locus (Cream/Red/Yellow)": "e",
    "K Locus (Dominant Black)": "k",
    "A Locus (Agouti)": "a",
    "B Locus (Brown)": "b",
    "D (Dilute) Locus": "d",
    "M Locus (Merle/Dapple)": "m",
    "Pied": "s",
}

# 遺伝子型表記 → シミュレーターselect value のマッピング
_GENOTYPE_TO_SELECT = {
    # E locus
    "E/E": "EE", "E/e": "Ee", "e/e": "ee",
    # K locus
    "KB/KB": "KBKB", "K/K": "KBKB", "KB/ky": "KBky", "KB/kbr": "KBkbr",
    "ky/ky": "kyky", "kbr/ky": "kbrky", "kbr/kbr": "kbrkbr",
    # A locus
    "ay/ay": "ayay", "ay/at": "ayat", "at/at": "atat", "a/a": "aa",
    # B locus
    "BB": "BB", "Bb": "Bb", "bb": "bb",
    # D locus
    "D/D": "DD", "D/d": "Dd", "d/d": "dd",
    # M locus
    "m/m": "mm", "M/m": "Mm", "M/M": "MM",
    # S (Pied) locus
    "S/S": "SS", "S/sp": "Ssp", "sp/sp": "spsp",
}

# 健康検査名 → シミュレーターキーのマッピング
_HEALTH_TO_SIM_KEY = {
    "Chondrodystrophy and Intervertebral Disc Disease": "CDDY+IVDD",
    "CDDY+IVDD": "CDDY+IVDD",
    "Osteochondrodysplasia": "Osteochondrodysplasia",
    "Chondrodysplasia (CDPA)": "CDPA",
    "Macrothrombocytopenia": "Macrothrombocytopenia",
    "Methemoglobinemia": "Methemoglobinemia",
    "Von Willebrand's Disease Type 1": "vWD1",
    "Degenerative Myelopathy": "DM",
    "GM2 Gangliosidosis": "GM2",
    "Progressive Retinal Atrophy - prcd": "prcd-PRA",
}


def extract_sim_data(dog):
    """DogProfileからシミュレーター用の遺伝子型データを抽出"""
    name = dog.pet_name or dog.registered_name or ""
    sex = "male" if "male" in dog.sex.lower() else "female"

    color = {}
    for r in dog.trait_results:
        sim_key = _TRAIT_TO_SIM_KEY.get(r.test_name)
        if sim_key and r.genotype:
            select_val = _GENOTYPE_TO_SELECT.get(r.genotype, r.genotype)
            color[sim_key] = select_val

    health = {}
    for r in dog.health_results:
        sim_key = _HEALTH_TO_SIM_KEY.get(r.test_name)
        if sim_key and r.genotype:
            health[sim_key] = r.genotype.replace("/", "")

    return {
        "name": name,
        "sex": sex,
        "color": color,
        "health": health,
    }


@app.route("/healthz")
def healthz():
    """軽量ヘルスチェック（Render等の死活監視用、テンプレ描画なし）"""
    return jsonify({
        "status": "ok",
        "pdfplumber": HAS_PDFPLUMBER,
        "ocr": HAS_OCR,
    }), 200


@app.route("/version")
def version_info():
    """デプロイ情報・KB件数を返す（運用可視性向上のため）"""
    return jsonify({
        "service": "Orivet 遺伝子解析",
        "git_sha": os.environ.get("GIT_SHA", os.environ.get("RENDER_GIT_COMMIT", "unknown"))[:12],
        "render_service": os.environ.get("RENDER_SERVICE_NAME", "unknown"),
        "disease_kb_count": len(DISEASE_KB),
        "trait_kb_count": len(TRAIT_KB),
        "guides_count": len(GUIDES),
        "symptom_categories": len(SYMPTOM_INDEX),
        "session_ttl_hours": SESSION_TTL_SECONDS // 3600,
        "max_upload_mb": app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024),
        "features": {
            "pdfplumber": HAS_PDFPLUMBER,
            "ocr": HAS_OCR,
            "service_worker": True,
            "manifest": True,
        },
    }), 200


@app.errorhandler(413)
def request_entity_too_large(_e):
    """50MB超過時のユーザー向けメッセージ"""
    flash("ファイルサイズが上限（50MB）を超えています。サイズを下げて再度お試しください。", "error")
    return redirect(url_for("index")), 303


@app.route("/")
def index():
    return render_template("index.html", has_pdfplumber=HAS_PDFPLUMBER, has_ocr=HAS_OCR)


@app.route("/analyze", methods=["POST"])
def analyze():
    """PDF・血統書写真をアップロードして解析"""
    request_id = uuid.uuid4().hex[:8]
    request_start = time.perf_counter()
    session_id = uuid.uuid4().hex
    session_upload = os.path.join(UPLOAD_FOLDER, session_id)
    session_report = os.path.join(REPORT_FOLDER, session_id)
    os.makedirs(session_upload, exist_ok=True)
    os.makedirs(session_report, exist_ok=True)

    pdf_count = len([f for f in request.files.getlist("pdf_files") if f and f.filename])
    img_count = len([f for f in request.files.getlist("pedigree_files") if f and f.filename])
    app.logger.info(
        "analyze_start request_id=%s session_id=%s pdf_files=%d pedigree_files=%d",
        request_id, session_id, pdf_count, img_count,
    )

    dogs = []
    pedigrees = []

    # --- PDF files ---
    pdf_files = request.files.getlist("pdf_files")
    for f in pdf_files:
        if f and f.filename and allowed_file(f.filename, ALLOWED_PDF_EXT):
            safe_name = f"{uuid.uuid4().hex[:8]}_{secure_filename(f.filename) or 'upload.pdf'}"
            path = os.path.join(session_upload, safe_name)
            f.save(path)

            # マジックバイト検証（拡張子偽装対策）
            if not _is_valid_pdf(path):
                os.remove(path)
                flash(f"{f.filename}: PDFファイルとして認識できませんでした（ファイルが壊れているか形式が異なります）", "warning")
                continue

            # DNAプロファイル（DNAP）ファイルの事前判定
            fname_upper = (f.filename or "").upper()
            is_dnap = "DNAP" in fname_upper or "DNA PROFILE" in fname_upper
            # 「見方」「説明」ファイルの事前判定
            is_guide = "見方" in (f.filename or "") or "説明" in (f.filename or "")

            if HAS_PDFPLUMBER:
                try:
                    dog = parse_pdf(path)
                    if dog:
                        dogs.append(dog)
                    elif is_dnap or is_guide:
                        # DNAプロファイル・説明ファイルは静かにスキップ
                        pass
                    else:
                        # Orivet遺伝子検査PDFでない場合、血統書PDFとして解析を試みる
                        ped = parse_pedigree_pdf(path)
                        if ped:
                            pedigrees.append(ped)
                        else:
                            flash(f"{f.filename}: 遺伝子検査PDFにも血統書PDFにも該当しませんでした", "warning")
                except Exception as e:
                    eid = _log_exc("parse_pdf", f.filename, e, request_id)
                    flash(f"{f.filename}: PDF解析中にエラーが発生しました（{type(e).__name__} / error_id={eid}）", "warning")

    # --- Pedigree files (PDF + images) ---
    pedigree_files = request.files.getlist("pedigree_files")
    ocr_errors = []
    for f in pedigree_files:
        if f and f.filename:
            ext = os.path.splitext(f.filename)[1].lower()

            # 血統書PDF
            if ext == ".pdf":
                if HAS_PDFPLUMBER:
                    safe_name = f"{uuid.uuid4().hex[:8]}_{secure_filename(f.filename) or 'upload.pdf'}"
                    path = os.path.join(session_upload, safe_name)
                    f.save(path)
                    if not _is_valid_pdf(path):
                        os.remove(path)
                        ocr_errors.append(f"{f.filename}: PDFファイルとして認識できませんでした（ファイルが壊れているか形式が異なります）")
                        continue
                    try:
                        ped = parse_pedigree_pdf(path)
                        if ped:
                            pedigrees.append(ped)
                        else:
                            ocr_errors.append(f"{f.filename}: 血統書PDFとして解析できませんでした")
                    except Exception as e:
                        eid = _log_exc("parse_pedigree_pdf", f.filename, e, request_id)
                        ocr_errors.append(f"{f.filename}: PDF解析中にエラーが発生しました（{type(e).__name__} / error_id={eid}）")
                else:
                    ocr_errors.append(f"{f.filename}: PDF解析機能が利用できません（pdfplumber未インストール）")
                continue

            # 血統書画像
            if not allowed_file(f.filename, ALLOWED_IMG_EXT):
                ocr_errors.append(f"{f.filename}: サポートされていない形式です（{ext}）")
                continue
            safe_name = f"{uuid.uuid4().hex[:8]}_{secure_filename(f.filename) or 'upload.img'}"
            path = os.path.join(session_upload, safe_name)
            f.save(path)
            if not _is_valid_image(path):
                os.remove(path)
                ocr_errors.append(f"{f.filename}: 画像ファイルとして認識できませんでした（ファイルが壊れているか形式が異なります）")
                continue
            if HAS_OCR:
                try:
                    text = try_ocr(path)
                    if text:
                        ped = parse_jkc_pedigree_text(text)
                        if ped and ped.dog_name:
                            pedigrees.append(ped)
                        else:
                            ocr_errors.append(f"{f.filename}: 血統書データの解析に失敗しました")
                    else:
                        ocr_errors.append(f"{f.filename}: 画像からテキストを読み取れませんでした")
                except Exception as e:
                    eid = _log_exc("ocr", f.filename, e, request_id)
                    ocr_errors.append(f"{f.filename}: OCR処理中にエラーが発生しました（{type(e).__name__} / error_id={eid}）")
            else:
                ocr_errors.append(f"{f.filename}: OCR機能が利用できません（pytesseract未インストール）")

    for err in ocr_errors:
        flash(err, "warning")

    # --- Demo pedigree option ---
    use_demo = request.form.get("use_demo")
    if use_demo:
        pedigrees.append(KNOWN_PEDIGREES["seven"])

    if not dogs and not pedigrees:
        flash("解析可能なデータがありませんでした。PDFまたは血統書画像をアップロードしてください。", "error")
        app.logger.info(
            "analyze_empty request_id=%s session_id=%s pdf_files=%d pedigree_files=%d",
            request_id, session_id, pdf_count, img_count,
        )
        # cleanup
        shutil.rmtree(session_upload, ignore_errors=True)
        shutil.rmtree(session_report, ignore_errors=True)
        return redirect(url_for("index"))

    # Generate reports
    html_path = os.path.join(session_report, "report.html")
    xlsx_path = os.path.join(session_report, "report.xlsx")

    try:
        generate_unified_html(dogs, pedigrees, html_path)
        generate_excel(dogs, pedigrees, xlsx_path)
    except Exception as e:
        eid = _log_exc("generate_report", "report.html/xlsx", e, request_id)
        flash(f"レポート生成中にエラーが発生しました（{type(e).__name__} / error_id={eid}）", "error")
        shutil.rmtree(session_upload, ignore_errors=True)
        shutil.rmtree(session_report, ignore_errors=True)
        return redirect(url_for("index"))

    # Save dog genotype data for simulator
    try:
        if dogs:
            sim_data = [extract_sim_data(d) for d in dogs]
            with open(os.path.join(session_report, "dogs.json"), "w", encoding="utf-8") as f:
                json.dump(sim_data, f, ensure_ascii=False)

        # Save pedigree data for simulator COI tab
        if pedigrees:
            ped_data = []
            for ped in pedigrees:
                ped_json = {
                    "dog_name": ped.dog_name,
                    "sex": ped.sex,
                    "sire": ped.sire.name if ped.sire else "",
                    "dam": ped.dam.name if ped.dam else "",
                    "ss": ped.ss.name if ped.ss else "",
                    "sd": ped.sd.name if ped.sd else "",
                    "ds": ped.ds.name if ped.ds else "",
                    "dd": ped.dd.name if ped.dd else "",
                    "sss": ped.sss.name if ped.sss else "",
                    "ssd": ped.ssd.name if ped.ssd else "",
                    "sds": ped.sds.name if ped.sds else "",
                    "sdd": ped.sdd.name if ped.sdd else "",
                    "dss": ped.dss.name if ped.dss else "",
                    "dsd": ped.dsd.name if ped.dsd else "",
                    "dds": ped.dds.name if ped.dds else "",
                    "ddd": ped.ddd.name if ped.ddd else "",
                }
                ped_data.append(ped_json)
            with open(os.path.join(session_report, "pedigrees.json"), "w", encoding="utf-8") as f:
                json.dump(ped_data, f, ensure_ascii=False)
    except Exception as e:
        # シミュレーター用データ保存失敗は非致命的だが、原因追跡のため必ずログに残す
        error_id = uuid.uuid4().hex[:8]
        app.logger.warning(
            "simulator_data_save_failed error_id=%s session=%s err_type=%s err=%s",
            error_id, session_id, type(e).__name__, e,
        )

    # Cleanup uploaded files
    shutil.rmtree(session_upload, ignore_errors=True)

    elapsed_ms = int((time.perf_counter() - request_start) * 1000)
    app.logger.info(
        "analyze_success request_id=%s session_id=%s dogs=%d pedigrees=%d elapsed_ms=%d",
        request_id, session_id, len(dogs), len(pedigrees), elapsed_ms,
    )

    return redirect(url_for("report", session_id=session_id))


@app.route("/report/<session_id>")
def report(session_id):
    """生成されたレポートを表示"""
    report_dir = os.path.join(REPORT_FOLDER, session_id)
    html_path = os.path.join(report_dir, "report.html")
    xlsx_exists = os.path.exists(os.path.join(report_dir, "report.xlsx"))

    if not os.path.exists(html_path):
        flash("レポートが見つかりません。", "error")
        return redirect(url_for("index"))

    with open(html_path, "r", encoding="utf-8") as f:
        report_html = f.read()

    return render_template("report.html", report_html=report_html,
                           session_id=session_id, xlsx_exists=xlsx_exists)


@app.route("/api/dogs/<session_id>")
def api_dogs(session_id):
    """解析済みの犬の遺伝子型データをJSONで返す"""
    if ".." in session_id or "/" in session_id:
        return jsonify({"error": "不正なリクエスト"}), 400
    json_path = os.path.join(REPORT_FOLDER, session_id, "dogs.json")
    if not os.path.exists(json_path):
        return jsonify([])
    with open(json_path, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.route("/api/pedigrees/<session_id>")
def api_pedigrees(session_id):
    """解析済みの血統書データをJSONで返す"""
    if ".." in session_id or "/" in session_id:
        return jsonify({"error": "不正なリクエスト"}), 400
    json_path = os.path.join(REPORT_FOLDER, session_id, "pedigrees.json")
    if not os.path.exists(json_path):
        return jsonify([])
    with open(json_path, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.route("/download/<session_id>/<filename>")
def download(session_id, filename):
    """Excel ファイルのダウンロード"""
    # Prevent directory traversal
    if ".." in session_id or "/" in session_id or ".." in filename or "/" in filename:
        flash("不正なリクエストです。", "error")
        return redirect(url_for("index"))

    report_dir = os.path.join(REPORT_FOLDER, session_id)
    return send_from_directory(report_dir, filename, as_attachment=True)


def _get_lang(request):
    """request から lang を判定 (ja / en)"""
    lang = (request.args.get("lang") or "").strip().lower()
    if lang not in ("ja", "en"):
        accept = (request.headers.get("Accept-Language") or "").lower()
        lang = "en" if accept.startswith("en") else "ja"
    return lang


@app.route("/glossary")
def glossary():
    """遺伝子疾患・形質の辞書ページ。

    クエリパラメータ:
      ?q=xxx        — 全文検索
      ?severity=    — 重症度フィルター (high / medium / low / all)
      ?symptom=     — 症状ベース絞り込み (SYMPTOM_INDEX の id)
    """
    query = (request.args.get("q") or "").strip().lower()
    severity_filter = (request.args.get("severity") or "").strip().lower()
    symptom_filter = (request.args.get("symptom") or "").strip().lower()
    # 言語設定: ?lang=en または Accept-Language で判定
    lang = (request.args.get("lang") or "").strip().lower()
    if lang not in ("ja", "en"):
        # Accept-Language から推定（en-US, en-GB 等を en に）
        accept = (request.headers.get("Accept-Language") or "").lower()
        lang = "en" if accept.startswith("en") else "ja"

    def _filter_query(entries):
        if not query:
            return entries
        out = []
        for e in entries:
            haystack = " ".join([
                e.get("title", ""), e.get("summary", ""),
                e.get("mechanism", ""), e.get("symptoms", ""),
                e.get("phenotype", ""), e.get("advice", ""),
                " ".join(e.get("match", [])),
            ]).lower()
            if query in haystack:
                out.append(e)
        return out

    def _filter_severity(entries):
        if severity_filter not in ("high", "medium", "low"):
            return entries
        return [e for e in entries if get_disease_severity(e) == severity_filter]

    # 言語別 KB を取得（EN なら英訳マージ済み）
    base_diseases = get_disease_kb_localized(lang)
    base_traits = get_trait_kb_localized(lang)
    # 疾患: 症状 → 検索 → 重症度の順でフィルタリング
    diseases_after_symptom = filter_by_symptom(base_diseases, symptom_filter) if symptom_filter else base_diseases
    filtered_diseases = _filter_severity(_filter_query(diseases_after_symptom))
    # 形質は severity / symptom フィルター対象外（適用しない）
    filtered_traits = _filter_query(base_traits)

    # 重症度カウント（バッジ用） — 全疾患ベース
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for e in DISEASE_KB:
        severity_counts[get_disease_severity(e)] += 1

    # EN モード時は ラベル類も英語化
    severity_labels_for_ui = SEVERITY_LABELS
    category_labels_en = CATEGORY_LABELS_EN if lang == "en" else {}
    symptom_labels_en = SYMPTOM_LABELS_EN if lang == "en" else {}
    return render_template(
        "glossary.html",
        diseases=filtered_diseases,
        disease_groups=group_diseases_by_category(filtered_diseases),
        traits=filtered_traits,
        query=request.args.get("q", ""),
        severity_filter=severity_filter,
        severity_counts=severity_counts,
        severity_labels=severity_labels_for_ui,
        severity_labels_en=SEVERITY_LABELS_EN,
        category_labels_en=category_labels_en,
        symptom_labels_en=symptom_labels_en,
        get_severity=get_disease_severity,
        symptom_filter=symptom_filter,
        symptom_index=SYMPTOM_INDEX,
        total_diseases=len(DISEASE_KB),
        total_traits=len(TRAIT_KB),
        lang=lang,
    )


@app.route("/api/glossary")
def api_glossary():
    """辞書データを JSON で返す（クライアント側検索やシミュレーター連携用）"""
    return jsonify({
        "diseases": DISEASE_KB,
        "traits": TRAIT_KB,
    })


@app.route("/glossary/disease/<slug>")
def disease_detail_page(slug):
    """疾患個別ページ（SEO 対応・schema.org 構造化データ付き）"""
    entry = DISEASE_SLUG_INDEX.get(slug)
    if not entry:
        return render_template(
            "glossary_404.html",
            kind="疾患",
            slug=slug,
        ), 404
    lang = (request.args.get("lang") or "").strip().lower()
    if lang not in ("ja", "en"):
        accept = (request.headers.get("Accept-Language") or "").lower()
        lang = "en" if accept.startswith("en") else "ja"
    # EN 表示時は _en で上書き
    if lang == "en" and "_en" in entry:
        merged = {**entry, **entry["_en"]}
        merged["match"] = entry["match"]
        merged["_slug"] = entry.get("_slug")
        if "severity" in entry:
            merged["severity"] = entry["severity"]
        merged["references"] = entry.get("references", [])
        entry = merged
    severity = get_disease_severity(entry)
    related_guides = GUIDES_BY_DISEASE.get(slug, [])
    # 英語表示時のみ監修状態を表示する
    en_reviewed = False
    if lang == "en":
        original = DISEASE_SLUG_INDEX.get(slug, {})
        en_data = original.get("_en", {})
        en_reviewed = bool(en_data.get("reviewed"))
    return render_template(
        "disease_detail.html",
        entry=entry,
        slug=slug,
        severity=severity,
        severity_labels=SEVERITY_LABELS,
        related_guides=related_guides,
        en_reviewed=en_reviewed,
        canonical=request.url_root.rstrip("/") + f"/glossary/disease/{slug}",
        lang=lang,
    )


@app.route("/glossary/trait/<slug>")
def trait_detail_page(slug):
    """形質個別ページ（SEO 対応）"""
    entry = TRAIT_SLUG_INDEX.get(slug)
    if not entry:
        return render_template(
            "glossary_404.html",
            kind="形質",
            slug=slug,
        ), 404
    lang = (request.args.get("lang") or "").strip().lower()
    if lang not in ("ja", "en"):
        accept = (request.headers.get("Accept-Language") or "").lower()
        lang = "en" if accept.startswith("en") else "ja"
    if lang == "en" and "_en" in entry:
        merged = {**entry, **entry["_en"]}
        merged["match"] = entry["match"]
        merged["_slug"] = entry.get("_slug")
        merged["references"] = entry.get("references", [])
        entry = merged
    related_guides = GUIDES_BY_TRAIT.get(slug, [])
    en_reviewed = False
    if lang == "en":
        original = TRAIT_SLUG_INDEX.get(slug, {})
        en_data = original.get("_en", {})
        en_reviewed = bool(en_data.get("reviewed"))
    return render_template(
        "trait_detail.html",
        entry=entry,
        slug=slug,
        related_guides=related_guides,
        en_reviewed=en_reviewed,
        canonical=request.url_root.rstrip("/") + f"/glossary/trait/{slug}",
        lang=lang,
    )


@app.route("/sitemap.xml")
def sitemap():
    """sitemap.xml — 検索エンジン用全URL列挙"""
    from datetime import datetime
    base = request.url_root.rstrip("/")
    urls = [
        (base + "/", "1.0", "weekly"),
        (base + "/glossary", "0.9", "weekly"),
        (base + "/guides", "0.9", "weekly"),
        (base + "/sample", "0.8", "monthly"),
        (base + "/simulator", "0.7", "monthly"),
    ]
    # 各疾患・形質ページ（JA / EN 両方）
    for slug in DISEASE_SLUG_INDEX:
        urls.append((base + f"/glossary/disease/{slug}", "0.7", "monthly"))
        if HAS_EN_KB and slug in DISEASE_SLUG_INDEX and "_en" in DISEASE_SLUG_INDEX[slug]:
            urls.append((base + f"/glossary/disease/{slug}?lang=en", "0.6", "monthly"))
    for slug in TRAIT_SLUG_INDEX:
        urls.append((base + f"/glossary/trait/{slug}", "0.6", "monthly"))
        if HAS_EN_KB and slug in TRAIT_SLUG_INDEX and "_en" in TRAIT_SLUG_INDEX[slug]:
            urls.append((base + f"/glossary/trait/{slug}?lang=en", "0.5", "monthly"))
    # ガイド記事
    for guide in GUIDES:
        urls.append((base + f"/guides/{guide['slug']}", "0.8", "monthly"))
    # 英語 glossary トップ
    if HAS_EN_KB:
        urls.append((base + "/glossary?lang=en", "0.9", "weekly"))

    today = datetime.utcnow().strftime("%Y-%m-%d")
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                 'xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for loc, priority, freq in urls:
        # hreflang: 同一 slug に JA/EN がある疾患・形質ページには xhtml:link を追加
        alternates_xml = ""
        if HAS_EN_KB:
            # /glossary/disease/<slug> 系の URL は EN alternate あり
            for prefix in ("/glossary/disease/", "/glossary/trait/"):
                if prefix in loc and "?lang=" not in loc:
                    slug = loc.split(prefix, 1)[1].rstrip("/")
                    idx = DISEASE_SLUG_INDEX if "disease" in prefix else TRAIT_SLUG_INDEX
                    if slug in idx and "_en" in idx[slug]:
                        alternates_xml = (
                            f'<xhtml:link rel="alternate" hreflang="ja" href="{loc}"/>'
                            f'<xhtml:link rel="alternate" hreflang="en" href="{loc}?lang=en"/>'
                            f'<xhtml:link rel="alternate" hreflang="x-default" href="{loc}"/>'
                        )
                    break
            if loc.endswith("/glossary"):
                alternates_xml = (
                    f'<xhtml:link rel="alternate" hreflang="ja" href="{base}/glossary"/>'
                    f'<xhtml:link rel="alternate" hreflang="en" href="{base}/glossary?lang=en"/>'
                )
        xml_parts.append(
            f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod>"
            f"<changefreq>{freq}</changefreq><priority>{priority}</priority>{alternates_xml}</url>"
        )
    xml_parts.append("</urlset>")
    from flask import Response
    return Response("\n".join(xml_parts), mimetype="application/xml")


@app.route("/sample")
def sample_report():
    """サンプルレポートページ — 解析せずに何が得られるかを示す。"""
    lang = _get_lang(request)
    return render_template(
        "sample_report.html",
        canonical=request.url_root.rstrip("/") + "/sample",
        lang=lang,
    )


@app.route("/guides")
def guides_index():
    """ガイド記事一覧ページ。"""
    lang = _get_lang(request)
    return render_template(
        "guides_index.html",
        guides=GUIDES,
        canonical=request.url_root.rstrip("/") + "/guides",
        lang=lang,
    )


@app.route("/guides/<slug>")
def guide_detail(slug):
    """ガイド記事個別ページ。"""
    lang = _get_lang(request)
    guide = GUIDES_INDEX.get(slug)
    if not guide:
        return render_template(
            "glossary_404.html",
            kind="ガイド記事" if lang != "en" else "guide",
            slug=slug,
        ), 404
    # 関連疾患・形質エントリを解決
    related_diseases = [DISEASE_SLUG_INDEX[s] for s in guide.get("related_disease_slugs", []) if s in DISEASE_SLUG_INDEX]
    related_traits = [TRAIT_SLUG_INDEX[s] for s in guide.get("related_trait_slugs", []) if s in TRAIT_SLUG_INDEX]
    return render_template(
        "guide_detail.html",
        guide=guide,
        slug=slug,
        related_diseases=related_diseases,
        related_traits=related_traits,
        canonical=request.url_root.rstrip("/") + f"/guides/{slug}",
        lang=lang,
    )


@app.route("/robots.txt")
def robots_txt():
    """検索エンジン向けクロール設定"""
    base = request.url_root.rstrip("/")
    from flask import Response
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /analyze\n"        # POST endpoint
        "Disallow: /report/\n"        # session URLs (個人情報含む可能性)
        "Disallow: /api/\n"           # API endpoints
        "Disallow: /download/\n"      # session-locked files
        f"Sitemap: {base}/sitemap.xml\n"
    )
    return Response(body, mimetype="text/plain")


@app.route("/manifest.json")
def manifest_json():
    """PWA manifest — モバイル『ホーム画面に追加』対応

    アイコンは絵文字ベースの SVG プレースホルダー。
    Orivet ブランドアイコン受領後に置き換えてください (icons[].src)。
    """
    manifest = {
        "name": "Orivet 遺伝子解析",
        "short_name": "Orivet 遺伝子",
        "description": "犬の遺伝子検査PDFから健康・毛色・血統を解析",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f8f9fa",
        "theme_color": "#7c3aed",
        "lang": "ja",
        "icons": [
            {
                "src": "/static/icon-192.svg",
                "sizes": "192x192",
                "type": "image/svg+xml",
                "purpose": "any maskable",
            },
            {
                "src": "/static/icon-512.svg",
                "sizes": "512x512",
                "type": "image/svg+xml",
                "purpose": "any maskable",
            },
        ],
        "categories": ["health", "lifestyle", "education"],
        "shortcuts": [
            {
                "name": "辞書",
                "short_name": "辞書",
                "url": "/glossary",
                "description": "遺伝子疾患・形質辞書",
            },
            {
                "name": "シミュレーター",
                "short_name": "シミュレーター",
                "url": "/simulator",
                "description": "繁殖シミュレーター",
            },
            {
                "name": "ガイド",
                "short_name": "ガイド",
                "url": "/guides",
                "description": "ガイド記事",
            },
        ],
    }
    return jsonify(manifest)


@app.route("/sw.js")
def service_worker():
    """Service Worker をルート直下から配信（スコープ制御のため）

    Service Worker は配置パスより下のスコープしか制御できないため、
    /static/sw.js だとサイト全体を制御できない。/sw.js から配信する。
    """
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    response = send_from_directory(static_dir, "sw.js")
    # Service Worker は強制再フェッチでアップデート反映する必要があるため no-cache
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Service-Worker-Allowed"] = "/"
    return response


@app.route("/simulator")
def simulator():
    """繁殖シミュレーター（静的HTML。session_id はクライアント側JS が
    window.location.search から取り出して /api/dogs|pedigrees を呼ぶ）"""
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)),
                               "breeding_simulator.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
