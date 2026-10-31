/**
 * admin_animations.js
 * انیمیشن‌های پنل مدیریت آریو شاپ
 * v2.0 — Modern Admin Animations
 */
(function () {
    'use strict';

    /* ── ابزارها ─────────────────────────────────────────────────────────── */

    /**
     * اجرای تابع پس از بارگذاری DOM
     */
    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }

    /**
     * اضافه کردن استایل به head
     */
    function injectStyle(css) {
        var style = document.createElement('style');
        style.textContent = css;
        document.head.appendChild(style);
    }

    /* ── انیمیشن ورود عناصر (Intersection Observer) ─────────────────────── */

    function initEntranceAnimations() {
        if (!window.IntersectionObserver) return;

        var targets = document.querySelectorAll(
            '.module, .change-form fieldset, .inline-group, #result_list, .messagelist li'
        );

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry, i) {
                if (entry.isIntersecting) {
                    var el = entry.target;
                    var delay = (i * 40) + 'ms';
                    el.style.animationDelay = delay;
                    el.classList.add('ap-animate-in');
                    observer.unobserve(el);
                }
            });
        }, { threshold: 0.05, rootMargin: '0px 0px -30px 0px' });

        targets.forEach(function (el) {
            el.style.opacity = '0';
            el.style.transform = 'translateY(16px)';
            el.style.transform += ' scale(0.98)';
            observer.observe(el);
        });

        injectStyle(
            '.ap-animate-in {' +
            '  animation: apFadeInUp 0.38s cubic-bezier(0.4, 0, 0.2, 1) both !important;' +
            '}' +
            '@keyframes apFadeInUp {' +
            '  from { opacity: 0; transform: translateY(16px) scale(0.98); }' +
            '  to   { opacity: 1; transform: translateY(0) scale(1); }' +
            '}'
        );
    }

    /* ── هایلایت ردیف‌های جدول ───────────────────────────────────────────── */

    function initTableRowHighlight() {
        var rows = document.querySelectorAll('#result_list tbody tr');
        rows.forEach(function (row, i) {
            row.style.animationDelay = (i * 25) + 'ms';
            row.classList.add('ap-row-in');
        });

        injectStyle(
            '.ap-row-in {' +
            '  animation: apRowSlide 0.3s ease both;' +
            '}' +
            '@keyframes apRowSlide {' +
            '  from { opacity: 0; transform: translateY(6px); }' +
            '  to   { opacity: 1; transform: translateY(0); }' +
            '}'
        );
    }

    /* ── افکت ripple روی دکمه‌ها ─────────────────────────────────────────── */

    function initRippleEffect() {
        injectStyle(
            '.ap-ripple-btn { position: relative; overflow: hidden; }' +
            '.ap-ripple-btn::after {' +
            '  content: "";' +
            '  position: absolute;' +
            '  border-radius: 50%;' +
            '  background: rgba(255,255,255,0.25);' +
            '  transform: scale(0);' +
            '  animation: apRipple 0.5s linear;' +
            '  pointer-events: none;' +
            '}' +
            '@keyframes apRipple {' +
            '  to { transform: scale(4); opacity: 0; }' +
            '}'
        );

        document.addEventListener('click', function (e) {
            var btn = e.target.closest(
                'input[type="submit"], input[type="button"], .button, .object-tools a, .submit-row input'
            );
            if (!btn) return;

            btn.classList.remove('ap-ripple-btn');
            void btn.offsetWidth; // reflow
            btn.classList.add('ap-ripple-btn');

            var rect = btn.getBoundingClientRect();
            var size = Math.max(rect.width, rect.height);
            btn.style.setProperty('--ripple-x', (e.clientX - rect.left - size / 2) + 'px');
            btn.style.setProperty('--ripple-y', (e.clientY - rect.top - size / 2) + 'px');
        });
    }

    /* ── انیمیشن focus روی فیلدها ────────────────────────────────────────── */

    function initFieldFocusGlow() {
        var fields = document.querySelectorAll(
            'input[type="text"], input[type="password"], input[type="email"],' +
            'input[type="number"], input[type="url"], input[type="search"],' +
            'input[type="date"], input[type="datetime-local"], select, textarea'
        );

        fields.forEach(function (field) {
            field.addEventListener('focus', function () {
                var row = field.closest('.form-row');
                if (row) {
                    row.style.transition = 'background 0.2s ease, box-shadow 0.2s ease';
                    row.style.background = 'rgba(139, 92, 246, 0.04)';
                    row.style.boxShadow = 'inset 0 0 0 1px rgba(139, 92, 246, 0.2)';
                }
            });

            field.addEventListener('blur', function () {
                var row = field.closest('.form-row');
                if (row) {
                    row.style.background = '';
                    row.style.boxShadow = '';
                }
            });
        });
    }

    /* ── انیمیشن دکمه‌های submit ─────────────────────────────────────────── */

    function initSubmitButtonAnimation() {
        injectStyle(
            '.ap-submit-btn-animate {' +
            '  position: relative;' +
            '  overflow: hidden;' +
            '  transition: all 0.3s ease !important;' +
            '}' +
            '.ap-submit-btn-animate::before {' +
            '  content: "";' +
            '  position: absolute;' +
            '  top: 0;' +
            '  left: -100%;' +
            '  width: 100%;' +
            '  height: 100%;' +
            '  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);' +
            '  transition: left 0.5s ease;' +
            '}' +
            '.ap-submit-btn-animate:hover::before {' +
            '  left: 100%;' +
            '}'
        );

        document.addEventListener('mouseover', function (e) {
            var btn = e.target.closest('.submit-row input[type="submit"]');
            if (btn) {
                btn.classList.add('ap-submit-btn-animate');
            }
        });
    }

    /* ── انیمیشن pulse روی پیام‌های موفقیت ───────────────────────────────── */

    function initSuccessMessagePulse() {
        injectStyle(
            '.ap-success-pulse {' +
            '  animation: apSuccessPulse 2s ease-in-out infinite;' +
            '}' +
            '@keyframes apSuccessPulse {' +
            '  0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }' +
            '  50% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }' +
            '}'
        );

        var successMsgs = document.querySelectorAll('.messagelist li.success');
        successMsgs.forEach(function (msg) {
            msg.classList.add('ap-success-pulse');
        });
    }

    /* ── انیمیشن hover روی ردیف‌های جدول ───────────────────────────────── */

    function initTableRowHoverEffect() {
        injectStyle(
            '.ap-table-row-hover {' +
            '  position: relative;' +
            '  overflow: hidden;' +
            '}' +
            '.ap-table-row-hover::after {' +
            '  content: "";' +
            '  position: absolute;' +
            '  top: 0;' +
            '  left: 0;' +
            '  width: 3px;' +
            '  height: 100%;' +
            '  background: linear-gradient(180deg, var(--ap-primary), var(--ap-accent));' +
            '  transform: scaleY(0);' +
            '  transform-origin: bottom;' +
            '  transition: transform 0.2s ease;' +
            '}' +
            '.ap-table-row-hover:hover::after {' +
            '  transform: scaleY(1);' +
            '}'
        );

        var rows = document.querySelectorAll('#result_list tbody tr');
        rows.forEach(function (row) {
            row.classList.add('ap-table-row-hover');
        });
    }

    /* ── شمارنده آمار (counter animation) ────────────────────────────────── */

    function animateCounters() {
        var statsDiv = document.querySelector('.field-usage_stats_display .readonly div');
        if (!statsDiv) return;

        var strongs = statsDiv.querySelectorAll('strong');
        strongs.forEach(function (el) {
            var text = el.textContent.trim();
            // فقط اعداد خالص را انیمیت کن
            var num = parseFloat(text.replace(/,/g, ''));
            if (isNaN(num) || text.includes('»') || text.includes('«')) return;

            var duration = 800;
            var start = null;
            var startVal = 0;

            function step(timestamp) {
                if (!start) start = timestamp;
                var progress = Math.min((timestamp - start) / duration, 1);
                var eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
                var current = Math.floor(startVal + (num - startVal) * eased);
                el.textContent = current.toLocaleString('fa-IR');
                if (progress < 1) {
                    requestAnimationFrame(step);
                } else {
                    el.textContent = num.toLocaleString('fa-IR');
                }
            }

            requestAnimationFrame(step);
        });
    }

    /* ── نوار پیشرفت برای usage_limit ────────────────────────────────────── */

    function initUsageProgressBar() {
        // اگر در صفحه تغییر DiscountCode هستیم
        var usedCountField = document.querySelector('.field-used_count .readonly');
        if (!usedCountField) return;

        var usedCount = parseInt(usedCountField.textContent.trim()) || 0;

        // پیدا کردن usage_limit_total
        var limitField = document.querySelector('#id_usage_limit_total');
        if (!limitField || !limitField.value) return;

        var limit = parseInt(limitField.value) || 0;
        if (limit <= 0) return;

        var percent = Math.min((usedCount / limit) * 100, 100);
        var color = percent < 50 ? '#10b981' : percent < 80 ? '#f59e0b' : '#ef4444';

        var bar = document.createElement('div');
        bar.style.cssText = [
            'margin-top: 8px',
            'height: 6px',
            'background: rgba(255,255,255,0.08)',
            'border-radius: 3px',
            'overflow: hidden',
        ].join(';');

        var fill = document.createElement('div');
        fill.style.cssText = [
            'height: 100%',
            'width: 0',
            'background: ' + color,
            'border-radius: 3px',
            'transition: width 1s cubic-bezier(0.4, 0, 0.2, 1)',
        ].join(';');

        bar.appendChild(fill);
        usedCountField.parentNode.appendChild(bar);

        // تأخیر برای انیمیشن
        setTimeout(function () {
            fill.style.width = percent + '%';
        }, 300);
    }

    /* ── tooltip برای badge‌ها ────────────────────────────────────────────── */

    function initBadgeTooltips() {
        injectStyle(
            '.ap-tooltip-wrap { position: relative; display: inline-block; }' +
            '.ap-tooltip {' +
            '  position: absolute;' +
            '  bottom: calc(100% + 6px);' +
            '  right: 50%;' +
            '  transform: translateX(50%);' +
            '  background: rgba(15, 23, 42, 0.95);' +
            '  color: #e2e8f0;' +
            '  font-size: 11px;' +
            '  padding: 4px 10px;' +
            '  border-radius: 6px;' +
            '  white-space: nowrap;' +
            '  pointer-events: none;' +
            '  opacity: 0;' +
            '  transition: opacity 0.18s ease;' +
            '  z-index: 9999;' +
            '  border: 1px solid rgba(255,255,255,0.08);' +
            '}' +
            '.ap-tooltip-wrap:hover .ap-tooltip { opacity: 1; }'
        );
    }

    /* ── انیمیشن هدر sticky ───────────────────────────────────────────────── */

    function initStickyHeaderShadow() {
        var header = document.getElementById('header');
        if (!header) return;

        window.addEventListener('scroll', function () {
            if (window.scrollY > 10) {
                header.style.boxShadow = '0 4px 30px rgba(0,0,0,0.8), 0 0 0 1px rgba(139,92,246,0.2), 0 0 30px rgba(139,92,246,0.1)';
            } else {
                header.style.boxShadow = '0 2px 20px rgba(0,0,0,0.6), 0 0 0 1px rgba(139,92,246,0.15)';
            }
        }, { passive: true });
    }

    /* ── اجرای اصلی ──────────────────────────────────────────────────────── */

    ready(function () {
        initEntranceAnimations();
        initTableRowHighlight();
        initRippleEffect();
        initFieldFocusGlow();
        initBadgeTooltips();
        initStickyHeaderShadow();
        initSubmitButtonAnimation();
        initSuccessMessagePulse();
        initTableRowHoverEffect();

        // شمارنده آمار با تأخیر کمی
        setTimeout(animateCounters, 400);
        setTimeout(initUsageProgressBar, 200);
    });

})();
