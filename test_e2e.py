"""
Playwright E2E / 視覚回帰テスト（JS 実行を伴うブラウザテスト）。

test_app.py は Flask クライアントで生 HTML を検証するが、JavaScript は
実行されない。このファイルは実ブラウザ（Chromium）で毛色シミュレーターを
動かし、runColorSim() が描画する結果 DOM・アレル色丸の hex・モード切替を
検証する。「色丸 hex 変更などの見落とし」を防ぐ視覚回帰の役割。

playwright 未インストール環境では自動スキップ（既存 CI を壊さない）。
専用の e2e CI ジョブ（.github/workflows/test.yml）で実行する。

実行:  pip install playwright && playwright install chromium && pytest test_e2e.py
"""

import os
import sys
import glob
import types
import socket
import threading

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

# 重量依存のスタブ（test_app.py と同様、PDF/OCR 等は不要）
for _mod in ("pdfplumber", "pytesseract", "openpyxl"):
    sys.modules.setdefault(_mod, types.ModuleType(_mod))
_ph = types.ModuleType("pillow_heif")
_ph.register_heif_opener = lambda: None
sys.modules.setdefault("pillow_heif", _ph)
if "PIL" not in sys.modules:
    sys.modules["PIL"] = types.ModuleType("PIL")
    sys.modules["PIL.Image"] = types.ModuleType("PIL.Image")

sys.path.insert(0, os.path.dirname(__file__))
import app as _app  # noqa: E402


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _chromium_executable():
    """環境変数 PLAYWRIGHT_BROWSERS_PATH 下の pre-installed chromium を探す。
    見つからなければ None（playwright の既定に任せる）。"""
    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
    if base:
        for pat in ("chromium-*/chrome-linux/chrome",
                    "chromium_headless_shell-*/chrome-linux/headless_shell"):
            hits = sorted(glob.glob(os.path.join(base, pat)))
            if hits:
                return hits[-1]
    return None


@pytest.fixture(scope="module")
def live_server():
    """Flask を werkzeug サーバーでバックグラウンド起動し base URL を返す。"""
    from werkzeug.serving import make_server
    _app.app.config["TESTING"] = True
    port = _free_port()
    srv = make_server("127.0.0.1", port, _app.app, threaded=True)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}"
    srv.shutdown()


@pytest.fixture(scope="module")
def browser():
    exe = _chromium_executable()
    with sync_playwright() as p:
        launch_kwargs = {"headless": True, "args": ["--no-sandbox"]}
        if exe:
            launch_kwargs["executable_path"] = exe
        b = p.chromium.launch(**launch_kwargs)
        yield b
        b.close()


@pytest.fixture()
def page(browser):
    ctx = browser.new_context(viewport={"width": 1000, "height": 1400})
    pg = ctx.new_page()
    yield pg
    ctx.close()


def _open_sim(page, live_server):
    page.goto(live_server + "/simulator", wait_until="networkidle")
    return page


def test_simulator_runs_and_renders_colors(page, live_server):
    """サンプル父犬 × 母犬で毛色シミュを実行し、既知の表現型が描画される。

    exA (Ee KBky atat Bb DD) × exB (ee KBKB atat Bb DD)
    → クリーム/ホワイト・ブラック・ブラウンが出るはず（Python 検証済みの遺伝）。"""
    _open_sim(page, live_server)
    page.select_option("#sire-color", "exA")
    page.select_option("#dam-color", "exB")
    page.click("button:has-text('シミュレーション実行')")
    page.wait_for_selector("#color-results", state="visible")
    out = page.inner_text("#color-output")
    assert "クリーム" in out or "ホワイト" in out
    assert "ブラック" in out
    assert "%" in out


def test_incomplete_genotype_does_not_crash(page, live_server):
    """PDF 解析で一部の座位が欠落した犬でもシミュレーターがクラッシュしない。

    実際の Orivet PDF は座位が欠けることがあり、以前は cross(undefined) で
    TypeError を起こして runColorSim が停止（シミュレーション実行できない）
    していた。欠けた座位は既定値で補完し、警告を出しつつ予測を継続する。"""
    _open_sim(page, live_server)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    # 座位が欠落した PDF 犬を投入（k/a/d/m/s や a/b/m/s が無い）
    page.evaluate(
        """() => {
            addDogsToSimulator([
              {name:'PartialSire', sex:'male', color:{e:'Ee', b:'Bb'}, health:{}},
              {name:'PartialDam', sex:'female', color:{e:'ee', k:'KBKB', d:'DD'}, health:{}},
            ], 'pdf_');
        }"""
    )
    page.click("button:has-text('シミュレーション実行')")
    page.wait_for_selector("#color-results", state="visible")
    out = page.inner_text("#color-output")
    # クラッシュせず結果が出る
    assert "%" in out
    # 欠落座位の警告が表示される
    assert "読み取れませんでした" in out
    # JS 例外が発生していない
    assert errors == [], f"pageerror が発生: {errors}"


