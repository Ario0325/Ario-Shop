/**
 * آریو شاپ — سیستم تغییر تم پنل مدیریت
 * Theme Switcher System v1.0
 */

(function() {
    'use strict';
    
    // تنظیمات تم‌ها - رنگ‌های متفاوت و زیبا
    const themes = {
        'atelier-gold': {
            name: 'طلایی آتلیه',
            isDark: true,
            color: '#C8944C',
            gradient: 'linear-gradient(135deg, #E7C48A 0%, #C8944C 50%, #A9782F 100%)'
        },
        'royal-purple': {
            name: 'بنفش سلطنتی',
            isDark: true,
            color: '#8b5cf6',
            gradient: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 50%, #a855f7 100%)'
        },
        'ocean-blue': {
            name: 'آبی اقیانوسی',
            isDark: true,
            color: '#06b6d4',
            gradient: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 50%, #22d3ee 100%)'
        },
        'pearl-white': {
            name: 'مروارید سفید',
            isDark: false,
            color: '#f8fafc',
            gradient: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #ffffff 100%)'
        },
        'forest-green': {
            name: 'جنگل سبز',
            isDark: true,
            color: '#22c55e',
            gradient: 'linear-gradient(135deg, #22c55e 0%, #16a34a 50%, #4ade80 100%)'
        },
        'sunset-orange': {
            name: 'غروب نارنجی',
            isDark: true,
            color: '#f97316',
            gradient: 'linear-gradient(135deg, #f97316 0%, #ea580c 50%, #fb923c 100%)'
        },
        'rose-pink': {
            name: 'رُز صورتی',
            isDark: true,
            color: '#ec4899',
            gradient: 'linear-gradient(135deg, #ec4899 0%, #db2777 50%, #f472b6 100%)'
        }
    };
    
    const DEFAULT_THEME = 'atelier-gold';
    const STORAGE_KEY = 'ario_admin_theme';
    const THEME_LINK_ID = 'admin-theme-stylesheet';
    
    // تابع بارگذاری تم
    function loadTheme(themeId) {
        const validTheme = themes[themeId] ? themeId : DEFAULT_THEME;
        
        // بررسی وجود لینک استایل
        let themeLink = document.getElementById(THEME_LINK_ID);
        
        if (!themeLink) {
            themeLink = document.createElement('link');
            themeLink.id = THEME_LINK_ID;
            themeLink.rel = 'stylesheet';
            document.head.appendChild(themeLink);
        }
        
        // بارگذاری فایل تم
        const themePath = `/static/admin/css/themes/${validTheme}.css`;
        themeLink.href = themePath;
        
        // ذخیره در localStorage
        try {
            localStorage.setItem(STORAGE_KEY, validTheme);
        } catch (e) {
            console.warn('LocalStorage not available:', e);
        }
        
        // به‌روزرسانی نشانگر تم فعال
        updateThemeIndicator(validTheme);
        
        // رویداد برای اعلام تغییر تم
        document.dispatchEvent(new CustomEvent('themeChanged', { 
            detail: { theme: validTheme, isDark: themes[validTheme].isDark } 
        }));
        
        return validTheme;
    }
    
    // تابع دریافت تم فعلی
    function getCurrentTheme() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            return themes[saved] ? saved : DEFAULT_THEME;
        } catch (e) {
            return DEFAULT_THEME;
        }
    }
    
    // تابع ایجاد رابط کاربری انتخاب تم
    function createThemeSelector() {
        // بررسی وجود قبلی
        if (document.getElementById('theme-selector-wrapper')) {
            return;
        }
        
        // ایجاد کانتینر
        const wrapper = document.createElement('div');
        wrapper.id = 'theme-selector-wrapper';
        wrapper.className = 'theme-selector-wrapper';
        
        // دکمه اصلی - طراحی مدرن‌تر
        const trigger = document.createElement('button');
        trigger.id = 'theme-trigger';
        trigger.className = 'theme-trigger';
        trigger.type = 'button';
        trigger.setAttribute('aria-label', 'انتخاب تم');
        trigger.setAttribute('aria-expanded', 'false');
        
        // آیکون با انیمیشن
        const icon = document.createElement('span');
        icon.className = 'theme-icon';
        icon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
        trigger.appendChild(icon);
        
        // عنوان
        const title = document.createElement('span');
        title.className = 'theme-title';
        title.textContent = 'تم';
        trigger.appendChild(title);
        
        // فلش با انیمیشن چرخشی
        const arrow = document.createElement('span');
        arrow.className = 'theme-arrow';
        arrow.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>';
        trigger.appendChild(arrow);
        
        wrapper.appendChild(trigger);
        
        // پنجره انتخاب تم - طراحی مدرن با انیمیشن
        const dropdown = document.createElement('div');
        dropdown.id = 'theme-dropdown';
        dropdown.className = 'theme-dropdown';
        
        // عنوان پنجره با آیکون
        const dropdownTitle = document.createElement('div');
        dropdownTitle.className = 'theme-dropdown-title';
        dropdownTitle.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 -8.313 -12.454z"/></svg> انتخاب تم پنل';
        dropdown.appendChild(dropdownTitle);
        
        // لیست تم‌ها - هر تم با طراحی منحصر به فرد
        const themeList = document.createElement('div');
        themeList.className = 'theme-list';
        
        Object.keys(themes).forEach((themeId, index) => {
            const theme = themes[themeId];
            const item = document.createElement('button');
            item.className = 'theme-item';
            item.dataset.theme = themeId;
            item.type = 'button';
            
            // رنگ نمایشی با گرادینت و انیمیشن
            const colorPreview = document.createElement('span');
            colorPreview.className = 'theme-color-preview';
            colorPreview.style.background = theme.isDark 
                ? `linear-gradient(135deg, ${theme.color} 0%, ${adjustColor(theme.color, -30)} 100%)`
                : `linear-gradient(135deg, ${theme.color} 0%, ${adjustColor(theme.color, 30)} 100%)`;
            
            // نام تم
            const themeName = document.createElement('span');
            themeName.className = 'theme-name';
            themeName.textContent = theme.name;
            
            // نشانگر تیره/روشن با آیکون بهتر
            const darkIndicator = document.createElement('span');
            darkIndicator.className = 'theme-dark-indicator';
            darkIndicator.innerHTML = theme.isDark 
                ? '<svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
                : '<svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" fill="none" stroke="currentColor" stroke-width="2"/></svg>';
            
            item.appendChild(colorPreview);
            item.appendChild(themeName);
            item.appendChild(darkIndicator);
            
            // انیمیشن ورود با تأخیر
            item.style.animationDelay = `${index * 0.05}s`;
            
            themeList.appendChild(item);
        });
        
        dropdown.appendChild(themeList);
        wrapper.appendChild(dropdown);
        
        // اضافه کردن به صفحه
        const header = document.getElementById('header');
        if (header) {
            header.appendChild(wrapper);
        } else {
            document.body.appendChild(wrapper);
        }
        
        // رویداد کلیک روی دکمه با انیمیشن
        trigger.addEventListener('click', function(e) {
            e.stopPropagation();
            const isOpen = wrapper.classList.contains('open');
            
            // بستن همه پنجره‌های باز با انیمیشن
            closeAllDropdowns();
            
            if (!isOpen) {
                wrapper.classList.add('open');
                trigger.setAttribute('aria-expanded', 'true');
                // انیمیشن باز شدن dropdown
                dropdown.style.opacity = '0';
                dropdown.style.transform = 'translateY(-10px) scale(0.95)';
                requestAnimationFrame(() => {
                    dropdown.style.opacity = '1';
                    dropdown.style.transform = 'translateY(0) scale(1)';
                });
            }
        });
        
        // رویداد کلیک روی آیتم‌های تم با انیمیشن انتخاب
        themeList.addEventListener('click', function(e) {
            const themeItem = e.target.closest('.theme-item');
            if (themeItem) {
                const selectedTheme = themeItem.dataset.theme;
                
                // انیمیشن انتخاب
                themeItem.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    themeItem.style.transform = 'scale(1)';
                }, 150);
                
                loadTheme(selectedTheme);
                closeAllDropdowns();
            }
        });
        
        // بستن پنجره با کلیک بیرون
        document.addEventListener('click', function(e) {
            if (!wrapper.contains(e.target)) {
                closeAllDropdowns();
            }
        });
        
        // تنظیم تم فعلی
        const currentTheme = getCurrentTheme();
        themeList.querySelectorAll('.theme-item').forEach(item => {
            if (item.dataset.theme === currentTheme) {
                item.classList.add('active');
            }
        });
    }
    
    // تابع کمکی برای تنظیم رنگ
    function adjustColor(color, amount) {
        const hex = color.replace('#', '');
        const num = parseInt(hex, 16);
        const r = Math.min(255, Math.max(0, (num >> 16) + amount));
        const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00FF) + amount));
        const b = Math.min(255, Math.max(0, (num & 0x0000FF) + amount));
        return '#' + (0x1000000 + r * 0x10000 + g * 0x100 + b).toString(16).slice(1);
    }
    
    // تابع بستن همه پنجره‌ها
    function closeAllDropdowns() {
        document.querySelectorAll('.theme-selector-wrapper.open').forEach(wrapper => {
            wrapper.classList.remove('open');
            const trigger = wrapper.querySelector('.theme-trigger');
            if (trigger) {
                trigger.setAttribute('aria-expanded', 'false');
            }
        });
    }
    
    // تابع به‌روزرسانی نشانگر تم
    function updateThemeIndicator(themeId) {
        const theme = themes[themeId];
        if (!theme) return;
        
        // به‌روزرسانی آیکون دکمه
        const trigger = document.getElementById('theme-trigger');
        if (trigger) {
            const icon = trigger.querySelector('.theme-icon');
            if (icon) {
                icon.style.backgroundColor = theme.color;
            }
        }
        
        // به‌روزرسانی حالت فعال در لیست
        const items = document.querySelectorAll('.theme-item');
        items.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.theme === themeId) {
                item.classList.add('active');
            }
        });
    }
    
    // اضافه کردن استایل‌های UI - طراحی مدرن با انیمیشن
    function addThemeSelectorStyles() {
        if (document.getElementById('theme-selector-styles')) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = 'theme-selector-styles';
        style.textContent = `
            /* استایل‌های انتخابگر تم - مدرن و زیبا */
            .theme-selector-wrapper {
                position: relative;
                display: inline-flex;
                align-items: center;
                margin-right: 12px;
                font-family: 'Vazir', 'Segoe UI', Tahoma, sans-serif;
            }
            
            .theme-trigger {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 10px 16px;
                background: linear-gradient(135deg, var(--ap-surface, #18181f) 0%, var(--ap-surface-2, #1f1f2a) 100%);
                border: 1px solid var(--ap-border, rgba(255,255,255,0.08));
                border-radius: 50px;
                color: var(--ap-text, #f1f5f9);
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                font-size: 13px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            }
            
            .theme-trigger:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 16px rgba(0,0,0,0.3), 0 0 20px var(--ap-primary-glow, rgba(139,92,246,0.2));
                border-color: var(--ap-primary, #8b5cf6);
            }
            
            .theme-trigger:active {
                transform: translateY(0);
            }
            
            .theme-icon {
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.5s ease;
            }\n            
            .theme-icon svg {
                width: 100%;
                height: 100%;
            }
            
            .theme-trigger:hover .theme-icon {
                transform: rotate(30deg);
            }
            
            .theme-arrow {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 16px;
                height: 16px;
                transition: transform 0.3s ease;
                opacity: 0.7;
            }
            
            .theme-arrow svg {
                width: 100%;
                height: 100%;
            }
            
            .theme-selector-wrapper.open .theme-arrow {
                transform: rotate(180deg);
                opacity: 1;
            }
            
            .theme-dropdown {
                position: absolute;
                top: calc(100% + 12px);
                right: 0;
                left: auto;
                min-width: 260px;
                background: linear-gradient(180deg, var(--ap-card, #1a1a24) 0%, var(--ap-surface, #18181f) 100%);
                border: 1px solid var(--ap-border, rgba(255,255,255,0.08));
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 40px var(--ap-primary-glow, rgba(139,92,246,0.1));
                padding: 16px;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                z-index: 10000;
            }
            
            .theme-selector-wrapper.open .theme-dropdown {
                opacity: 1;
                visibility: visible;
                transform: translateY(0) scale(1);
            }
            
            .theme-dropdown-title {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 12px;
                font-weight: 600;
                color: var(--ap-text-muted, #94a3b8);
                padding: 8px 12px;
                margin-bottom: 12px;
                border-bottom: 1px solid var(--ap-border, rgba(255,255,255,0.06));
            }
            
            .theme-dropdown-title svg {
                opacity: 0.7;
            }
            
            .theme-list {
                display: flex;
                flex-direction: column;
                gap: 6px;
            }
            
            .theme-item {
                display: flex;
                align-items: center;
                gap: 14px;
                width: 100%;
                padding: 12px 14px;
                background: transparent;
                border: 1px solid transparent;
                border-radius: 14px;
                color: var(--ap-text, #f1f5f9);
                cursor: pointer;
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                text-align: right;
                font-size: 13px;
                font-family: inherit;
                animation: themeItemFadeIn 0.4s ease backwards;
            }
            
            @keyframes themeItemFadeIn {
                from {
                    opacity: 0;
                    transform: translateX(-10px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            .theme-item:hover {
                background: linear-gradient(135deg, var(--ap-surface, #18181f) 0%, var(--ap-surface-2, #1f1f2a) 100%);
                border-color: var(--ap-border, rgba(255,255,255,0.1));
                transform: translateX(4px);
            }
            
            .theme-item.active {
                background: linear-gradient(135deg, var(--ap-primary-glow, rgba(139,92,246,0.2)) 0%, var(--ap-primary-glow, rgba(139,92,246,0.1)) 100%);
                border-color: var(--ap-primary, #8b5cf6);
                box-shadow: 0 0 20px var(--ap-primary-glow, rgba(139,92,246,0.2));
            }
            
            .theme-color-preview {
                width: 32px;
                height: 32px;
                border-radius: 10px;
                flex-shrink: 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1);
                transition: all 0.3s ease;
            }
            
            .theme-item:hover .theme-color-preview {
                transform: scale(1.1) rotate(5deg);
                box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            }
            
            .theme-item.active .theme-color-preview {
                box-shadow: 0 0 15px currentColor;
            }
            
            .theme-name {
                flex: 1;
                text-align: right;
                font-weight: 500;
            }
            
            .theme-dark-indicator {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                background: var(--ap-surface-2, #1f1f2a);
                transition: all 0.3s ease;
            }
            
            .theme-item:hover .theme-dark-indicator {
                transform: scale(1.1);
            }
            
            /* انیمیشن تغییر تم */
            @keyframes themeTransition {
                0% { opacity: 1; }
                25% { opacity: 0.8; filter: blur(1px); }
                50% { opacity: 0.6; filter: blur(2px); }
                75% { opacity: 0.8; filter: blur(1px); }
                100% { opacity: 1; }
            }
            
            body.theme-changing {
                animation: themeTransition 0.5s ease;
            }
            
            /* انیمیشن بارگذاری صفحه */
            @keyframes pageLoad {
                0% { opacity: 0; transform: translateY(10px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            
            #header {
                animation: pageLoad 0.6s ease;
            }
        `;
        
        document.head.appendChild(style);
    }
    
    // تابع مقداردهی اولیه
    function init() {
        // بارگذاری تم ذخیره شده
        const savedTheme = getCurrentTheme();
        loadTheme(savedTheme);
        
        // اضافه کردن استایل‌های UI
        addThemeSelectorStyles();
        
        // ایجاد رابط کاربری (با تأخیر برای اطمینان از بارگذاری کامل)
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(createThemeSelector, 100);
            });
        } else {
            setTimeout(createThemeSelector, 100);
        }
    }
    
    // اجرای اولیه
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // خروجی عمومی برای استفاده در صورت نیاز
    window.AdminTheme = {
        load: loadTheme,
        getCurrent: getCurrentTheme,
        themes: themes
    };
    
})();
