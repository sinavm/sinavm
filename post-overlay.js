(function () {
  const overlayId = 'sinavm-post-overlay';

  function ensureOverlay() {
    if (document.getElementById(overlayId)) return document.getElementById(overlayId);
    const wrap = document.createElement('div');
    wrap.id = overlayId;
    wrap.setAttribute('hidden', '');
    wrap.innerHTML = '<div class="sinavm-post-overlay-backdrop"></div><div class="sinavm-post-overlay-sheet" role="dialog" aria-modal="true"><button type="button" class="sinavm-post-overlay-close" aria-label="بستن">×</button><div class="sinavm-post-overlay-media"></div><div class="sinavm-post-overlay-text"></div><div class="sinavm-post-overlay-actions"></div></div>';
    document.body.appendChild(wrap);
    if (!document.getElementById('sinavm-post-overlay-style')) {
      const style = document.createElement('style');
      style.id = 'sinavm-post-overlay-style';
      style.textContent = '#' + overlayId + '{position:fixed;inset:0;z-index:2500;display:flex;align-items:center;justify-content:center;padding:18px}#' + overlayId + '[hidden]{display:none}#' + overlayId + ' .sinavm-post-overlay-backdrop{position:absolute;inset:0;background:rgba(2,6,23,.72);backdrop-filter:blur(10px)}#' + overlayId + ' .sinavm-post-overlay-sheet{position:relative;width:min(420px,100%);max-height:82vh;overflow:auto;background:rgba(15,23,42,.96);border:1px solid rgba(255,255,255,.12);border-radius:22px;padding:18px 16px 16px;z-index:1}#' + overlayId + ' .sinavm-post-overlay-close{position:absolute;top:8px;left:10px;background:transparent;border:0;color:#e2e8f0;font-size:22px;cursor:pointer}#' + overlayId + ' .sinavm-post-overlay-text{white-space:pre-wrap;line-height:1.8;font-size:.92rem;color:#e2e8f0;margin-top:12px}#' + overlayId + ' .sinavm-post-overlay-media img{width:100%;max-height:220px;object-fit:cover;border-radius:14px;display:block}#' + overlayId + ' .sinavm-post-overlay-actions{display:flex;gap:8px;margin-top:14px}#' + overlayId + ' .sinavm-post-overlay-actions a{flex:1;text-align:center;text-decoration:none;color:#0f172a;background:#f8fafc;border-radius:12px;padding:10px;font-weight:700;font-size:.85rem}';
      document.head.appendChild(style);
    }
    wrap.querySelector('.sinavm-post-overlay-backdrop').addEventListener('click', closeOverlay);
    wrap.querySelector('.sinavm-post-overlay-close').addEventListener('click', closeOverlay);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeOverlay();
    });
    return wrap;
  }

  function closeOverlay() {
    const el = document.getElementById(overlayId);
    if (el) el.setAttribute('hidden', '');
    document.body.style.overflow = '';
  }

  function openOverlay(post) {
    const el = ensureOverlay();
    const media = el.querySelector('.sinavm-post-overlay-media');
    const text = el.querySelector('.sinavm-post-overlay-text');
    const actions = el.querySelector('.sinavm-post-overlay-actions');
    media.innerHTML = '';
    if (post.media && post.media.url && post.media.type === 'photo') {
      const img = document.createElement('img');
      img.src = post.media.url;
      img.alt = '';
      media.appendChild(img);
    }
    text.textContent = post.text || '';
    const tg = post.link || 'https://t.me/sinavm';
    let extra = '';
    if (post.media && post.media.url && post.media.type === 'document') {
      extra = '<a href="' + post.media.url + '" target="_blank" rel="noopener">دانلود فایل</a>';
    }
    actions.innerHTML = extra + '<a href="' + tg + '" target="_blank" rel="noopener">باز کردن در تلگرام</a>';
    el.removeAttribute('hidden');
    document.body.style.overflow = 'hidden';
  }

  function bind(posts) {
    const root = document.getElementById('telegram-posts');
    if (!root) return;
    root.querySelectorAll('a.post-link').forEach(function (a) {
      a.addEventListener('click', function (e) {
        const href = a.getAttribute('href');
        const post = (posts || []).find(function (p) { return p.link === href; });
        if (!post) return;
        e.preventDefault();
        openOverlay(post);
      });
    });
  }

  window.sinavmBindPostOverlay = function () {
    fetch('posts_formatted.json')
      .then(function (r) { return r.json(); })
      .then(bind)
      .catch(function () {});
  };
})();
