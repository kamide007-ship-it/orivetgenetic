// Service Worker for Orivet 遺伝子解析
// バージョン: PR #59 で導入
//
// キャッシュ戦略:
//   - /api/* / /analyze / /report / /download: network-only (常に最新・PII 非キャッシュ)
//   - / (トップ): network-only (flash メッセージのキャッシュ汚染を防ぐ)
//   - HTML ページ (/simulator, /glossary, /guides, /sample, /glossary/*, /guides/*):
//     network-first, fallback to cache (デプロイ後の修正を即座に反映。特にモバイルで
//     古い壊れた JS が残る問題を防ぐ)
//   - 静的アセット (/static/*): cache-first (stale-while-revalidate、高速表示優先)
//
// ⚠️ Service Worker のスコープはこのファイルの配置パスで決まる。
//    /sw.js から配信することでサイト全体を制御可能。

const CACHE_VERSION = 'orivet-v5';
const CACHE_NAME = `app-shell-${CACHE_VERSION}`;

// オフラインでも閲覧したい最小コアアセット
// 注: '/' は flash メッセージを含み得るので、ここから外して runtime で都度取得
const APP_SHELL = [
  '/glossary',
  '/guides',
  '/sample',
  '/manifest.json',
  '/static/favicon.svg',
  '/static/icon-192.svg',
  '/static/icon-512.svg',
  '/static/apple-touch-icon.svg',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // 個別 add() で失敗しても他は通す（一部 URL が 404 でも install を継続）
      return Promise.all(
        APP_SHELL.map((url) => cache.add(url).catch((e) => console.warn('SW cache failed:', url, e)))
      );
    })
  );
  // 即座にアクティブ化（既存 SW を上書き）
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    // 旧バージョンのキャッシュを削除
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k.startsWith('app-shell-') && k !== CACHE_NAME)
            .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // POST / PUT / DELETE は素通し（変更系は絶対にキャッシュしない）
  if (event.request.method !== 'GET') return;

  // 他オリジンへのリクエストは触らない（CDN/Wikipedia 等）
  if (url.origin !== self.location.origin) return;

  // API / 解析 / レポート / ダウンロード は network-only
  // (個人情報含むレスポンスをキャッシュしないため)
  if (
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/analyze') ||
    url.pathname.startsWith('/report/') ||
    url.pathname.startsWith('/download/')
  ) {
    return;  // ブラウザに任せる
  }

  // トップページ '/' は network-only（キャッシュしない）。
  // flash メッセージ（DNAP 案内・エラー等）は一度きりの personalized 内容で、
  // これをキャッシュするとネットワーク不調時に古い flash が再表示される
  // （更新を押すと消えるが、キャッシュが残ると出続ける問題の根治）。
  // よって '/' は絶対にキャッシュへ put しない。オフライン時はブラウザ既定に任せる
  // （'/' はアップロード POST が前提でありネットワーク必須のため）。
  if (url.pathname === '/' || url.pathname === '/index' || url.pathname === '/index.html') {
    event.respondWith(fetch(event.request));
    return;
  }

  // HTML ページ（/simulator, /glossary, /guides, /sample, /glossary/*, /guides/*）は
  // network-first にする。
  // 理由: cache-first（stale-while-revalidate）だと、デプロイ後もリロードするまで
  // 古い HTML/JS がキャッシュから返され、修正が届かない。特にモバイルはリロード
  // しないため「スマホでシミュレーターが動かない（古い壊れた版が残る）」問題が
  // 起きていた。network-first で常に最新を取得し、オフライン時のみキャッシュへ
  // フォールバックする。
  const isHtmlNav = event.request.mode === 'navigate' ||
    (event.request.headers.get('accept') || '').includes('text/html');
  if (isHtmlNav) {
    event.respondWith(
      fetch(event.request).then((response) => {
        if (response.ok && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((c) => c.put(event.request, clone)).catch(() => {});
        }
        return response;
      }).catch(() =>
        caches.match(event.request).then((c) => c || caches.match('/simulator') || caches.match('/'))
      )
    );
    return;
  }

  // 静的アセット（/static/* : SVG・JS 等）は cache-first（stale-while-revalidate）。
  // これらは頻繁には変わらず、変わってもファイル内容の差分は軽微なため高速表示を優先。
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        // バックグラウンドでネットワークから更新（stale-while-revalidate）
        fetch(event.request).then((fresh) => {
          if (fresh.ok) {
            caches.open(CACHE_NAME).then((c) => c.put(event.request, fresh.clone()));
          }
        }).catch(() => {});  // ネットワーク失敗時は無視
        return cached;
      }
      // キャッシュ未ヒット: ネットワーク取得 + 成功なら次回用にキャッシュ
      return fetch(event.request).then((response) => {
        if (response.ok && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((c) => c.put(event.request, clone));
        }
        return response;
      }).catch(() => caches.match('/'));
    })
  );
});
