/**
 * discount_code_admin.js
 * نمایش/پنهان کردن فیلد «محصول مرتبط» بر اساس انتخاب «محدوده تخفیف»
 * با انیمیشن smooth
 */
(function () {
    'use strict';

    /**
     * نمایش یا پنهان کردن فیلد محصول با انیمیشن
     */
    function toggleProductField(animate) {
        var scopeSelect = document.getElementById('id_scope');
        if (!scopeSelect) return;

        var productRow = document.querySelector('.field-product');
        if (!productRow) return;

        var isProduct = scopeSelect.value === 'product';

        if (isProduct) {
            // نمایش با انیمیشن
            productRow.style.display = '';
            productRow.style.overflow = 'hidden';

            if (animate) {
                productRow.style.maxHeight = '0';
                productRow.style.opacity = '0';
                productRow.style.transition = 'max-height 0.35s cubic-bezier(0.4,0,0.2,1), opacity 0.3s ease';

                requestAnimationFrame(function () {
                    requestAnimationFrame(function () {
                        productRow.style.maxHeight = '200px';
                        productRow.style.opacity = '1';
                    });
                });
            } else {
                productRow.style.maxHeight = '';
                productRow.style.opacity = '';
                productRow.style.transition = '';
            }
        } else {
            // پنهان کردن با انیمیشن
            if (animate) {
                productRow.style.overflow = 'hidden';
                productRow.style.maxHeight = productRow.scrollHeight + 'px';
                productRow.style.opacity = '1';
                productRow.style.transition = 'max-height 0.3s cubic-bezier(0.4,0,0.2,1), opacity 0.25s ease';

                requestAnimationFrame(function () {
                    requestAnimationFrame(function () {
                        productRow.style.maxHeight = '0';
                        productRow.style.opacity = '0';
                    });
                });

                setTimeout(function () {
                    productRow.style.display = 'none';
                    productRow.style.maxHeight = '';
                    productRow.style.opacity = '';
                    productRow.style.transition = '';
                    productRow.style.overflow = '';
                }, 320);
            } else {
                productRow.style.display = 'none';
            }
        }
    }

    /**
     * اضافه کردن badge توضیحی به کنار scope select
     */
    function addScopeBadge() {
        var scopeSelect = document.getElementById('id_scope');
        if (!scopeSelect) return;

        var badge = document.createElement('span');
        badge.id = 'scope-badge';
        badge.style.cssText = [
            'display: inline-block',
            'margin-right: 10px',
            'padding: 3px 10px',
            'border-radius: 999px',
            'font-size: 12px',
            'font-weight: 600',
            'transition: all 0.25s ease',
            'vertical-align: middle',
        ].join(';');

        scopeSelect.parentNode.insertBefore(badge, scopeSelect.nextSibling);
        updateScopeBadge(scopeSelect.value, badge);
    }

    function updateScopeBadge(value, badge) {
        if (!badge) badge = document.getElementById('scope-badge');
        if (!badge) return;

        if (value === 'product') {
            badge.textContent = '🎯 محصول خاص';
            badge.style.background = 'rgba(167, 139, 250, 0.15)';
            badge.style.color = '#c4b5fd';
            badge.style.border = '1px solid rgba(167, 139, 250, 0.3)';
        } else {
            badge.textContent = '🛒 کل سبد خرید';
            badge.style.background = 'rgba(251, 191, 36, 0.15)';
            badge.style.color = '#fde68a';
            badge.style.border = '1px solid rgba(251, 191, 36, 0.3)';
        }
    }

    /**
     * اضافه کردن badge به کنار discount_type select
     */
    function addTypeBadge() {
        var typeSelect = document.getElementById('id_discount_type');
        if (!typeSelect) return;

        var badge = document.createElement('span');
        badge.id = 'type-badge';
        badge.style.cssText = [
            'display: inline-block',
            'margin-right: 10px',
            'padding: 3px 10px',
            'border-radius: 999px',
            'font-size: 12px',
            'font-weight: 600',
            'transition: all 0.25s ease',
            'vertical-align: middle',
        ].join(';');

        typeSelect.parentNode.insertBefore(badge, typeSelect.nextSibling);
        updateTypeBadge(typeSelect.value, badge);

        typeSelect.addEventListener('change', function () {
            updateTypeBadge(this.value, badge);
        });
    }

    function updateTypeBadge(value, badge) {
        if (!badge) badge = document.getElementById('type-badge');
        if (!badge) return;

        if (value === 'percent') {
            badge.textContent = '📊 درصدی';
            badge.style.background = 'rgba(34, 211, 238, 0.15)';
            badge.style.color = '#67e8f9';
            badge.style.border = '1px solid rgba(34, 211, 238, 0.3)';
        } else {
            badge.textContent = '💰 مبلغ ثابت';
            badge.style.background = 'rgba(52, 211, 153, 0.15)';
            badge.style.color = '#6ee7b7';
            badge.style.border = '1px solid rgba(52, 211, 153, 0.3)';
        }
    }

    /**
     * نمایش/پنهان کردن فیلد max_discount_amount بر اساس نوع تخفیف
     */
    function toggleMaxDiscountField(animate) {
        var typeSelect = document.getElementById('id_discount_type');
        if (!typeSelect) return;

        var maxRow = document.querySelector('.field-max_discount_amount');
        if (!maxRow) return;

        var isPercent = typeSelect.value === 'percent';

        if (isPercent) {
            maxRow.style.display = '';
            if (animate) {
                maxRow.style.opacity = '0';
                maxRow.style.transition = 'opacity 0.3s ease';
                requestAnimationFrame(function () {
                    requestAnimationFrame(function () {
                        maxRow.style.opacity = '1';
                    });
                });
            }
        } else {
            if (animate) {
                maxRow.style.transition = 'opacity 0.25s ease';
                maxRow.style.opacity = '0';
                setTimeout(function () {
                    maxRow.style.display = 'none';
                    maxRow.style.opacity = '';
                    maxRow.style.transition = '';
                }, 260);
            } else {
                maxRow.style.display = 'none';
            }
        }
    }

    /* ── اجرای اصلی ──────────────────────────────────────────────────────── */

    document.addEventListener('DOMContentLoaded', function () {
        var scopeSelect = document.getElementById('id_scope');
        var typeSelect = document.getElementById('id_discount_type');

        if (scopeSelect) {
            toggleProductField(false);
            addScopeBadge();

            scopeSelect.addEventListener('change', function () {
                toggleProductField(true);
                updateScopeBadge(this.value);
            });
        }

        if (typeSelect) {
            toggleMaxDiscountField(false);
            addTypeBadge();

            typeSelect.addEventListener('change', function () {
                toggleMaxDiscountField(true);
                updateTypeBadge(this.value);
            });
        }
    });

})();
