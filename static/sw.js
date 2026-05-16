// Service Worker for Orivet 遺伝子解析
// バージョン: PR #59 で導入
//
// キャッシュ戦略:
//   - app shell (HTML / 静的辞書 / アイコン): cache-first
//   - /api/* / /analyze / /report: network-only (常に最新)
//   - その他: network-first, fallback to cache
//
// ⚠️ Service Worker のスコープはこのファイルの配置パスで決まる。
//    /sw.js から配信することでサイト全体を制御可能。

const CACHE_VERSION = 'orivet-v1';
const CACHE_NAME = `app-shell-${CACHE_VERSION}`;

// オフラインでも閲覧したい最小コアアセット
const APP_SHELL = [
  '/',
  '/glossary',
  '/guides',
  '/sample',
  '/manifest.json',
  '/static/icon-192.svg',
  '/static/icon-512.svg',
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

  // 静的辞書ページ・KB ページ等は cache-first
  // - /, /glossary, /guides, /sample, /simulator, /static/*
  // - /glossary/disease/*, /glossary/trait/*, /guides/*
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
      }).catch(() => {
        // オフライン時のフォールバック: トップページの cache を返す
        return caches.match('/');
      });
    })
  );
});
