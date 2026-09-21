/* CareerHub — static/js/main.js
   Vanilla JS only. Progressive enhancement: everything works without it. */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------------------------------------------------------
     Mobile navigation drawer
  --------------------------------------------------------------- */
  function initMobileNav() {
    var toggle = document.querySelector('.nav-hamburger');
    var drawer = document.querySelector('.nav-links');
    var overlay = document.querySelector('.nav-overlay');
    var body = document.body;
    if (!toggle || !drawer) return;

    function close() {
      drawer.classList.remove('open');
      toggle.classList.remove('active');
      if (overlay) overlay.classList.remove('show');
      body.classList.remove('nav-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
    function open() {
      drawer.classList.add('open');
      toggle.classList.add('active');
      if (overlay) overlay.classList.add('show');
      body.classList.add('nav-open');
      toggle.setAttribute('aria-expanded', 'true');
    }
    toggle.setAttribute('role', 'button');
    toggle.setAttribute('tabindex', '0');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.addEventListener('click', function () {
      drawer.classList.contains('open') ? close() : open();
    });
    toggle.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle.click(); }
    });
    if (overlay) overlay.addEventListener('click', close);
    drawer.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', close);
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 900) close();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
    });
  }

  /* ---------------------------------------------------------------
     User menu dropdown (desktop)
  --------------------------------------------------------------- */
  function initUserMenu() {
    var menu = document.querySelector('.user-menu');
    if (!menu) return;
    var trigger = menu.querySelector('.user-menu-trigger');
    var dropdown = menu.querySelector('.user-menu-dropdown');
    if (!trigger || !dropdown) return;

    trigger.addEventListener('click', function (e) {
      e.stopPropagation();
      menu.classList.toggle('open');
    });
    document.addEventListener('click', function (e) {
      if (!menu.contains(e.target)) menu.classList.remove('open');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') menu.classList.remove('open');
    });
  }

  /* ---------------------------------------------------------------
     Sidebar (mobile) toggle for app shell
  --------------------------------------------------------------- */
  function initSidebar() {
    var toggle = document.querySelector('.sidebar-toggle');
    var sidebar = document.querySelector('.app-sidebar');
    var overlay = document.querySelector('.sidebar-overlay');
    if (!toggle || !sidebar) return;

    function close() {
      sidebar.classList.remove('open');
      if (overlay) overlay.classList.remove('show');
    }
    function open() {
      sidebar.classList.add('open');
      if (overlay) overlay.classList.add('show');
    }
    toggle.addEventListener('click', function () {
      sidebar.classList.contains('open') ? close() : open();
    });
    if (overlay) overlay.addEventListener('click', close);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
    });
  }

  /* ---------------------------------------------------------------
     Password visibility toggle — works for any [data-password-toggle]
  --------------------------------------------------------------- */
  function initPasswordToggles() {
    document.querySelectorAll('[data-password-toggle]').forEach(function (btn) {
      var targetId = btn.getAttribute('data-password-toggle');
      var input = document.getElementById(targetId);
      if (!input) return;
      btn.addEventListener('click', function () {
        var isHidden = input.type === 'password';
        input.type = isHidden ? 'text' : 'password';
        btn.classList.toggle('showing', isHidden);
        btn.setAttribute('aria-label', isHidden ? 'Hide password' : 'Show password');
      });
    });
  }

  /* ---------------------------------------------------------------
     Flash messages — auto dismiss + manual close
  --------------------------------------------------------------- */
  function initFlashMessages() {
    var flashes = document.querySelectorAll('.flash');
    flashes.forEach(function (f, i) {
      var closeBtn = f.querySelector('.flash-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', function () { dismiss(f); });
      }
      var delay = 5500 + i * 300;
      var timer = setTimeout(function () { dismiss(f); }, delay);
      f.addEventListener('mouseenter', function () { clearTimeout(timer); });
    });
    function dismiss(el) {
      el.classList.add('flash-out');
      setTimeout(function () { el.remove(); }, 300);
    }
  }

  /* ---------------------------------------------------------------
     Scroll reveal — IntersectionObserver based
  --------------------------------------------------------------- */
  function initScrollReveal() {
    var els = document.querySelectorAll('[data-reveal]');
    if (!els.length) return;
    if (reduceMotion || !('IntersectionObserver' in window)) {
      els.forEach(function (el) { el.classList.add('revealed'); });
      return;
    }
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    els.forEach(function (el) { observer.observe(el); });
  }

  /* ---------------------------------------------------------------
     Submit-button loading state (skips forms marked data-no-loading)
  --------------------------------------------------------------- */
  function initFormLoadingStates() {
    document.querySelectorAll('form:not([data-no-loading])').forEach(function (form) {
      form.addEventListener('submit', function () {
        if (form.hasAttribute('data-confirmed-skip')) return;
        var btn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (btn && !btn.disabled) {
          btn.classList.add('btn-loading');
          btn.disabled = true;
          // Safety: never permanently lock the UI if navigation is client-side blocked
          setTimeout(function () { btn.disabled = false; }, 8000);
        }
      });
    });
  }

  /* ---------------------------------------------------------------
     Confirm dialogs for destructive actions
  --------------------------------------------------------------- */
  function initConfirmActions() {
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
      el.addEventListener('submit', function (e) {
        var msg = el.getAttribute('data-confirm') || 'Are you sure?';
        if (!window.confirm(msg)) {
          e.preventDefault();
          e.stopPropagation();
        }
      });
    });
  }

  /* ---------------------------------------------------------------
     Active nav link underline / state driven by data-active on server
     (already set server-side; this just enables keyboard focus ring
     consistency — no-op placeholder retained for extensibility)
  --------------------------------------------------------------- */

  /* ---------------------------------------------------------------
     Navbar shadow on scroll
  --------------------------------------------------------------- */
  function initNavbarScroll() {
    var nav = document.querySelector('.navbar');
    if (!nav) return;
    function onScroll() {
      if (window.scrollY > 8) nav.classList.add('scrolled');
      else nav.classList.remove('scrolled');
    }
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---------------------------------------------------------------
     Live character-free skill/interest chip preview inputs
     (progressively enhances any input with [data-chip-preview])
  --------------------------------------------------------------- */
  function initChipPreview() {
    document.querySelectorAll('[data-chip-preview]').forEach(function (input) {
      var target = document.getElementById(input.getAttribute('data-chip-preview'));
      if (!target) return;
      function render() {
        var parts = input.value.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
        target.innerHTML = '';
        if (!parts.length) {
          target.innerHTML = '<span class="chip-preview-empty">Nothing added yet</span>';
          return;
        }
        parts.forEach(function (p) {
          var span = document.createElement('span');
          span.className = 'chip';
          span.textContent = p;
          target.appendChild(span);
        });
      }
      input.addEventListener('input', render);
      render();
    });
  }

  /* ---------------------------------------------------------------
     File input filename display
  --------------------------------------------------------------- */
  function initFileInputs() {
    document.querySelectorAll('.file-input').forEach(function (input) {
      var label = input.closest('.file-drop');
      if (!label) return;
      var nameEl = label.querySelector('.file-drop-filename');
      input.addEventListener('change', function () {
        if (input.files && input.files[0]) {
          if (nameEl) nameEl.textContent = input.files[0].name;
          label.classList.add('has-file');
        } else {
          label.classList.remove('has-file');
        }
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initMobileNav();
    initUserMenu();
    initSidebar();
    initPasswordToggles();
    initFlashMessages();
    initScrollReveal();
    initFormLoadingStates();
    initConfirmActions();
    initNavbarScroll();
    initChipPreview();
    initFileInputs();
  });
})();
