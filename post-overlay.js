(function () {
  const overlayId = 'sinavm-post-overlay';
  const pages = 'https://sinavm.github.io/sinavm/';

  function absUrl(url) {
    if (!url) return '';
    if (/^https?:\/\//i.test(url)) return url;
    return pages + url.replace(/^\/+/, '');
  }

  function cleanText(text) {
    return (text || '')
      .split('\n')
      .filter(function (line) {
        const value = line.trim();
        return !/^رمز(?:\s+عبور)?\s*[:：=]/i.test(value) &&
          !/^(?:password|pass)\s*[:：=]/i.test(value);
      })
      .join('\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim();
  }

  function appendFormattedText(container, value) {
    const text = cleanText(value);
    const urlPattern = /https?:\/\/[^\s<>()]+/g;
    let lastIndex = 0;
    let match;
    while ((match = urlPattern.exec(text)) !== null) {
      container.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
      const anchor = document.createElement('a');
      const url = match[0].replace(/[.,!?،؛؟]+$/, '');
      anchor.href = url;
      anchor.textContent = url;
      anchor.target = '_blank';
      anchor.rel = 'noopener noreferrer';
      container.appendChild(anchor);
      container.appendChild(document.createTextNode(match[0].slice(url.length)));
      lastIndex = match.index + match[0].length;
    }
    container.appendChild(document.createTextNode(text.slice(lastIndex)));
  }

  function ensureOverlay() {
    let wrap = document.getElementById(overlayId);
    if (wrap) return wrap;
    wrap = document.createElement('div');
    wrap.id = overlayId;
    wrap.hidden = true;
    wrap.innerHTML = '<div class="sinavm-post-overlay-backdrop"></div><section class="sinavm-post-overlay-sheet" role="dialog" aria-modal="true" aria-label="جزئیات پست"><button type="button" class="sinavm-post-overlay-close" aria-label="بستن">×</button><div class="sinavm-post-overlay-heading"></div><div class="sinavm-post-overlay-media"></div><div class="sinavm-post-overlay-text"></div><div class="sinavm-post-overlay-pass" hidden></div><div class="sinavm-post-overlay-file" hidden></div><div class="sinavm-post-overlay-actions"></div></section>';
    document.body.appendChild(wrap);
    if (!document.getElementById('sinavm-post-overlay-style')) {
      const style = document.createElement('style');
      style.id = 'sinavm-post-overlay-style';
      style.textContent = '#' + overlayId + '{position:fixed;inset:0;z-index:2500;display:flex;align-items:center;justify-content:center;padding:16px}#' + overlayId + '[hidden]{display:none}#' + overlayId + ' .sinavm-post-overlay-backdrop{position:absolute;inset:0;background:rgba(2,6,23,.78);backdrop-filter:blur(9px)}#' + overlayId + ' .sinavm-post-overlay-sheet{position:relative;width:min(640px,100%);max-height:88vh;overflow:auto;background:#101b31;border:1px solid rgba(255,255,255,.14);border-radius:22px;padding:24px 20px 18px;z-index:1;text-align:right;box-shadow:0 24px 80px rgba(0,0,0,.45)}#' + overlayId + ' .sinavm-post-overlay-close{position:absolute;top:8px;left:12px;background:rgba(255,255,255,.08);border:0;border-radius:10px;width:34px;height:34px;color:#e2e8f0;font-size:23px;cursor:pointer}#' + overlayId + ' .sinavm-post-overlay-heading{color:#94a3b8;font-size:.78rem;margin:0 42px 14px 0}#' + overlayId + ' .sinavm-post-overlay-text{white-space:pre-wrap;overflow-wrap:anywhere;word-break:normal;line-height:2;font-size:.95rem;color:#e2e8f0;margin-top:10px;text-align:right;unicode-bidi:plaintext}#' + overlayId + ' .sinavm-post-overlay-text a{color:#67e8f9;text-decoration:underline}#' + overlayId + ' .sinavm-post-overlay-media img,#' + overlayId + ' .sinavm-post-overlay-media video{width:100%;max-height:340px;object-fit:contain;border-radius:14px;display:block;background:#020617;margin-bottom:14px}#' + overlayId + ' .sinavm-post-overlay-pass{margin-top:14px;background:rgba(251,191,36,.1);border:1px solid rgba(251,191,36,.3);border-radius:12px;padding:10px 12px;color:#fde68a;overflow-wrap:anywhere}#' + overlayId + ' .sinavm-post-overlay-file{display:flex;align-items:center;gap:12px;margin-top:16px;padding:14px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:14px;min-width:0}#' + overlayId + ' .sinavm-post-overlay-file-icon{font-size:1.5rem}#' + overlayId + ' .sinavm-post-overlay-file-info{min-width:0;flex:1}#' + overlayId + ' .sinavm-post-overlay-file-info strong{display:block;color:#f8fafc;overflow-wrap:anywhere}#' + overlayId + ' .sinavm-post-overlay-file-info small{display:block;color:#94a3b8;margin-top:4px}#' + overlayId + ' .sinavm-post-overlay-actions{display:flex;gap:9px;margin-top:16px;flex-wrap:wrap}#' + overlayId + ' .sinavm-post-overlay-actions a,#' + overlayId + ' .sinavm-post-overlay-actions button{flex:1;min-width:130px;text-align:center;text-decoration:none;color:#0f172a;background:#e2e8f0;border:0;border-radius:12px;padding:11px;font-weight:700;font-size:.86rem;font-family:inherit;cursor:pointer}#' + overlayId + ' .sinavm-post-overlay-actions .secondary{background:rgba(255,255,255,.1);color:#e2e8f0}';
      document.head.appendChild(style);
    }
    wrap.querySelector('.sinavm-post-overlay-backdrop').addEventListener('click', closeOverlay);
    wrap.querySelector('.sinavm-post-overlay-close').addEventListener('click', closeOverlay);
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') closeOverlay();
    });
    return wrap;
  }

  function closeOverlay() {
    const element = document.getElementById(overlayId);
    if (element) element.hidden = true;
    document.body.style.overflow = '';
  }

  function downloadNamed(url, name) {
    fetch(url).then(function (response) {
      if (!response.ok) throw new Error('Download failed');
      return response.blob();
    }).then(function (blob) {
      const anchor = document.createElement('a');
      anchor.href = URL.createObjectURL(blob);
      anchor.download = name;
      document.body.appendChild(anchor);
      anchor.click();
      setTimeout(function () {
        URL.revokeObjectURL(anchor.href);
        anchor.remove();
      }, 1500);
    }).catch(function () {
      window.open(url, '_blank', 'noopener');
    });
  }

  function openOverlay(post) {
    const element = ensureOverlay();
    const media = element.querySelector('.sinavm-post-overlay-media');
    const text = element.querySelector('.sinavm-post-overlay-text');
    const actions = element.querySelector('.sinavm-post-overlay-actions');
    const fileBox = element.querySelector('.sinavm-post-overlay-file');
    const passBox = element.querySelector('.sinavm-post-overlay-pass');
    const attachment = post.media || {};
    media.replaceChildren();
    text.replaceChildren();
    actions.replaceChildren();
    fileBox.hidden = true;
    fileBox.replaceChildren();
    passBox.hidden = !post.password;
    passBox.textContent = post.password ? 'رمز عبور: ' + post.password : '';
    element.querySelector('.sinavm-post-overlay-heading').textContent = post.date_label || '';
    appendFormattedText(text, post.text || '');

    const mediaUrl = absUrl(attachment.download_url || attachment.url);
    if (attachment.type === 'photo' && mediaUrl) {
      const image = document.createElement('img');
      image.src = mediaUrl;
      image.alt = 'تصویر پیوست‌شده به پست';
      image.loading = 'lazy';
      media.appendChild(image);
    } else if (attachment.type === 'video' && mediaUrl) {
      const video = document.createElement('video');
      video.src = mediaUrl;
      video.controls = true;
      video.preload = 'metadata';
      media.appendChild(video);
    }

    const fileUrl = mediaUrl;
    if ((attachment.type === 'document' || attachment.type === 'video') && fileUrl) {
      fileBox.hidden = false;
      const icon = document.createElement('span');
      icon.className = 'sinavm-post-overlay-file-icon';
      icon.textContent = '📎';
      const info = document.createElement('div');
      info.className = 'sinavm-post-overlay-file-info';
      const name = document.createElement('strong');
      name.textContent = attachment.original_name || attachment.filename || 'فایل پیوست';
      const detail = document.createElement('small');
      const size = attachment.size ? ' · ' + (attachment.size / 1024 / 1024).toFixed(2) + ' MB' : '';
      detail.textContent = (attachment.kind || 'فایل پیوست') + size;
      info.append(name, detail);
      fileBox.append(icon, info);
      const download = document.createElement('button');
      download.type = 'button';
      download.textContent = 'دانلود فایل';
      download.addEventListener('click', function () {
        downloadNamed(fileUrl, attachment.original_name || attachment.filename || 'sinavm-file');
      });
      actions.appendChild(download);
    }

    if (post.link) {
      const telegram = document.createElement('a');
      telegram.href = post.link;
      telegram.target = '_blank';
      telegram.rel = 'noopener noreferrer';
      telegram.textContent = 'باز کردن در تلگرام';
      if (actions.children.length) telegram.className = 'secondary';
      actions.appendChild(telegram);
    }
    element.hidden = false;
    document.body.style.overflow = 'hidden';
  }

  function bind(posts) {
    const root = document.getElementById('telegram-posts');
    if (!root) return;
    root.querySelectorAll('a.post-link').forEach(function (anchor) {
      anchor.addEventListener('click', function (event) {
        const href = anchor.getAttribute('href');
        const post = (posts || []).find(function (item) { return item.link === href; });
        if (!post) return;
        event.preventDefault();
        openOverlay(post);
      });
    });
  }

  window.sinavmBindPostOverlay = function () {
    fetch('posts_formatted.json')
      .then(function (response) {
        if (!response.ok) throw new Error('Posts unavailable');
        return response.json();
      })
      .then(bind)
      .catch(function () {});
  };
})();