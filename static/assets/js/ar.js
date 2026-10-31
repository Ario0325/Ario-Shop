/*!
 * Ario Shop — storefront interaction layer
 * Vanilla JS, no dependencies. Every module is progressive enhancement:
 * without it the pages still render, navigate, and submit.
 */
(function () {
    "use strict";

    var doc = document;
    var root = doc.documentElement;
    var FA = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];
    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    var $ = function (sel, ctx) { return (ctx || doc).querySelector(sel); };
    var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || doc).querySelectorAll(sel)); };
    var on = function (el, ev, fn, opts) { if (el) el.addEventListener(ev, fn, opts || false); };
    var clamp = function (n, a, b) { return Math.min(b, Math.max(a, n)); };
    var toFa = function (v) { return String(v).replace(/\d/g, function (d) { return FA[+d]; }); };
    var esc = function (s) {
        return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
        });
    };
    var debounce = function (fn, wait) {
        var t;
        return function () {
            var args = arguments, ctx = this;
            clearTimeout(t);
            t = setTimeout(function () { fn.apply(ctx, args); }, wait);
        };
    };

    var store = {
        get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
        set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
        del: function (k) { try { localStorage.removeItem(k); } catch (e) {} },
        sget: function (k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } },
        sset: function (k, v) { try { sessionStorage.setItem(k, v); } catch (e) {} }
    };

    /* ----------------------------------------------------------------------
       Preloader
       ---------------------------------------------------------------------- */
    function initPreloader() {
        var pre = doc.getElementById("ar-preloader");
        if (!pre) return;

        if (!root.classList.contains("is-preloading")) {
            pre.classList.add("is-done");
            root.classList.add("is-preloaded");
            return;
        }

        var fill = $("[data-preload-bar]", pre);
        var pct = $("[data-preload-pct]", pre);
        var value = 6;
        var finished = false;
        var started = performance.now();

        var paint = function () {
            if (fill) fill.style.transform = "scaleX(" + (value / 100) + ")";
            if (pct) pct.textContent = toFa(Math.round(value)) + "٪";
        };

        paint();

        var ticker = setInterval(function () {
            var target = clamp(((performance.now() - started) / 1400) * 82, 6, 82);
            if (target > value) { value = target; paint(); }
        }, 90);

        var finish = function () {
            if (finished) return;
            finished = true;
            clearInterval(ticker);
            value = 100;
            paint();
            setTimeout(function () {
                pre.classList.add("is-done");
                root.classList.remove("is-preloading");
                root.classList.add("is-preloaded");
                store.sset("ar-loaded", "1");
                setTimeout(function () {
                    if (pre.parentNode) pre.parentNode.removeChild(pre);
                }, 700);
            }, 280);
        };

        if (doc.readyState === "complete") setTimeout(finish, 480);
        else {
            on(window, "load", function () { setTimeout(finish, 320); });
            /* slow network bail-out: never trap the visitor behind the loader */
            setTimeout(finish, 4500);
        }
    }

    /* ----------------------------------------------------------------------
       Theme
       ---------------------------------------------------------------------- */
    function paintTheme(theme) {
        root.setAttribute("data-theme", theme);
        var meta = doc.querySelector('meta[name="theme-color"]');
        if (meta) meta.setAttribute("content", theme === "dark" ? "#150A10" : "#24101B");
        $$("[data-ar-theme-toggle]").forEach(function (btn) {
            var isDark = theme === "dark";
            btn.setAttribute("aria-pressed", isDark ? "true" : "false");
            btn.setAttribute("aria-label", isDark ? "فعال کردن حالت روشن" : "فعال کردن حالت تاریک");
            btn.setAttribute("title", isDark ? "حالت روشن" : "حالت تاریک");
        });
        var themeMeta = doc.querySelector('meta[name="color-scheme"]');
        if (themeMeta) themeMeta.setAttribute("content", theme === "dark" ? "dark" : "light");
    }

    function initTheme() {
        var saved = store.get("ar-theme");
        var theme = root.getAttribute("data-theme") || saved ||
            (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
        paintTheme(theme);

        $$("[data-ar-theme-toggle]").forEach(function (btn) {
            on(btn, "click", function () {
                var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
                paintTheme(next);
                store.set("ar-theme", next);
                toast("info", next === "dark" ? "حالت تاریک فعال شد" : "حالت روشن فعال شد", "", { duration: 2400 });
            });
        });

        var mq = window.matchMedia("(prefers-color-scheme: dark)");
        var follow = function (e) { if (!store.get("ar-theme")) paintTheme(e.matches ? "dark" : "light"); };
        if (mq.addEventListener) mq.addEventListener("change", follow);
    }

    /* ----------------------------------------------------------------------
       Scroll lock + focus-managed layers (drawers, search, modals)
       ---------------------------------------------------------------------- */
    var layers = [];
    var scrollLocked = false;
    var FOCUSABLE = "a[href], area[href], button:not([disabled]), input:not([disabled]):not([type=hidden]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])";

    function focusables(el) {
        return $$(FOCUSABLE, el).filter(function (n) {
            return n.offsetWidth > 0 || n.offsetHeight > 0 || n.getClientRects().length > 0;
        });
    }

    function lockScroll(lock) {
        if (lock === scrollLocked) return;
        scrollLocked = lock;
        if (lock) {
            var sw = window.innerWidth - root.clientWidth;
            doc.body.style.overflow = "hidden";
            if (sw > 0) doc.body.style.paddingInlineEnd = sw + "px";
        } else {
            doc.body.style.overflow = "";
            doc.body.style.paddingInlineEnd = "";
        }
    }

    function setPageInert(inert) {
        var page = doc.getElementById("ar-page");
        if (!page) return;
        if (inert) page.setAttribute("inert", "");
        else page.removeAttribute("inert");
    }

    function openLayer(el, trigger) {
        if (!el) return;
        var isModal = el.classList.contains("ar-modal");
        if (layers.length) closeLayer(layers[layers.length - 1].el, true);

        layers.push({ el: el, trigger: trigger || doc.activeElement, isModal: isModal });

        el.classList.add("is-open");
        el.setAttribute("aria-hidden", "false");
        if (trigger && trigger.hasAttribute("aria-expanded")) trigger.setAttribute("aria-expanded", "true");
        if (!isModal) {
            var ov = doc.getElementById("ar-overlay");
            if (ov) {
                ov.hidden = false;
                requestAnimationFrame(function () { ov.classList.add("is-open"); });
            }
        }

        setPageInert(true);
        lockScroll(true);

        var auto = el.querySelector("[data-ar-autofocus]") || focusables(el)[0];
        if (auto) setTimeout(function () {
            try { auto.focus({ preventScroll: true }); } catch (e) { auto.focus(); }
        }, 90);

        el.dispatchEvent(new CustomEvent("ar:open"));
    }

    function closeLayer(el, keepInert) {
        if (!el) return;
        var idx = -1;
        for (var i = 0; i < layers.length; i++) if (layers[i].el === el) idx = i;
        if (idx === -1) return;

        var entry = layers.splice(idx, 1)[0];
        el.classList.remove("is-open");
        el.setAttribute("aria-hidden", "true");
        if (entry.trigger && entry.trigger.hasAttribute("aria-expanded")) entry.trigger.setAttribute("aria-expanded", "false");

        if (!entry.isModal) {
            var stillOpen = layers.some(function (l) { return !l.isModal; });
            if (!stillOpen) {
                var ov = doc.getElementById("ar-overlay");
                if (ov) {
                    ov.classList.remove("is-open");
                    setTimeout(function () {
                        if (!ov.classList.contains("is-open")) ov.hidden = true;
                    }, 240);
                }
            }
        }

        if (!keepInert && !layers.length) {
            setPageInert(false);
            lockScroll(false);
        }

        if (entry.trigger && entry.trigger.focus) {
            try { entry.trigger.focus({ preventScroll: true }); } catch (e) {}
        }
        el.dispatchEvent(new CustomEvent("ar:close"));
    }

    function topLayer() { return layers[layers.length - 1]; }

    function initLayers() {
        doc.addEventListener("click", function (e) {
            var opener = e.target.closest("[data-ar-open]");
            if (opener) {
                e.preventDefault();
                openLayer(doc.getElementById(opener.getAttribute("data-ar-open")), opener);
                return;
            }

            var closer = e.target.closest("[data-ar-close]");
            if (closer) {
                e.preventDefault();
                var id = closer.getAttribute("data-ar-close");
                var target = id ? doc.getElementById(id) : closer.closest(".ar-drawer, .ar-searchpanel, .ar-modal");
                if (!target && topLayer()) target = topLayer().el;
                closeLayer(target);
                return;
            }

            var overlay = e.target.closest("#ar-overlay");
            if (overlay) {
                if (topLayer()) closeLayer(topLayer().el);
                return;
            }

            var modal = e.target.closest(".ar-modal");
            if (modal && e.target === modal) closeLayer(modal);
        });

        on(doc, "keydown", function (e) {
            if (e.key === "Escape") {
                if (layers.length) {
                    e.preventDefault();
                    closeLayer(topLayer().el);
                    return;
                }
                closeAllMega(true);
            }

            if (e.key === "Tab" && layers.length) {
                var el = topLayer().el;
                var items = focusables(el);
                if (!items.length) { e.preventDefault(); return; }
                var first = items[0];
                var last = items[items.length - 1];
                var current = doc.activeElement;
                if (e.shiftKey && (current === first || !el.contains(current))) {
                    e.preventDefault();
                    last.focus();
                } else if (!e.shiftKey && current === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
        });

        on(window, "pageshow", function (e) {
            if (!e.persisted) return;
            var pre = doc.getElementById("ar-preloader");
            if (pre) pre.classList.add("is-done");
            root.classList.remove("is-preloading");
            root.classList.add("is-preloaded");
            layers = [];
            setPageInert(false);
            lockScroll(false);
            $$("form[data-submitting]").forEach(function (form) { delete form.dataset.submitting; });
            $$(".is-loading").forEach(function (el) { el.classList.remove("is-loading"); });
        });
    }

    /* ----------------------------------------------------------------------
       Header: sticky bar with compact state + back to top
       ---------------------------------------------------------------------- */
    function initHeader() {
        var header = $(".ar-header");
        var compact = false;
        var ticking = false;
        var compactAfter = 44;

        var setCompact = function (value) {
            if (compact === value) return;
            compact = value;
            header.classList.toggle("is-compact", value);
            root.classList.toggle("is-hdr-compact", value);
        };

        if (header) {
            on(window, "scroll", function () {
                if (ticking) return;
                ticking = true;
                requestAnimationFrame(function () {
                    setCompact((window.scrollY || 0) > compactAfter);
                    ticking = false;
                });
            }, { passive: true });
            setCompact((window.scrollY || 0) > compactAfter);
        }

        var top = doc.getElementById("scroll-top");
        if (top) {
            var topTicking = false;
            on(window, "scroll", function () {
                if (topTicking) return;
                topTicking = true;
                requestAnimationFrame(function () {
                    top.classList.toggle("is-visible", window.scrollY > 760);
                    topTicking = false;
                });
            }, { passive: true });

            on(top, "click", function () {
                window.scrollTo({ top: 0, behavior: reduceMotion.matches ? "auto" : "smooth" });
            });

            var footer = doc.querySelector(".ar-footer");
            if (footer && "IntersectionObserver" in window) {
                new IntersectionObserver(function (entries) {
                    top.classList.toggle("is-footerview", entries[0].isIntersecting);
                }, { threshold: 0 }).observe(footer);
            }
        }
    }

    /* ----------------------------------------------------------------------
       Search shortcut (Ctrl/Cmd + K)
       ---------------------------------------------------------------------- */
    function initSearchShortcut() {
        var input = doc.getElementById("arOmniSearch");
        if (!input) return;

        on(doc, "keydown", function (e) {
            if (!(e.ctrlKey || e.metaKey) || String(e.key).toLowerCase() !== "k") return;
            e.preventDefault();

            var form = input.closest(".ar-omni");
            if (form && window.getComputedStyle(form).display !== "none") {
                input.focus();
                input.select();
                return;
            }
            openLayer(
                doc.getElementById("ar-search"),
                doc.querySelector('[data-ar-open="ar-search"]')
            );
        });
    }

    /* ----------------------------------------------------------------------
       Product shelves (native scroll-snap)
       ---------------------------------------------------------------------- */
    function initScroller(track, prev, next, step) {
        if (!track) return;
        var rtl = window.getComputedStyle(track).direction === "rtl";

        var move = function (dir) {
            track.scrollBy({ left: dir * (rtl ? -1 : 1) * step, behavior: reduceMotion.matches ? "auto" : "smooth" });
        };
        on(next, "click", function () { move(1); });
        on(prev, "click", function () { move(-1); });

        var update = function () {
            var max = Math.max(0, track.scrollWidth - track.clientWidth);
            var x = Math.abs(track.scrollLeft);
            if (prev) prev.disabled = x < 4;
            if (next) next.disabled = x > max - 4;
        };
        on(track, "scroll", debounce(update, 90), { passive: true });
        on(window, "resize", debounce(update, 150));
        update();
    }

    function initShelves() {
        $$("[data-ar-shelf]").forEach(function (track) {
            var rootEl = track.closest("[data-ar-shelf-root]") || track.parentNode;
            initScroller(
                track,
                $("[data-ar-shelf-prev]", rootEl),
                $("[data-ar-shelf-next]", rootEl),
                Math.max(240, Math.round(track.clientWidth * 0.7))
            );
        });
    }

    /* ----------------------------------------------------------------------
       Mega menu
       ---------------------------------------------------------------------- */
    function closeAllMega(focusTrigger) {
        $$(".ar-mega.is-open").forEach(function (mega) {
            mega.classList.remove("is-open");
            var btn = doc.querySelector('[data-ar-mega-toggle="' + mega.id + '"]');
            if (btn) {
                btn.setAttribute("aria-expanded", "false");
                if (focusTrigger) btn.focus();
            }
        });
    }

    function initMega() {
        $$("[data-ar-mega-toggle]").forEach(function (btn) {
            var mega = doc.getElementById(btn.getAttribute("data-ar-mega-toggle"));
            if (!mega) return;
            on(btn, "click", function (e) {
                e.preventDefault();
                var willOpen = !mega.classList.contains("is-open");
                closeAllMega();
                if (willOpen) {
                    mega.classList.add("is-open");
                    btn.setAttribute("aria-expanded", "true");
                }
            });
        });

        on(doc, "click", function (e) {
            if (!e.target.closest(".ar-mega") && !e.target.closest("[data-ar-mega-toggle]")) closeAllMega();
        });
    }

    /* ----------------------------------------------------------------------
       Mobile submenus
       ---------------------------------------------------------------------- */
    function initSubmenus() {
        $$("[data-ar-submenu-toggle]").forEach(function (btn) {
            var sub = doc.getElementById(btn.getAttribute("data-ar-submenu-toggle"));
            if (!sub) return;
            on(btn, "click", function (e) {
                e.preventDefault();
                var open = sub.hasAttribute("hidden");
                btn.setAttribute("aria-expanded", open ? "true" : "false");
                if (open) {
                    sub.removeAttribute("hidden");
                    void sub.offsetHeight;
                    sub.classList.add("is-open");
                } else {
                    sub.classList.remove("is-open");
                    setTimeout(function () {
                        if (!sub.classList.contains("is-open")) sub.setAttribute("hidden", "");
                    }, 240);
                }
            });
        });
    }

    /* ----------------------------------------------------------------------
       Tabs
       ---------------------------------------------------------------------- */
    function initTabs() {
        $$("[data-ar-tabs]").forEach(function (tabs) {
            var wrap = tabs.closest("[data-ar-tabwrap]") || tabs.parentNode;
            var buttons = $$("[data-ar-tab]", tabs);
            if (!buttons.length) return;

            var activate = function (name, focus) {
                buttons.forEach(function (btn) {
                    var selected = btn.getAttribute("data-ar-tab") === name;
                    btn.classList.toggle("is-active", selected);
                    btn.setAttribute("aria-selected", selected ? "true" : "false");
                    btn.tabIndex = selected ? 0 : -1;
                    if (selected && focus) btn.focus();
                });
                $$("[data-ar-panel]", wrap).forEach(function (panel) {
                    var selected = panel.getAttribute("data-ar-panel") === name;
                    panel.hidden = !selected;
                    panel.classList.toggle("is-active", selected);
                });
            };

            buttons.forEach(function (btn, i) {
                on(btn, "click", function (e) {
                    e.preventDefault();
                    activate(btn.getAttribute("data-ar-tab"));
                });
                on(btn, "keydown", function (e) {
                    var dir = e.key === "ArrowLeft" ? -1 : e.key === "ArrowRight" ? 1 : 0;
                    if (!dir) return;
                    e.preventDefault();
                    var nextBtn = buttons[(i + dir + buttons.length) % buttons.length];
                    activate(nextButtonName(nextBtn), true);
                });
            });

            function nextButtonName(b) { return b.getAttribute("data-ar-tab"); }

            var requested = parseInt(tabs.getAttribute("data-ar-tabs-active"), 10);
            var initial = (!isNaN(requested) && buttons[requested]) ||
                buttons.filter(function (b) { return b.classList.contains("is-active"); })[0] ||
                buttons[0];
            activate(initial.getAttribute("data-ar-tab"));

            $$("[data-ar-switch-tab]", tabs).forEach(function (link) {
                on(link, "click", function (e) {
                    e.preventDefault();
                    var target = buttons[parseInt(link.getAttribute("data-ar-switch-tab"), 10)];
                    if (!target) return;
                    activate(target.getAttribute("data-ar-tab"));
                    var panel = $("[data-ar-panel='" + target.getAttribute("data-ar-tab") + "']", wrap);
                    var first = panel && $("input:not([type=hidden]):not([disabled]), select, textarea", panel);
                    if (first) first.focus({ preventScroll: true });
                });
            });
        });

        $$("[data-ar-goto-tab]").forEach(function (link) {
            on(link, "click", function (e) {
                e.preventDefault();
                var wrapId = link.getAttribute("data-ar-tab-scroll");
                var wrap = wrapId ? doc.getElementById(wrapId) : link.closest("[data-ar-tabwrap]");
                if (!wrap) return;
                var name = link.getAttribute("data-ar-goto-tab");
                var targetBtn = null;
                $$("[data-ar-tab]", wrap).forEach(function (btn) {
                    if (btn.getAttribute("data-ar-tab") === name) targetBtn = btn;
                });
                if (targetBtn) targetBtn.click();
                wrap.scrollIntoView({
                    behavior: reduceMotion.matches ? "auto" : "smooth",
                    block: "start"
                });
            });
        });
    }

    /* ----------------------------------------------------------------------
       Product gallery (snap track + thumbs + dots + zoom dialog)
       ---------------------------------------------------------------------- */
    function initGalleries() {
        $$("[data-ar-gallery]").forEach(function (gallery) {
            var track = $("[data-ar-gallery-track]", gallery);
            if (!track) return;
            var thumbs = $$("[data-ar-thumb]", gallery);
            var dots = $$("[data-ar-dot]", gallery);
            var slides = $$(".ar-gallery__slide", track);
            var rtl = window.getComputedStyle(track).direction === "rtl";

            var currentIndex = function () {
                if (!track.clientWidth) return 0;
                return clamp(Math.round(Math.abs(track.scrollLeft) / track.clientWidth), 0, slides.length - 1);
            };

            var paint = function (i) {
                thumbs.forEach(function (t, idx) {
                    t.classList.toggle("is-active", idx === i);
                    t.setAttribute("aria-current", idx === i ? "true" : "false");
                });
                dots.forEach(function (d, idx) {
                    d.classList.toggle("is-active", idx === i);
                    d.setAttribute("aria-current", idx === i ? "true" : "false");
                });
            };

            var goTo = function (i, smooth) {
                track.scrollTo({
                    left: (rtl ? -1 : 1) * i * track.clientWidth,
                    behavior: smooth === false || reduceMotion.matches ? "auto" : "smooth"
                });
            };

            thumbs.forEach(function (t, i) { on(t, "click", function () { goTo(i); }); });
            dots.forEach(function (d, i) { on(d, "click", function () { goTo(i); }); });
            on(track, "scroll", debounce(function () { paint(currentIndex()); }, 70), { passive: true });

            var zoomBtn = $("[data-ar-zoom-open]", gallery);
            var dialog = doc.getElementById("ar-zoom");
            if (zoomBtn && dialog) {
                var dialogImg = $("img", dialog);
                on(zoomBtn, "click", function () {
                    var slide = slides[currentIndex()];
                    var img = slide && $("img", slide);
                    if (img && dialogImg) {
                        dialogImg.src = img.getAttribute("data-full") || img.src;
                        dialogImg.alt = img.alt || "";
                    }
                    if (typeof dialog.showModal === "function") dialog.showModal();
                    else dialog.setAttribute("open", "");
                });
                $$("[data-ar-zoom-close]", dialog).forEach(function (btn) {
                    on(btn, "click", function () { dialog.close ? dialog.close() : dialog.removeAttribute("open"); });
                });
                on(dialog, "click", function (e) { if (e.target === dialog) dialog.close(); });
            }
        });
    }

    /* ----------------------------------------------------------------------
       Product variants + sticky buy bar
       ---------------------------------------------------------------------- */
    function initVariants() {
        $$("[data-ar-variant]").forEach(function (group) {
            var output = $("[data-ar-variant-output]", group);
            var radios = $$("input[type=radio]", group);
            var render = function () {
                var checked = radios.filter(function (r) { return r.checked; })[0];
                if (!checked || !output) return;
                var label = checked.getAttribute("data-label") || checked.value;
                output.textContent = label;
            };
            radios.forEach(function (radio) {
                on(radio, "change", function () {
                    render();
                    radios.forEach(function (r) {
                        var lbl = r.closest(".ar-swatch, .ar-size");
                        if (lbl) lbl.classList.toggle("is-active", r.checked);
                    });
                });
            });
            render();
        });

        var addBtn = $("[data-ar-buybar-add]");
        if (addBtn) {
            on(addBtn, "click", function () {
                var form = doc.getElementById("ar-product-form");
                if (!form) return;
                if (typeof form.requestSubmit === "function") form.requestSubmit();
                else form.submit();
            });
        }
    }

    /* ----------------------------------------------------------------------
       Quantity steppers
       ---------------------------------------------------------------------- */
    function initQty() {
        $$("[data-ar-qty]").forEach(function (wrap) {
            var input = $("[data-qty-input]", wrap);
            if (!input) return;
            var min = input.min !== "" ? +input.min : 1;
            var max = input.max !== "" ? +input.max : 99;
            var set = function (v) {
                input.value = clamp(v, min, max);
                input.dispatchEvent(new Event("change", { bubbles: true }));
            };
            $$("[data-qty-step]", wrap).forEach(function (btn) {
                on(btn, "click", function (e) {
                    e.preventDefault();
                    set(Math.round(+input.value || min) + (+btn.getAttribute("data-qty-step")));
                });
            });
            on(input, "change", function () {
                var v = Math.round(+input.value || min);
                input.value = clamp(v, min, max);
            });
            /* implicit submission would pick the first submit button in the
               form, which on the cart page is the per-row "remove" button */
            on(input, "keydown", function (e) {
                if (e.key !== "Enter") return;
                var form = input.form;
                if (!form) return;
                var submit = form.querySelector("[data-ar-submit]");
                if (!submit) return;
                e.preventDefault();
                if (typeof form.requestSubmit === "function") form.requestSubmit(submit);
                else submit.click();
            });
        });
    }

    /* ----------------------------------------------------------------------
       Catalogue filters: restore multi-value state + chip toggles
       ---------------------------------------------------------------------- */
    function initFilters() {
        var params = new URLSearchParams(window.location.search);
        var multi = ["brand", "size"];
        var singles = ["min_price", "max_price"];

        $$("[data-ar-filter-form]").forEach(function (form) {
            var inputs = $$("input", form);

            multi.forEach(function (name) {
                var values = params.getAll(name);
                if (!values.length) return;
                inputs.forEach(function (input) {
                    if (input.name === name && values.indexOf(input.value) !== -1) {
                        input.checked = true;
                        var chip = input.closest(".ar-size");
                        if (chip) chip.classList.add("is-active");
                    }
                });
            });

            var available = $('input[name="available"]', form);
            if (available && params.get("available")) available.checked = true;

            singles.forEach(function (name) {
                var input = $('input[name="' + name + '"]', form);
                if (input && !input.value) input.value = params.get(name) || "";
            });

            on(form, "change", function (e) {
                var chip = e.target.closest(".ar-size");
                if (chip) chip.classList.toggle("is-active", e.target.checked);
            });
        });
    }

    /* ----------------------------------------------------------------------
       OTP boxes -> hidden input
       ---------------------------------------------------------------------- */
    function initOtp() {
        $$("[data-ar-otp]").forEach(function (wrap) {
            var hidden = $("[data-otp-value]", wrap);
            var targetId = wrap.getAttribute("data-otp-target");
            var target = targetId ? doc.getElementById(targetId) : null;
            var inputs = $$("[data-otp-digit]", wrap);
            if (!inputs.length) return;
            if (target) target.tabIndex = -1;

            var sync = function () {
                var code = inputs.map(function (i) { return i.value.replace(/\D/g, ""); }).join("");
                if (hidden) hidden.value = code;
                if (target) target.value = code;
            };

            inputs.forEach(function (input, i) {
                on(input, "input", function () {
                    input.value = input.value.replace(/\D/g, "").slice(-1);
                    if (input.value && i < inputs.length - 1) inputs[i + 1].focus();
                    sync();
                });
                on(input, "keydown", function (e) {
                    if (e.key === "Backspace" && !input.value && i > 0) {
                        e.preventDefault();
                        inputs[i - 1].focus();
                        inputs[i - 1].value = "";
                        sync();
                    } else if (e.key === "ArrowLeft" && i < inputs.length - 1) {
                        e.preventDefault();
                        inputs[i + 1].focus();
                    } else if (e.key === "ArrowRight" && i > 0) {
                        e.preventDefault();
                        inputs[i - 1].focus();
                    }
                });
                on(input, "paste", function (e) {
                    e.preventDefault();
                    var data = (e.clipboardData || window.clipboardData).getData("text") || "";
                    var digits = data.replace(/\D/g, "").slice(0, inputs.length);
                    if (!digits) return;
                    for (var k = 0; k < digits.length && i + k < inputs.length; k++) inputs[i + k].value = digits[k];
                    inputs[Math.min(i + digits.length, inputs.length - 1)].focus();
                    sync();
                });
                on(input, "focus", function () { input.select(); });
            });

            var initialValue = (hidden && hidden.value) || (target && target.value) || "";
            if (initialValue) {
                var initial = initialValue.replace(/\D/g, "");
                inputs.forEach(function (input, i) { input.value = initial[i] || ""; });
            }
            var otpForm = wrap.closest("form");
            if (otpForm) on(otpForm, "submit", sync);
            sync();
            wrap.addEventListener("ar:reset", function () {
                inputs.forEach(function (i) { i.value = ""; });
                sync();
            });
        });
    }

    /* ----------------------------------------------------------------------
       Password visibility + strength
       ---------------------------------------------------------------------- */
    function initPasswords() {
        $$("[data-ar-pw-toggle]").forEach(function (btn) {
            var id = btn.getAttribute("data-ar-pw-toggle");
            var input = id ? doc.getElementById(id) : ($( "input", btn.closest(".ar-input-group") || btn.closest(".ar-field") || doc));
            if (!input) return;
            on(btn, "click", function () {
                var show = input.type === "password";
                input.type = show ? "text" : "password";
                btn.setAttribute("aria-pressed", show ? "true" : "false");
                btn.setAttribute("aria-label", show ? "پنهان کردن رمز" : "نمایش رمز");
                btn.classList.toggle("is-active", show);
            });
        });

        $$("[data-ar-pwmeter]").forEach(function (meter) {
            var field = meter.closest(".ar-field") || meter.parentNode;
            var input = $('input[type="password"], input[name*="password"]', field);
            if (!input) return;
            on(input, "input", function () {
                var v = input.value;
                var score = 0;
                if (v.length >= 8) score++;
                if (/[a-z]/.test(v) && /[A-Z]/.test(v)) score++;
                if (/\d/.test(v)) score++;
                if (/[^A-Za-z0-9]/.test(v)) score++;
                if (v.length > 0 && v.length < 6) score = Math.min(score, 1);
                meter.setAttribute("data-level", String(score));
            });
        });
    }

    /* ----------------------------------------------------------------------
       Inline validation
       ---------------------------------------------------------------------- */
    var MSG = {
        required: "این فیلد الزامی است.",
        email: "یک ایمیل معتبر وارد کنید.",
        number: "یک عدد معتبر وارد کنید.",
        short: "مقدار وارد شده کوتاه است.",
        mismatch: "مقدار وارد شده معتبر نیست."
    };

    function setFieldError(field, message) {
        var wrap = field.closest(".ar-field") || field.parentNode;
        wrap.classList.add("has-error");
        field.classList.add("is-invalid");
        field.setAttribute("aria-invalid", "true");

        var error = wrap.querySelector("[data-ar-error]");
        if (!error) {
            error = doc.createElement("p");
            error.className = "ar-error";
            error.setAttribute("data-ar-error", "");
            error.id = (field.id || field.name || "field") + "-error";
            wrap.appendChild(error);
        }
        error.textContent = message;

        var described = (field.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean);
        if (described.indexOf(error.id) === -1) described.push(error.id);
        field.setAttribute("aria-describedby", described.join(" "));
    }

    function clearFieldError(field) {
        var wrap = field.closest(".ar-field") || field.parentNode;
        wrap.classList.remove("has-error");
        field.classList.remove("is-invalid");
        field.removeAttribute("aria-invalid");
        var error = wrap.querySelector("[data-ar-error]");
        if (error) error.remove();
    }

    function validateField(field) {
        if (field.disabled || field.type === "hidden" || field.hasAttribute("data-ar-skip-validation")) return true;
        if (field.checkValidity()) {
            clearFieldError(field);
            return true;
        }
        var message = field.getAttribute("data-msg");
        if (!message) {
            if (field.validity.valueMissing) message = MSG.required;
            else if (field.validity.typeMismatch && field.type === "email") message = MSG.email;
            else if (field.validity.badInput || field.validity.rangeUnderflow || field.validity.rangeOverflow) message = MSG.number;
            else if (field.validity.tooShort) message = "حداقل " + toFa(field.minLength) + " نویسه لازم است.";
            else message = MSG.mismatch;
        }
        setFieldError(field, message);
        return false;
    }

    function initValidation() {
        $$("form[data-ar-validate]").forEach(function (form) {
            form.noValidate = true;
            var fields = $$("input, select, textarea", form).filter(function (f) {
                return ["hidden", "submit", "button", "reset"].indexOf(f.type) === -1;
            });

            fields.forEach(function (field) {
                on(field, "blur", function () {
                    if (field.value !== "" || field.required) validateField(field);
                });
                on(field, "input", function () {
                    if (field.classList.contains("is-invalid")) validateField(field);
                });
            });

            on(form, "submit", function (e) {
                if (form.dataset.submitting === "1") { e.preventDefault(); return; }

                var bad = null;
                fields.forEach(function (field) {
                    if (!validateField(field) && !bad) bad = field;
                });

                var otp = form.querySelector("[data-ar-otp]");
                if (otp) {
                    var hidden = otp.querySelector("[data-otp-value]");
                    var targetId = otp.getAttribute("data-otp-target");
                    var target = targetId ? doc.getElementById(targetId) : null;
                    var otpValue = hidden ? hidden.value : (target ? target.value : "");
                    var digits = otp.querySelectorAll("[data-otp-digit]").length;
                    if (otpValue.length < digits) {
                        e.preventDefault();
                        otp.classList.add("is-invalid");
                        var empty = Array.prototype.filter.call(otp.querySelectorAll("[data-otp-digit]"), function (i) { return !i.value; })[0];
                        if (empty) empty.focus();
                        return;
                    }
                    otp.classList.remove("is-invalid");
                }

                if (bad) {
                    e.preventDefault();
                    try { bad.focus({ preventScroll: false }); } catch (err) { bad.focus(); }
                    if (bad.scrollIntoView) bad.scrollIntoView({ block: "center", behavior: reduceMotion.matches ? "auto" : "smooth" });
                    return;
                }

                form.dataset.submitting = "1";
                var btn = form.querySelector("[data-ar-submit]") || form.querySelector('button[type="submit"]');
                if (btn) btn.classList.add("is-loading");
                form.setAttribute("aria-busy", "true");
            });
        });

        on(doc, "submit", function (e) {
            var form = e.target;
            if (!form || form.tagName !== "FORM" || e.defaultPrevented) return;
            if (form.hasAttribute("data-ar-validate")) return;
            if (form.dataset.submitting === "1") { e.preventDefault(); return; }
            form.dataset.submitting = "1";
            var btn = e.submitter || form.querySelector("[data-ar-submit]") || form.querySelector('button[type="submit"]');
            if (btn) btn.classList.add("is-loading");
        });
    }

    /* ----------------------------------------------------------------------
       Persian/Arabic digits -> latin on numeric inputs (server compatibility)
       ---------------------------------------------------------------------- */
    function initDigits() {
        var selector = 'input[type="tel"], input[inputmode="numeric"], input[name*="phone"], input[name*="postal"], input[name="code"], input[id*="phone"], input[id*="postal"]';
        $$(selector).forEach(function (input) {
            on(input, "input", function () {
                var before = input.value;
                var after = before
                    .replace(/[\u06F0-\u06F9]/g, function (d) { return String(d.charCodeAt(0) - 1776); })
                    .replace(/[\u0660-\u0669]/g, function (d) { return String(d.charCodeAt(0) - 1632); });
                if (after !== before) {
                    var pos = input.selectionStart;
                    input.value = after;
                    try { input.setSelectionRange(pos, pos); } catch (e) {}
                }
            });
        });
    }

    /* ----------------------------------------------------------------------
       Toasts
       ---------------------------------------------------------------------- */
    var TOAST_ICON = {
        success: "icon-check",
        danger: "icon-close",
        warning: "icon-info-circle",
        info: "icon-info-circle"
    };

    function toastContainer() {
        var c = doc.getElementById("ar-toasts");
        if (!c) {
            c = doc.createElement("div");
            c.id = "ar-toasts";
            c.className = "ar-toasts";
            c.setAttribute("aria-live", "polite");
            c.setAttribute("aria-atomic", "false");
            doc.body.appendChild(c);
        }
        return c;
    }

    function mountToast(el) {
        var duration = parseInt(el.getAttribute("data-duration"), 10) || 6000;
        var bar = $(".ar-toast__progress", el);
        if (bar) bar.style.animationDuration = duration + "ms";

        var remaining = duration;
        var startedAt = 0;
        var timer = null;

        var dismiss = function () {
            if (!el.parentNode || el.classList.contains("is-leaving")) return;
            el.classList.add("is-leaving");
            setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 260);
        };

        var start = function () {
            startedAt = Date.now();
            timer = setTimeout(dismiss, remaining);
            if (bar) bar.style.animationPlayState = "running";
        };
        var pause = function () {
            clearTimeout(timer);
            remaining -= Date.now() - startedAt;
            if (remaining < 800) remaining = 800;
            if (bar) bar.style.animationPlayState = "paused";
        };

        on(el, "mouseenter", pause);
        on(el, "mouseleave", start);
        on(el, "focusin", pause);
        on(el, "focusout", start);
        on($("[data-ar-toast-close]", el), "click", dismiss);

        start();
    }

    function toast(type, title, text, opts) {
        opts = opts || {};
        type = TOAST_ICON[type] ? type : "info";
        var el = doc.createElement("div");
        el.className = "ar-toast ar-toast--" + type;
        el.setAttribute("role", type === "danger" ? "alert" : "status");
        el.setAttribute("data-duration", opts.duration || 6000);
        el.innerHTML =
            '<span class="ar-toast__icon" aria-hidden="true"><i class="' + TOAST_ICON[type] + '"></i></span>' +
            '<div class="ar-toast__text">' +
                (title ? "<strong>" + esc(title) + "</strong>" : "") +
                (text ? "<div>" + esc(text) + "</div>" : "") +
            "</div>" +
            '<button type="button" class="ar-toast__close" data-ar-toast-close aria-label="بستن"><i class="icon-close" aria-hidden="true"></i></button>' +
            '<span class="ar-toast__progress" aria-hidden="true"></span>';
        toastContainer().appendChild(el);
        mountToast(el);
        return el;
    }

    function initToasts() {
        $$("[data-ar-toast]").forEach(function (el) {
            el.classList.add("ar-toast");
            if (!el.getAttribute("data-duration")) el.setAttribute("data-duration", "8000");
            mountToast(el);
        });
    }

    /* ----------------------------------------------------------------------
       Reveal on scroll
       ---------------------------------------------------------------------- */
    function initReveal() {
        var items = $$("[data-ar-reveal]");
        if (!items.length) return;

        if (reduceMotion.matches || !("IntersectionObserver" in window)) {
            items.forEach(function (el) { el.classList.add("is-in"); });
            return;
        }

        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                entry.target.classList.add("is-in");
                io.unobserve(entry.target);
            });
        }, { rootMargin: "0px 0px -6% 0px", threshold: 0.06 });

        items.forEach(function (el, i) {
            if (!el.style.getPropertyValue("--ar-delay")) el.style.setProperty("--ar-delay", String(i % 5));
            io.observe(el);
        });
    }

    /* ----------------------------------------------------------------------
       Countdown (upcoming Friday, local time)
       ---------------------------------------------------------------------- */
    function nextWeekend() {
        var now = new Date();
        var day = now.getDay(); /* 0 Sun … 5 Fri, 6 Sat */
        var add = (5 - day + 7) % 7;
        var end = new Date(now.getFullYear(), now.getMonth(), now.getDate() + add, 23, 59, 59);
        if (end <= now) end.setDate(end.getDate() + 7);
        return end;
    }

    function initCountdown() {
        $$("[data-ar-countdown]").forEach(function (box) {
            var raw = box.getAttribute("data-deadline");
            var end = raw ? new Date(raw) : nextWeekend();
            if (isNaN(end.getTime())) end = nextWeekend();

            var cells = {
                d: $("[data-cd='days']", box),
                h: $("[data-cd='hours']", box),
                m: $("[data-cd='minutes']", box),
                s: $("[data-cd='seconds']", box)
            };
            var timer;

            var tick = function () {
                var diff = Math.max(0, end.getTime() - Date.now());
                var d = Math.floor(diff / 864e5);
                var h = Math.floor((diff % 864e5) / 36e5);
                var m = Math.floor((diff % 36e5) / 6e4);
                var s = Math.floor((diff % 6e4) / 1e3);
                var pad = function (n) { return n < 10 ? "0" + n : String(n); };
                if (cells.d) cells.d.textContent = toFa(pad(d));
                if (cells.h) cells.h.textContent = toFa(pad(h));
                if (cells.m) cells.m.textContent = toFa(pad(m));
                if (cells.s) cells.s.textContent = toFa(pad(s));
                if (diff <= 0) clearInterval(timer);
            };

            tick();
            timer = setInterval(tick, 1000);
            on(doc, "visibilitychange", function () { if (!doc.hidden) tick(); });
        });
    }

    /* ----------------------------------------------------------------------
       Newsletter promo modal
       ---------------------------------------------------------------------- */
    function initPromo() {
        var modal = doc.querySelector("[data-ar-promo]");
        if (!modal) return;

        var key = "ar-promo-dismissed";
        var last = parseInt(store.get(key) || "0", 10);
        if (last && Date.now() - last < 7 * 864e5) return;

        var delay = parseInt(modal.getAttribute("data-delay"), 10) || 9000;
        var timer = setTimeout(function () {
            if (layers.length) return;
            openLayer(modal);
        }, delay);

        var hide = $("[data-ar-promo-hide]", modal);
        on(modal, "ar:close", function () {
            clearTimeout(timer);
            if (hide && hide.checked) store.set(key, String(Date.now()));
        });
    }

    /* ----------------------------------------------------------------------
       Print + misc
       ---------------------------------------------------------------------- */
    function initMisc() {
        $$("[data-ar-autosubmit]").forEach(function (field) {
            on(field, "change", function () {
                if (field.form) field.form.submit();
            });
        });

        $$("[data-ar-print]").forEach(function (btn) {
            on(btn, "click", function () { window.print(); });
        });

        $$("[data-ar-copy]").forEach(function (btn) {
            on(btn, "click", function () {
                var value = btn.getAttribute("data-ar-copy");
                if (!value || !navigator.clipboard) return;
                navigator.clipboard.writeText(value).then(function () {
                    toast("success", "کپی شد", value, { duration: 2600 });
                }).catch(function () {});
            });
        });

        $$("img").forEach(function (img) {
            if (!img.hasAttribute("decoding")) img.setAttribute("decoding", "async");
        });
    }

    /* ----------------------------------------------------------------------
       Persian digits for editorial copy (CMS text keeps latin digits)
       ---------------------------------------------------------------------- */
    function initFaText() {
        $$("[data-ar-digitize]").forEach(function (host) {
            if (!/\d/.test(host.textContent)) return;
            var walker = doc.createTreeWalker(host, NodeFilter.SHOW_TEXT, null);
            var node;
            while ((node = walker.nextNode())) {
                if (/\d/.test(node.nodeValue)) node.nodeValue = toFa(node.nodeValue);
            }
        });
    }

    /* ----------------------------------------------------------------------
       Confirmation dialog for destructive forms
       ---------------------------------------------------------------------- */
    function initConfirm() {
        var modal = doc.getElementById("ar-confirm");
        if (!modal) return;

        var text = $("[data-ar-confirm-text]", modal);
        var accept = $("[data-ar-confirm-accept]", modal);
        var pending = null;

        $$("form[data-ar-confirm]").forEach(function (form) {
            on(form, "submit", function (e) {
                if (form.dataset.confirmed === "1") return;
                e.preventDefault();
                pending = form;
                if (text) text.textContent = form.getAttribute("data-ar-confirm");
                openLayer(modal, doc.activeElement);
            });
        });

        on(accept, "click", function () {
            if (!pending) return;
            var form = pending;
            pending = null;
            form.dataset.confirmed = "1";
            closeLayer(modal);
            if (typeof form.requestSubmit === "function") form.requestSubmit();
            else form.submit();
        });

        on(modal, "ar:close", function () { pending = null; });
    }

    /* ----------------------------------------------------------------------
       Boot
       ---------------------------------------------------------------------- */
    window.Ario = {
        toast: toast,
        openLayer: openLayer,
        closeLayer: closeLayer,
        toFa: toFa
    };

    initPreloader();

    var boot = function () {
        initTheme();
        initLayers();
        initConfirm();
        initHeader();
        initSearchShortcut();
        initShelves();
        initMega();
        initSubmenus();
        initTabs();
        initGalleries();
        initVariants();
        initQty();
        initFilters();
        initOtp();
        initPasswords();
        initValidation();
        initDigits();
        initFaText();
        initToasts();
        initReveal();
        initCountdown();
        initPromo();
        initMisc();
    };

    if (doc.readyState === "loading") on(doc, "DOMContentLoaded", boot);
    else boot();
})();
