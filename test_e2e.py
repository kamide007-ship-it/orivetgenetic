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


def test_color_probabilities_sum_to_100_dilute_agouti(page, live_server):
    """毛色予測の確率が合計 100% になる（希釈アグーチの計上漏れ回帰テスト）。

    以前は E_ + ky/ky（アグーチ）経路が dd（希釈）を計上せず、ブルー
    ファントム等の確率が漏れて合計 93.75% 等になっていた。"""
    _open_sim(page, live_server)
    total = page.evaluate(
        """() => {
            // ky/ky + Dd × Dd（希釈が 25% 出る）+ at/at（ファントム）
            const sire = {e:'Ee', k:'kyky', a:'atat', b:'Bb', d:'Dd', m:'mm', s:'SS', g:'gg'};
            const dam  = {e:'Ee', k:'kyky', a:'atat', b:'Bb', d:'Dd', m:'mm', s:'SS', g:'gg'};
            const cons = _consolidateByBaseColor(_buildColorResults(sire, dam));
            let sum = 0;
            for (const [k, p] of Object.entries(cons)) {
                if (k === 'merle' || k === 'parti') continue;  // 上乗せ修飾は除外
                sum += p;
            }
            return sum;
        }"""
    )
    assert abs(total - 1.0) < 0.01, f"毛色確率の合計が 100% でない: {total}"


def test_pairing_summary_renders_on_load(page, live_server):
    """総合サマリーが初期表示（既定サンプル配合）で毛色と健康リスクを一望できる。

    競合の Pairing Predictor 同様「1回選べば全部出る」ことの回帰テスト。
    既定は exA(♂ブラック) × exB(♀クリーム)。両親 CDDY P/N → 子 25% P/P で高リスク。"""
    _open_sim(page, live_server)
    page.wait_for_selector("#pair-summary", state="visible")
    summ = page.inner_text("#pair-summary-body")
    assert "父" in summ and "%" in summ           # ペア名＋毛色%が出る
    assert "クリーム" in summ or "ブラック" in summ  # 予測毛色チップ
    assert "高リスク" in summ or "注意" in summ      # CDDY 健康リスクが集約表示される


def test_pair_selection_syncs_across_tabs(page, live_server):
    """父犬/母犬をどのタブで選んでも毛色・健康の両タブに同期する（配合ペア共通化）。"""
    _open_sim(page, live_server)
    # 毛色タブで母犬を変更 → 健康タブの母犬セレクトが追従
    page.select_option("#dam-color", "exI")
    assert page.eval_on_selector("#dam-health", "el => el.value") == "exI"
    # 健康タブで父犬を変更 → 毛色タブの父犬セレクトが追従
    page.click(".tab:has-text('健康リスク')")
    page.select_option("#sire-health", "exC")
    assert page.eval_on_selector("#sire-color", "el => el.value") == "exC"
    # custom ↔ custom_h の対応
    page.click(".tab:has-text('毛色')")
    page.select_option("#sire-color", "custom")
    assert page.eval_on_selector("#sire-health", "el => el.value") == "custom_h"


def test_no_horizontal_overflow_on_mobile(browser, live_server):
    """スマホ幅(375px)で横スクロール（はみ出し）が発生しない。"""
    ctx = browser.new_context(viewport={"width": 375, "height": 800})
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(live_server + "/simulator", wait_until="networkidle")
    pg.wait_for_selector("#pair-summary", state="visible")
    overflow = pg.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    ctx.close()
    assert overflow <= 2, f"モバイルで横方向にはみ出し: {overflow}px"
    assert errors == [], f"pageerror: {errors}"


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


def test_coi_full_sib_mating_is_25_percent(page, live_server):
    """近親交配係数: 全兄妹交配 → COI 25%（Wright's F の教科書値）。

    以前は指数を n₁+n₂+1 ではなく gen+gen+1 としており COI を 4 倍過小評価
    （兄妹交配が 25% ではなく 6.25% と表示）していた。仔犬起点の世代
    (父=1,祖父母=2) から親起点の世代 (gen-1) へ正しく変換する回帰テスト。

    父犬と母犬が全兄妹 = 同じ両親を共有 → 仔の祖父母(gen2)が父方母方で一致。"""
    _open_sim(page, live_server)
    page.click(".tab:has-text('近親交配係数')")
    page.fill("#p-sire", "SireDog")
    page.fill("#p-dam", "DamDog")
    # 全兄妹: 父方祖父母 = 母方祖父母（同一個体）
    page.fill("#p-ss", "SharedGrandpa")
    page.fill("#p-sd", "SharedGrandma")
    page.fill("#p-ds", "SharedGrandpa")
    page.fill("#p-dd", "SharedGrandma")
    page.click("button:has-text('COI算出')")
    page.wait_for_selector("#coi-results", state="visible")
    out = page.inner_text("#coi-output")
    assert "25.00%" in out, f"全兄妹交配の COI が 25% でない: {out[:200]}"
    assert "極めて高リスク" in out


def test_coi_first_cousin_mating_is_6_25_percent(page, live_server):
    """近親交配係数: いとこ交配 → COI 6.25%（アプリの目安表と一致）。

    父犬と母犬がいとこ = 曾祖父母(gen3)を父方母方で共有。"""
    _open_sim(page, live_server)
    page.click(".tab:has-text('近親交配係数')")
    page.fill("#p-sire", "SireDog")
    page.fill("#p-dam", "DamDog")
    # いとこ: 父方曾祖父母1 = 母方曾祖父母1（同一個体）
    page.fill("#p-sss", "SharedGGpa")
    page.fill("#p-ssd", "SharedGGma")
    page.fill("#p-dss", "SharedGGpa")
    page.fill("#p-dsd", "SharedGGma")
    page.click("button:has-text('COI算出')")
    page.wait_for_selector("#coi-results", state="visible")
    out = page.inner_text("#coi-output")
    assert "6.25%" in out, f"いとこ交配の COI が 6.25% でない: {out[:200]}"


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
