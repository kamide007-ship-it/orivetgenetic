#!/usr/bin/env python3
"""
Orivet 遺伝子解析 Webアプリ（全犬種対応）
Flask ベースの Web インターフェース
"""

import os
import uuid
import json
import glob
import shutil
import secrets
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
REPORT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

ALLOWED_PDF_EXT = {".pdf"}
ALLOWED_IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".heic", ".heif"}

# Import analysis modules
from poodle_genetics import (
    parse_pdf, parse_pedigree_pdf, KNOWN_PEDIGREES, calc_coi_3gen,
    generate_unified_html, generate_excel,
    HAS_PDFPLUMBER, HAS_OCR,
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


@app.route("/")
def index():
    return render_template("index.html", has_pdfplumber=HAS_PDFPLUMBER, has_ocr=HAS_OCR)


@app.route("/analyze", methods=["POST"])
def analyze():
    """PDF・血統書写真をアップロードして解析"""
    session_id = uuid.uuid4().hex
    session_upload = os.path.join(UPLOAD_FOLDER, session_id)
    session_report = os.path.join(REPORT_FOLDER, session_id)
    os.makedirs(session_upload, exist_ok=True)
    os.makedirs(session_report, exist_ok=True)

    dogs = []
    pedigrees = []

    # --- PDF files ---
    pdf_files = request.files.getlist("pdf_files")
    for f in pdf_files:
        if f and f.filename and allowed_file(f.filename, ALLOWED_PDF_EXT):
            safe_name = f"{uuid.uuid4().hex[:8]}_{secure_filename(f.filename) or 'upload.pdf'}"
            path = os.path.join(session_upload, safe_name)
            f.save(path)

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
                    elif not is_dnap and not is_guide:
                        # Orivet PDFでない場合、血統書PDFとして解析を試みる
                        ped = parse_pedigree_pdf(path)
                        if ped:
                            pedigrees.append(ped)
                except Exception as e:
                    flash(f"{f.filename}: PDF解析中にエラーが発生しました（{type(e).__name__}）", "warning")

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
                    try:
                        ped = parse_pedigree_pdf(path)
                        if ped:
                            pedigrees.append(ped)
                        else:
                            ocr_errors.append(f"{f.filename}: 血統書PDFとして解析できませんでした")
                    except Exception as e:
                        ocr_errors.append(f"{f.filename}: PDF解析中にエラーが発生しました（{type(e).__name__}）")
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
                    ocr_errors.append(f"{f.filename}: OCR処理中にエラーが発生しました（{type(e).__name__}）")
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
        flash(f"レポート生成中にエラーが発生しました（{type(e).__name__}: {e}）", "error")
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
    except Exception:
        pass  # シミュレーター用データ保存失敗は非致命的

    # Cleanup uploaded files
    shutil.rmtree(session_upload, ignore_errors=True)

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


@app.route("/simulator")
def simulator():
    """繁殖シミュレーター"""
    session_id = request.args.get("session")
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)),
                               "breeding_simulator.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
