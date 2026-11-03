(() => {
  'use strict';
  const root = document.documentElement;
  const toggle = document.getElementById('lang-toggle');
  const menuToggle = document.getElementById('menu-toggle');
  const nav = document.getElementById('primary-navigation');
  const nodes = document.querySelectorAll('[data-fa][data-en]');
  const year = document.getElementById('year');
  const description = document.querySelector('meta[name="description"]');
  const titles = {
    fa: document.documentElement.dataset.titleFa || 'سینا — پورتفولیوی توسعه‌دهنده | SiNAVM',
    en: document.documentElement.dataset.titleEn || 'Sina — Developer Portfolio | SiNAVM'
  };
  const descriptions = {
    fa: 'سینا؛ توسعه‌دهنده مستقل و سازنده ابزارهای متن‌باز در حوزه زیرساخت اینترنت، سنجش شبکه و اتوماسیون.',
    en: 'Sina is an independent developer building open-source tools for internet infrastructure, network measurement and automation.'
  };
  if (year) year.textContent = String(new Date().getFullYear());

  function setLanguage(lang, persist = true) {
    const selected = lang === 'en' ? 'en' : 'fa';
    root.lang = selected;
    root.dir = selected === 'fa' ? 'rtl' : 'ltr';
    root.dataset.lang = selected;
    nodes.forEach(node => {
      const value = node.dataset[selected];
      if (value !== undefined) node.textContent = value;
    });
    if (toggle) {
      toggle.textContent = selected === 'fa' ? 'EN' : 'فا';
      toggle.setAttribute('aria-label', selected === 'fa' ? 'Switch to English' : 'تغییر زبان به فارسی');
      toggle.setAttribute('aria-pressed', String(selected === 'en'));
    }
    document.title = titles[selected];
    if (description) description.content = descriptions[selected];
    if (persist) {
      try { localStorage.setItem('sinavm-portfolio-language', selected); } catch (_) { /* storage may be disabled */ }
    }
  }

  if (toggle) toggle.addEventListener('click', () => setLanguage(root.lang === 'fa' ? 'en' : 'fa'));
  if (menuToggle && nav) {
    menuToggle.addEventListener('click', () => {
      const open = menuToggle.getAttribute('aria-expanded') !== 'true';
      menuToggle.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('is-open', open);
    });
    nav.addEventListener('click', event => {
      if (event.target.closest('a')) {
        menuToggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('is-open');
      }
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && nav.classList.contains('is-open')) {
        menuToggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('is-open');
        menuToggle.focus();
      }
    });
  }

  let preferred = 'fa';
  try {
    const stored = localStorage.getItem('sinavm-portfolio-language');
    if (stored === 'fa' || stored === 'en') preferred = stored;
  } catch (_) { /* default to Persian */ }
  setLanguage(preferred, false);
})();
