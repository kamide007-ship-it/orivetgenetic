#!/usr/bin/env python3
"""
プードル遺伝子総合解析 Webアプリ
Flask ベースの Web インターフェース
"""

import os
import uuid
import glob
import shutil
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "poodle-genetics-default-key")

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
REPORT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

ALLOWED_PDF_EXT = {".pdf"}
ALLOWED_IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

# Import analysis modules
from poodle_genetics import (
    parse_pdf, KNOWN_PEDIGREES, calc_coi_3gen,
    generate_unified_html, generate_excel,
    HAS_PDFPLUMBER, HAS_OCR,
)

try:
    from poodle_genetics import try_ocr, parse_jkc_pedigree_text
except ImportError:
    pass


def allowed_file(filename, extensions):
    return os.path.splitext(filename)[1].lower() in extensions


@app.route("/")
def index():
    return render_template("index.html", has_pdfplumber=HAS_PDFPLUMBER, has_ocr=HAS_OCR)


@app.route("/analyze", methods=["POST"])
def analyze():
    """PDF・血統書写真をアップロードして解析"""
    session_id = uuid.uuid4().hex[:12]
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
            safe_name = f"{uuid.uuid4().hex[:8]}_{f.filename}"
            path = os.path.join(session_upload, safe_name)
            f.save(path)
            if HAS_PDFPLUMBER:
                dog = parse_pdf(path)
                if dog:
                    dogs.append(dog)

    # --- Pedigree images ---
    pedigree_files = request.files.getlist("pedigree_files")
    for f in pedigree_files:
        if f and f.filename and allowed_file(f.filename, ALLOWED_IMG_EXT):
            safe_name = f"{uuid.uuid4().hex[:8]}_{f.filename}"
            path = os.path.join(session_upload, safe_name)
            f.save(path)
            if HAS_OCR:
                text = try_ocr(path)
                if text:
                    ped = parse_jkc_pedigree_text(text)
                    if ped and ped.dog_name:
                        pedigrees.append(ped)

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

    generate_unified_html(dogs, pedigrees, html_path)
    generate_excel(dogs, pedigrees, xlsx_path)

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
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)),
                               "breeding_simulator.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
