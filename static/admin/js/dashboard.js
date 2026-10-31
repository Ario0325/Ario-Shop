/* ==========================================================================
   Ario Shop — dashboard
   Dependency-free SVG charts (CSP-friendly: no CDN), Persian formatting,
   range switching (7/30/90) and theme-aware re-rendering.
   ========================================================================== */
(function () {
    'use strict';

    var root = document.documentElement;
    var dash = document.getElementById('dash');
    if (!dash) return;

    var STATS_URL = '/admin/core/dashboard-stats/';
    var STATUS_LABELS = {
        pending: 'در انتظار پرداخت',
        paid: 'پرداخت شده',
        processing: 'در حال پردازش',
        shipped: 'ارسال شده',
        delivered: 'تحویل شده',
        cancelled: 'لغو شده'
    };

    var salesEl = document.getElementById('salesChart');
    var statusEl = document.getElementById('statusChart');
    var topBody = document.getElementById('topProductsBody');
    var totalChip = document.getElementById('sales-total');

    var days = (function () {
        var active = document.querySelector('.dash-range__btn.is-active');
        return active ? parseInt(active.getAttribute('data-days'), 10) || 30 : 30;
    })();
    var state = null;

    /* ── formatting ────────────────────────────────────────────────────────── */
    var nf = new Intl.NumberFormat('fa-IR', { maximumFractionDigits: 0 });
    var nf1 = new Intl.NumberFormat('fa-IR', { maximumFractionDigits: 1 });
    var df = new Intl.DateTimeFormat('fa-IR', { month: 'short', day: 'numeric' });

    function fa(n) { return nf.format(Number(n) || 0); }
    function fa1(n) { return nf1.format(Number(n) || 0); }

    function compact(n) {
        n = Number(n) || 0;
        if (n >= 1e9) return fa1(n / 1e9) + ' میلیارد';
        if (n >= 1e6) return fa1(n / 1e6) + ' میلیون';
        if (n >= 1e3) return fa1(n / 1e3) + ' هزار';
        return fa(n);
    }

    function money(n) { return compact(n) + ' تومان'; }

    function jalaliShort(iso) {
        var date = new Date(iso + 'T00:00:00');
        return isNaN(date) ? iso : df.format(date);
    }

    function cssVar(name, fallback) {
        var value = getComputedStyle(root).getPropertyValue(name).trim();
        return value || fallback;
    }

    function palette() {
        return [
            cssVar('--chart-1', '#B07A2F'),
            cssVar('--chart-2', '#0D5F58'),
            cssVar('--chart-3', '#2E5A87'),
            cssVar('--chart-4', '#5A6635'),
            cssVar('--chart-5', '#9C5E08'),
            cssVar('--chart-6', '#B0462E')
        ];
    }

    function svgEl(name, attrs) {
        var el = document.createElementNS('http://www.w3.org/2000/svg', name);
        Object.keys(attrs || {}).forEach(function (key) { el.setAttribute(key, attrs[key]); });
        return el;
    }

    /* ── KPI row ───────────────────────────────────────────────────────────── */
    function setText(id, value) {
        var el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    function setValue(id, value, unit) {
        var el = document.getElementById(id);
        if (!el) return;
        el.textContent = value;
        if (unit) {
            var small = document.createElement('small');
            small.textContent = ' ' + unit;
            el.appendChild(small);
        }
    }

    function setDelta(id, value) {
        var el = document.getElementById(id);
        if (!el) return;
        var v = Number(value) || 0;
        el.textContent = fa(Math.abs(v)) + '٪';
        el.className = 'kpi__delta ' + (v > 0 ? 'kpi__delta--up' : v < 0 ? 'kpi__delta--down' : 'kpi__delta--flat');
    }

    function renderKpi(kpi) {
        if (!kpi) return;
        setValue('kpi-revenue', compact(kpi.revenue), 'تومان');
        setValue('kpi-orders', fa(kpi.orders), 'سفارش');
        setValue('kpi-aov', compact(kpi.aov), 'تومان');
        setValue('kpi-customers', fa(kpi.new_customers), 'نفر');
        setDelta('kpi-revenue-delta', kpi.revenue_delta);
        setDelta('kpi-orders-delta', kpi.orders_delta);
        setDelta('kpi-aov-delta', kpi.aov_delta);
        setDelta('kpi-customers-delta', kpi.new_customers_delta);

        Array.prototype.forEach.call(document.querySelectorAll('[data-period-label]'), function (el) {
            el.textContent = 'در ' + fa(days) + ' روز اخیر';
        });
    }

    /* ── sales area chart ──────────────────────────────────────────────────── */
    function renderSales(series) {
        if (!salesEl) return;
        salesEl.innerHTML = '';

        var points = (series || []).map(function (row) {
            return { date: row.date, total: Number(row.total) || 0, count: row.count || 0 };
        });

        if (!points.length) {
            salesEl.appendChild(emptyState('i-trend', 'داده‌ای برای این بازه ثبت نشده است'));
            if (totalChip) totalChip.textContent = '—';
            return;
        }

        var W = 640;
        var H = 232;
        var padT = 12;
        var padB = 26;
        var padL = 14;
        var padR = 52;
        var plotW = W - padL - padR;
        var plotH = H - padT - padB;

        var max = Math.max.apply(null, points.map(function (p) { return p.total; }));
        if (!max) max = 1;

        var colors = palette();
        var line = colors[0];
        var gridColor = cssVar('--line', '#E7DDCE');
        var faint = cssVar('--faint', '#948779');

        var svg = svgEl('svg', {
            viewBox: '0 0 ' + W + ' ' + H,
            preserveAspectRatio: 'none',
            role: 'img',
            'aria-label': 'نمودار فروش',
            style: 'height:232px'
        });
        svg.classList.add('chart-svg');

        var defs = svgEl('defs', {});
        var grad = svgEl('linearGradient', { id: 'adm-sales-grad', x1: '0', y1: '0', x2: '0', y2: '1' });
        var stopA = svgEl('stop', { offset: '0%', 'stop-color': line, 'stop-opacity': '.28' });
        var stopB = svgEl('stop', { offset: '100%', 'stop-color': line, 'stop-opacity': '0' });
        grad.appendChild(stopA);
        grad.appendChild(stopB);
        defs.appendChild(grad);
        svg.appendChild(defs);

        // grid + y labels (three lines)
        [0, 0.5, 1].forEach(function (ratio) {
            var y = padT + plotH * ratio;
            svg.appendChild(svgEl('line', {
                x1: padL, y1: y, x2: W - padR + 4, y2: y,
                stroke: gridColor, 'stroke-width': '.7', 'stroke-dasharray': ratio === 1 ? '0' : '3 5'
            }));
            var label = svgEl('text', {
                x: W - padR + 10, y: y + 3.5,
                'font-size': '9.5', fill: faint, 'text-anchor': 'start'
            });
            label.textContent = compact(max * (1 - ratio));
            svg.appendChild(label);
        });

        var step = points.length > 1 ? plotW / (points.length - 1) : plotW;
        var coords = points.map(function (point, i) {
            return {
                x: padL + step * i,
                y: padT + plotH - (point.total / max) * plotH,
                item: point
            };
        });

        function smoothPath(list) {
            if (!list.length) return '';
            var d = 'M' + list[0].x.toFixed(2) + ',' + list[0].y.toFixed(2);
            for (var i = 1; i < list.length; i += 1) {
                var prev = list[i - 1];
                var cur = list[i];
                var mx = ((prev.x + cur.x) / 2).toFixed(2);
                d += ' C' + mx + ',' + prev.y.toFixed(2) + ' ' + mx + ',' + cur.y.toFixed(2) +
                     ' ' + cur.x.toFixed(2) + ',' + cur.y.toFixed(2);
            }
            return d;
        }

        var baseY = padT + plotH;
        var dLine = smoothPath(coords);
        var dArea = dLine + ' L' + coords[coords.length - 1].x.toFixed(2) + ',' + baseY +
                    ' L' + coords[0].x.toFixed(2) + ',' + baseY + ' Z';

        svg.appendChild(svgEl('path', { d: dArea, fill: 'url(#adm-sales-grad)', stroke: 'none' }));
        svg.appendChild(svgEl('path', {
            d: dLine, fill: 'none', stroke: line, 'stroke-width': '2.2',
            'stroke-linecap': 'round', 'stroke-linejoin': 'round'
        }));

        var showDots = points.length <= 31;
        coords.forEach(function (point) {
            var group = svgEl('g', {});
            if (showDots) {
                group.appendChild(svgEl('circle', {
                    cx: point.x, cy: point.y, r: '2.6', fill: cssVar('--surface', '#FFFDF9'),
                    stroke: line, 'stroke-width': '1.6'
                }));
            }
            var hit = svgEl('circle', {
                cx: point.x, cy: point.y, r: '9', fill: 'transparent', style: 'cursor:default'
            });
            var title = svgEl('title', {});
            title.textContent = jalaliShort(point.item.date) + ' — ' + money(point.item.total);
            hit.appendChild(title);
            group.appendChild(hit);
            svg.appendChild(group);
        });

        // x labels: five evenly spaced ticks
        var tickCount = Math.min(5, points.length);
        for (var t = 0; t < tickCount; t += 1) {
            var index = tickCount === 1 ? 0 : Math.round((points.length - 1) / (tickCount - 1) * t);
            var cx = padL + step * index;
            var anchor = t === 0 ? 'start' : t === tickCount - 1 ? 'end' : 'middle';
            var label = svgEl('text', {
                x: cx, y: H - 7, 'font-size': '9.5', fill: faint, 'text-anchor': anchor
            });
            label.textContent = jalaliShort(points[index].date);
            svg.appendChild(label);
        }

        salesEl.appendChild(svg);

        var total = points.reduce(function (sum, p) { return sum + p.total; }, 0);
        if (totalChip) totalChip.textContent = money(total);
        salesEl.setAttribute('aria-label', 'مجموع فروش ' + fa(days) + ' روز اخیر: ' + money(total));
    }

    /* ── order status donut ────────────────────────────────────────────────── */
    function renderStatuses(statuses) {
        if (!statusEl) return;
        statusEl.innerHTML = '';

        var rows = (statuses || []).filter(function (row) { return Number(row.count) > 0; });
        var total = rows.reduce(function (sum, row) { return sum + Number(row.count); }, 0);

        if (!total) {
            statusEl.appendChild(emptyState('i-receipt', 'هنوز سفارشی ثبت نشده است'));
            return;
        }

        var colors = palette();
        var size = 148;
        var radius = 54;
        var stroke = 15;
        var circumference = 2 * Math.PI * radius;
        var svg = svgEl('svg', {
            viewBox: '0 0 140 140',
            role: 'img',
            'aria-label': 'ترکیب وضعیت سفارش‌ها',
            style: 'width:148px;height:148px'
        });

        svg.appendChild(svgEl('circle', {
            cx: '70', cy: '70', r: String(radius), fill: 'none',
            stroke: cssVar('--surface-3', '#F3EBDF'), 'stroke-width': String(stroke)
        }));

        var offset = 0;
        var legend = document.createElement('div');
        legend.className = 'donut-legend';

        rows.forEach(function (row, i) {
            var color = colors[i % colors.length];
            var length = (Number(row.count) / total) * circumference;
            svg.appendChild(svgEl('circle', {
                cx: '70', cy: '70', r: String(radius), fill: 'none',
                stroke: color, 'stroke-width': String(stroke),
                'stroke-dasharray': length.toFixed(2) + ' ' + (circumference - length).toFixed(2),
                'stroke-dashoffset': (-offset).toFixed(2),
                transform: 'rotate(-90 70 70)',
                'stroke-linecap': 'butt'
            }));
            offset += length;

            var item = document.createElement('div');
            item.className = 'donut-legend__row';
            var swatch = document.createElement('i');
            swatch.style.background = color;
            var name = document.createElement('span');
            name.textContent = STATUS_LABELS[row.status] || row.status;
            var count = document.createElement('b');
            count.textContent = fa(row.count);
            item.appendChild(swatch);
            item.appendChild(name);
            item.appendChild(count);
            legend.appendChild(item);
        });

        var center = svgEl('text', {
            x: '70', y: '68', 'text-anchor': 'middle',
            'font-size': '17', 'font-weight': '700', fill: cssVar('--ink', '#1B1611')
        });
        center.textContent = fa(total);
        var caption = svgEl('text', {
            x: '70', y: '84', 'text-anchor': 'middle',
            'font-size': '8.5', fill: cssVar('--muted', '#6E6154')
        });
        caption.textContent = 'سفارش';
        svg.appendChild(center);
        svg.appendChild(caption);

        statusEl.appendChild(svg);
        statusEl.appendChild(legend);
    }

    /* ── best sellers ──────────────────────────────────────────────────────── */
    function renderTopProducts(products) {
        if (!topBody) return;
        topBody.innerHTML = '';

        if (!products || !products.length) {
            var row = document.createElement('tr');
            var cell = document.createElement('td');
            cell.colSpan = 3;
            cell.className = 'dash-empty';
            cell.textContent = 'به‌اندازه کافی فروش ثبت نشده است';
            row.appendChild(cell);
            topBody.appendChild(row);
            return;
        }

        products.forEach(function (product) {
            var row = document.createElement('tr');
            var name = document.createElement('td');
            name.textContent = product.name;
            var sold = document.createElement('td');
            sold.className = 'num';
            sold.textContent = fa(product.sold);
            var revenue = document.createElement('td');
            revenue.className = 'money';
            revenue.textContent = money(product.revenue);
            row.appendChild(name);
            row.appendChild(sold);
            row.appendChild(revenue);
            topBody.appendChild(row);
        });
    }

    /* ── helpers ───────────────────────────────────────────────────────────── */
    function emptyState(icon, message) {
        var box = document.createElement('div');
        box.className = 'dash-empty';
        box.innerHTML = '<svg aria-hidden="true"><use href="#' + icon + '"/></svg>';
        var text = document.createElement('span');
        text.textContent = message;
        box.appendChild(text);
        return box;
    }

    function setLoading(loading) {
        [salesEl, statusEl].forEach(function (el) {
            if (el) el.classList.toggle('is-loading', loading);
        });
    }

    function load() {
        setLoading(true);
        fetch(STATS_URL + '?days=' + days, { headers: { Accept: 'application/json' } })
            .then(function (response) {
                if (!response.ok) throw new Error('HTTP ' + response.status);
                return response.json();
            })
            .then(function (data) {
                state = data;
                renderKpi(data.kpi);
                renderSales(data.sales);
                renderStatuses(data.statuses);
                renderTopProducts(data.top_products);
                setLoading(false);
            })
            .catch(function () {
                setLoading(false);
                if (salesEl) {
                    salesEl.innerHTML = '';
                    salesEl.appendChild(emptyState('i-alert', 'دریافت آمار ممکن نشد. صفحه را بازخوانی کنید.'));
                }
            });
    }

    /* ── interactions ──────────────────────────────────────────────────────── */
    var range = document.getElementById('dash-range');
    if (range) {
        range.addEventListener('click', function (event) {
            var button = event.target.closest('.dash-range__btn');
            if (!button) return;
            var next = parseInt(button.getAttribute('data-days'), 10);
            if (!next || next === days) return;
            days = next;
            Array.prototype.forEach.call(range.querySelectorAll('.dash-range__btn'), function (btn) {
                var on = btn === button;
                btn.classList.toggle('is-active', on);
                btn.setAttribute('aria-pressed', on ? 'true' : 'false');
            });
            load();
        });
        Array.prototype.forEach.call(range.querySelectorAll('.dash-range__btn'), function (btn) {
            btn.setAttribute('aria-pressed', btn.classList.contains('is-active') ? 'true' : 'false');
        });
    }

    document.addEventListener('adm:themechange', function () {
        palette();
        if (!state) return;
        renderSales(state.sales);
        renderStatuses(state.statuses);
    });

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', load);
    else load();
})();
