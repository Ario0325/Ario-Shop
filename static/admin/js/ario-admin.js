/* ==========================================================================
   Ario Shop — admin shell behaviour
   Drawer · popovers · theme · command palette · responsive tables.
   Progressive enhancement: every admin page works without this file.
   ========================================================================== */
(function () {
    'use strict';

    var doc = document;
    var body = doc.body;
    var root = doc.documentElement;
    var MOBILE = '(max-width: 1024px)';
    var THEME_KEY = 'ario-admin-theme';

    function $(sel, ctx) { return (ctx || doc).querySelector(sel); }
    function $$(sel, ctx) { return Array.prototype.slice.call((ctx || doc).querySelectorAll(sel)); }
    function isMobile() { return window.matchMedia(MOBILE).matches; }

    /* ── theme ─────────────────────────────────────────────────────────────── */
    function currentTheme() {
        return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    }

    function applyTheme(theme) {
        if (theme === 'dark') root.setAttribute('data-theme', 'dark');
        else root.removeAttribute('data-theme');

        try { localStorage.setItem(THEME_KEY, theme); } catch (e) { /* private mode */ }

        var meta = $('meta[name="theme-color"]');
        if (meta) meta.setAttribute('content', theme === 'dark' ? '#150A10' : '#F7F1EA');

        var btn = $('#adm-theme');
        if (btn) btn.setAttribute('aria-label', theme === 'dark' ? 'روشن کردن پوسته' : 'تاریک کردن پوسته');

        doc.dispatchEvent(new CustomEvent('adm:themechange', { detail: { theme: theme } }));
    }

    function initTheme() {
        var btn = $('#adm-theme');
        var stored = null;
        try { stored = localStorage.getItem(THEME_KEY); } catch (e) { /* ignore */ }

        var theme = stored === 'dark' || (!stored && window.matchMedia('(prefers-color-scheme: dark)').matches)
            ? 'dark'
            : 'light';
        if (theme === 'dark') root.setAttribute('data-theme', 'dark');
        var meta = $('meta[name="theme-color"]');
        if (meta) meta.setAttribute('content', theme === 'dark' ? '#150A10' : '#F7F1EA');
        if (btn) {
            btn.setAttribute('aria-label', theme === 'dark' ? 'روشن کردن پوسته' : 'تاریک کردن پوسته');
            btn.addEventListener('click', function () {
                applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
            });
        }
    }

    /* ── nav drawer (mobile) ───────────────────────────────────────────────── */
    function initDrawer() {
        var rail = $('#adm-rail');
        var burger = $('#adm-burger');
        var scrim = $('#adm-scrim');
        var close = $('#adm-rail-close');
        if (!rail || !burger || !scrim) return;

        function open() {
            body.classList.add('adm-nav-open');
            scrim.hidden = false;
            requestAnimationFrame(function () { scrim.style.display = ''; });
            burger.setAttribute('aria-expanded', 'true');
        }
        function shut() {
            body.classList.remove('adm-nav-open');
            scrim.hidden = true;
            burger.setAttribute('aria-expanded', 'false');
        }

        burger.addEventListener('click', function () {
            if (body.classList.contains('adm-nav-open')) { shut(); burger.focus(); }
            else open();
        });
        scrim.addEventListener('click', function () { shut(); burger.focus(); });
        if (close) close.addEventListener('click', function () { shut(); burger.focus(); });

        doc.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && body.classList.contains('adm-nav-open')) shut();
        });

        var mq = window.matchMedia(MOBILE);
        var onWidth = function () { if (!mq.matches) shut(); };
        if (mq.addEventListener) mq.addEventListener('change', onWidth);
        else if (mq.addListener) mq.addListener(onWidth);
    }

    /* ── popovers ──────────────────────────────────────────────────────────── */
    function initPopovers() {
        var pops = $$('[data-pop]');
        if (!pops.length) return;

        function closeAll(except) {
            pops.forEach(function (pop) {
                if (pop === except) return;
                var panel = $('[data-pop-toggle]', pop);
                var id = panel && panel.getAttribute('aria-controls');
                var target = id ? doc.getElementById(id) : null;
                if (target) target.hidden = true;
                if (panel) panel.setAttribute('aria-expanded', 'false');
            });
        }

        pops.forEach(function (pop) {
            var toggle = $('[data-pop-toggle]', pop);
            if (!toggle) return;
            var id = toggle.getAttribute('aria-controls');
            var panel = id ? doc.getElementById(id) : null;
            if (!panel) return;

            toggle.addEventListener('click', function (e) {
                e.stopPropagation();
                var willOpen = panel.hidden;
                closeAll(pop);
                panel.hidden = !willOpen;
                toggle.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
                if (willOpen) {
                    var focusable = panel.querySelector('a, button, input');
                    if (focusable && e.detail !== 0) focusable.focus({ preventScroll: true });
                }
            });
        });

        doc.addEventListener('click', function (e) {
            var inside = pops.some(function (pop) { return pop.contains(e.target); });
            if (!inside) closeAll(null);
        });

        doc.addEventListener('keydown', function (e) {
            if (e.key !== 'Escape') return;
            var opened = pops.filter(function (pop) {
                return $('[data-pop-toggle]', pop) && $('[data-pop-toggle]', pop).getAttribute('aria-expanded') === 'true';
            });
            if (opened.length) {
                closeAll(null);
                var toggle = $('[data-pop-toggle]', opened[0]);
                if (toggle) toggle.focus();
            }
        });
    }

    /* ── command palette ───────────────────────────────────────────────────── */
    function initPalette() {
        var palette = $('#adm-palette');
        if (!palette) return;

        var input = $('#adm-palette-input');
        var list = $('#adm-palette-list');
        var empty = $('#adm-palette-empty');
        var items = $$('[data-palette-item]', list);
        var selected = -1;

        var trMap = { 'ي': 'ی', 'ك': 'ک', 'ۀ': 'ه', 'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ؤ': 'و', 'ة': 'ه' };
        function normalize(text) {
            return String(text || '')
                .toLowerCase()
                .replace(/[\u064B-\u065F\u0670\u0640\u200c\u200d]/g, '')
                .replace(/[يكۀأإآؤة]/g, function (ch) { return trMap[ch] || ch; })
                .replace(/[۰-۹]/g, function (d) { return String(d.charCodeAt(0) - 0x06F0); })
                .replace(/[٠-٩]/g, function (d) { return String(d.charCodeAt(0) - 0x0660); })
                .replace(/\s+/g, ' ')
                .trim();
        }

        items.forEach(function (item) {
            item._search = normalize(item.getAttribute('data-search') + ' ' + item.textContent);
        });

        function visibleItems() {
            return items.filter(function (item) { return !item.hidden; });
        }

        function select(index) {
            var shown = visibleItems();
            items.forEach(function (item) {
                item.classList.remove('is-selected');
                item.setAttribute('aria-selected', 'false');
            });
            if (!shown.length) { selected = -1; return; }
            if (index < 0) index = shown.length - 1;
            if (index >= shown.length) index = 0;
            selected = index;
            shown.forEach(function (item, i) {
                var on = i === selected;
                item.classList.toggle('is-selected', on);
                item.setAttribute('aria-selected', on ? 'true' : 'false');
                if (on && item.scrollIntoView) item.scrollIntoView({ block: 'nearest' });
            });
        }

        function filter() {
            var q = normalize(input.value);
            var shown = 0;
            items.forEach(function (item) {
                var match = !q || item._search.indexOf(q) !== -1;
                item.hidden = !match;
                if (match) shown += 1;
            });
            if (empty) empty.hidden = shown !== 0;
            selected = -1;
            if (shown) select(0);
        }

        function open() {
            palette.hidden = false;
            body.classList.add('adm-palette-open');
            input.value = '';
            filter();
            input.focus();
        }

        function shut() {
            palette.hidden = true;
            body.classList.remove('adm-palette-open');
        }

        ['#adm-search-open', '#adm-search-open-rail'].forEach(function (sel) {
            var btn = $(sel);
            if (btn) btn.addEventListener('click', open);
        });

        $$('[data-palette-close]', palette).forEach(function (el) {
            el.addEventListener('click', shut);
        });

        input.addEventListener('input', filter);

        input.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowDown') { e.preventDefault(); select(selected + 1); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); select(selected - 1); }
            else if (e.key === 'Enter') {
                var shown = visibleItems();
                if (selected >= 0 && shown[selected]) {
                    e.preventDefault();
                    window.location.href = shown[selected].getAttribute('href');
                }
            } else if (e.key === 'Escape') { shut(); }
        });

        doc.addEventListener('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
                e.preventDefault();
                if (palette.hidden) open(); else shut();
            } else if (e.key === 'Escape' && !palette.hidden) {
                shut();
            }
        });
    }

    /* ── mobile table labels ───────────────────────────────────────────────── */
    function initTableLabels() {
        $$('table#result_list, table.tabular-data, .inline-group .tabular table').forEach(function (table) {
            var headers = $$('thead th', table).map(function (th) {
                return (th.textContent || '').trim();
            });
            if (!headers.length) return;
            $$('tbody tr', table).forEach(function (row) {
                var cells = row.children;
                for (var i = 0; i < cells.length; i += 1) {
                    var cell = cells[i];
                    if (cell.tagName === 'TD' || cell.tagName === 'TH') {
                        var label = headers[i] || '';
                        if (label && !cell.hasAttribute('data-label')) {
                            cell.setAttribute('data-label', label);
                        }
                    }
                }
            });
        });
    }

    /* ── sticky topbar shadow ──────────────────────────────────────────────── */
    function initScrollState() {
        var topbar = $('.adm-topbar');
        if (!topbar) return;
        var update = function () { topbar.classList.toggle('is-scrolled', window.scrollY > 6); };
        update();
        window.addEventListener('scroll', update, { passive: true });
    }

    /* ── bulk-action feedback ──────────────────────────────────────────────── */
    function initActionFeedback() {
        var form = $('#changelist-form');
        if (!form) return;
        form.addEventListener('submit', function () {
            var checked = form.querySelectorAll('input.action-select:checked').length;
            var button = form.querySelector('button[name="index"]');
            if (button && checked > 0) button.disabled = true;
        });
    }

    /* ── keep selected nav item in view ────────────────────────────────────── */
    function initActiveNav() {
        var active = $('.adm-navlink.is-active');
        if (active && active.scrollIntoView) active.scrollIntoView({ block: 'nearest' });
    }

    /* ── compact mobile filters ────────────────────────────────────────────── */
    function initFilterCollapse() {
        var filter = $('#changelist-filter');
        if (!filter || !window.matchMedia('(max-width: 1024px)').matches) return;
        $$('details', filter).forEach(function (item) { item.open = false; });
    }

    function boot() {
        initTheme();
        initDrawer();
        initPopovers();
        initPalette();
        initTableLabels();
        initFilterCollapse();
        initScrollState();
        initActionFeedback();
        initActiveNav();
        doc.addEventListener('formset:added', function () { initTableLabels(); });
    }

    if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', boot);
    else boot();
})();