def test_allele_dot_hex_rendered(page, live_server):
    """アレル色丸が期待通りの背景 hex で描画される（hex 回帰検出）。
    詳細モードに切り替え、E アレルの黒 (#0a0a0a) 丸が存在することを確認。"""
    _open_sim(page, live_server)
    page.select_option("#sire-color", "exA")
    page.select_option("#dam-color", "exB")
    page.click("button:has-text('シミュレーション実行')")
    page.wait_for_selector("#color-results", state="visible")
    # 詳細モードに切替（アレルドットを含む詳細パネルを表示）
    page.click("#mode-advanced")
    # アレルドットが DOM に出現するまで待つ
    page.wait_for_function("document.querySelectorAll('.allele-dot').length > 0")
    # いずれかの色丸が E/B 座位の黒 hex (#0a0a0a=rgb(10,10,10)) を背景に持つ
    found_black = page.evaluate(
        """() => {
            const dots = document.querySelectorAll('.allele-dot');
            for (const d of dots) {
                const bg = getComputedStyle(d).backgroundColor.replace(/\\s/g, '');
                if (bg === 'rgb(10,10,10)') return true;
            }
            return false;
        }"""
    )
    assert found_black, "E/B 座位の黒アレル (#0a0a0a=rgb(10,10,10)) 丸が見つからない"


def test_beginner_advanced_mode_toggle(page, live_server):
    """初級モードで詳細パネルが隠れ、詳細モードで表示される。"""
    _open_sim(page, live_server)
    page.select_option("#sire-color", "exA")
    page.select_option("#dam-color", "exB")
    page.click("button:has-text('シミュレーション実行')")
    page.wait_for_selector("#color-results", state="visible")
    # 初級モード（デフォルト）: .sim-advanced-block は非表示
    adv = page.locator("#color-output .sim-advanced-block").first
    assert adv.is_hidden()
    # 詳細モードに切替 → 表示
    page.click("#mode-advanced")
    assert adv.is_visible()
    # 初級に戻す → 再び非表示
    page.click("#mode-beginner")
    assert adv.is_hidden()


def test_two_pair_compare_renders(page, live_server):
    """2ペア比較パネルを開いて2頭の母犬を選び、左右比較が描画される。"""
    _open_sim(page, live_server)
    page.select_option("#sire-color", "exA")
    # 比較パネルを開く（summary クリックで _syncCompareDropdowns が走る）
    page.click("#compare-panel summary")
    # ドロップダウンにサンプル母犬が入るまで待つ（option は visible 判定できないため JS で件数確認）
    page.wait_for_function("document.querySelectorAll('#compare-dam-a option').length >= 2")
    vals = page.evaluate(
        "() => [...document.querySelectorAll('#compare-dam-a option')].map(o => o.value)"
    )
    page.select_option("#compare-dam-a", vals[0])
    page.select_option("#compare-dam-b", vals[1])
    page.click("#compare-panel button:has-text('くらべる')")
    page.wait_for_selector("#compare-output .color-bar")
    out = page.inner_text("#compare-output")
    assert "父犬:" in out
    # 2 カラム（🅰 / 🅱）が描画される
    assert "🅰" in out and "🅱" in out


def test_health_warning_names_actual_disease(page, live_server):
    """健康リスク警告は実際にリスクのある疾患名を表示する（CDDY 決め打ちの修正）。

    DM を両親 P/P → 子 100% P/P。警告文が「変性性脊髄症」を挙げ、
    無関係の「CDDY遺伝子型」を挙げないことを確認。"""
    _open_sim(page, live_server)
    page.click(".tab:has-text('健康リスク')")
    page.select_option("#sire-health", "custom_h")
    page.select_option("#dam-health", "custom_h")
    page.wait_for_selector("#custom-health-sire", state="visible")
    page.select_option("#chs-DM", "PP")
    page.select_option("#chd-DM", "PP")
    page.click("button:has-text('健康リスク分析')")
    page.wait_for_selector("#health-results", state="visible")
    out = page.inner_text("#health-output")
    assert "変性性脊髄症" in out          # 実際の危険疾患が明記される
    assert "CDDY遺伝子型" not in out       # 無関係な決め打ち文言が出ない


def test_custom_health_input_computes(page, live_server):
    """健康リスク分析のカスタム入力: 父P/N × 母P/N → 25% P/P を表示。

    以前は「今後追加予定です」のプレースホルダーだった機能を実装。"""
    _open_sim(page, live_server)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.click(".tab:has-text('健康リスク')")
    page.select_option("#sire-health", "custom_h")
    page.select_option("#dam-health", "custom_h")
    # カスタムパネルが表示される
    page.wait_for_selector("#custom-health-sire", state="visible")
    page.wait_for_selector("#custom-health-dam", state="visible")
    # CDDY を両親 P/N に設定 → 子は 25% P/P
    page.select_option("#chs-CDDY_IVDD", "PN")
    page.select_option("#chd-CDDY_IVDD", "PN")
    page.click("button:has-text('健康リスク分析')")
    page.wait_for_selector("#health-results", state="visible")
    out = page.inner_text("#health-output")
    assert "%" in out
    assert "25" in out  # P/P 25%
    assert "今後追加予定" not in out
    assert errors == [], f"pageerror: {errors}"
