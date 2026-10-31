# Persian (Jalali) Calendar Implementation Plan

## Overview
This plan outlines the complete implementation of Persian (Jalali/Shamsi) calendar support for the Ario Shop Django e-commerce project. The implementation will convert all date displays from Gregorian to Persian calendar while keeping the database storage in Gregorian format.

## Current State Analysis

### Existing Date Fields (15 locations)
- **Menu_Module**: `created_at`, `updated_at`
- **Contact_Module**: `created_at` (ContactMessage), `created_at`, `updated_at` (Newsletter)
- **AboutUs_Module**: `created_at`
- **Cart_Module**: `starts_at`, `ends_at` (DiscountCode), `created_at`, `updated_at` (Cart), `created_at`, `updated_at` (Order), `created_at`, `updated_at` (OrderItem)
- **Products_Module**: `created_at`, `updated_at` (Category, Product, ProductImage, Tag, Review)
- **Accounts_Module**: `created_at`, `updated_at` (Profile)

### Current Settings
- `TIME_ZONE = 'Asia/Tehran'` ✓
- `LANGUAGE_CODE = 'fa-ir'` ✓
- `USE_TZ = True` ✓

---

## Implementation Steps

### Step 1: Install Required Packages

```bash
pip install jdatetime
```

Add to requirements.txt:
```
jdatetime
```

### Step 2: Create Jalali Date Utility Module

Create `Core_Module/templatetags/jalali_tags.py` or add to existing utilities:

**Features needed:**
- `gregorian_to_jalali(date)` - Convert datetime/date to Jalali
- `jalali_to_gregorian(date_str)` - Parse Jalali string to Gregorian
- `format_jalali_datetime(dt, format_string)` - Format with Persian locale
- `format_jalali_date(dt)` - Format as YYYY/MM/DD

### Step 3: Create Template Filters

Create `Core_Module/templatetags/jalali_tags.py`:

```python
@register.filter
def to_jalali(value):
    """Convert datetime to Persian date string"""
    # Implementation

@register.filter
def to_jalali_datetime(value):
    """Convert datetime to Persian date/time string"""
    # Implementation
```

### Step 4: Create Custom Admin Widgets

Create `Core_Module/admin_widgets.py`:

**JalaliDateWidget:**
- Extends Django's AdminDateWidget
- Uses Persian calendar for date selection
- Displays Persian month names (Farvardin, Ordibehesht, etc.)
- JavaScript integration for Persian date picker

**JalaliDateTimeWidget:**
- Extends AdminTimeWidget
- Shows Persian date with time

### Step 5: Create Admin Configuration Mixin

Create `Core_Module/admin_mixins.py`:

```python
class JalaliDateMixin:
    """Mixin to automatically use Jalali date widgets in admin"""
    
    def get_form(self, request, obj=None, **kwargs):
        # Override to use Jalali widgets
```

### Step 6: Update All Admin Classes

Update admin configurations in:
- `Menu_Module/admin.py`
- `Contact_Module/admin.py`
- `AboutUs_Module/admin.py`
- `Cart_Module/admin.py`
- `Products_Module/admin.py`
- `Accounts_Module/admin.py`

Each admin class needs:
- Use `JalaliDateMixin`
- Define `list_display` with Jalali date methods
- Use `readonly_fields` with Persian date display
- Add `list_filter` with proper date filtering

### Step 7: Update Templates

Update all templates displaying dates:
- Product detail pages
- Order history
- User profile
- Cart views
- Admin templates (via admin configuration)

### Step 8: Configuration in settings.py

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    ...
    'Core_Module',  # For shared utilities
]

# Template context processors for Jalali
TEMPLATES = [{
    ...
    'OPTIONS': {
        'context_processors': [
            ...
            'Core_Module.context_processors.jalali_context',
        ],
    },
}]

# Add custom template tags
TEMPLATE_DIRS = [
    ...
]

# Load custom template tags
OPTIONS = {
    'libraries': {
        'jalali_tags': 'Core_Module.templatetags.jalali_tags',
    },
}
```

---

## File Structure

```
Ario_Shop/
Core_Module/
    __init__.py
    admin_mixins.py      # Admin configuration mixins
    admin_widgets.py     # Custom Jalali date widgets
    utils.py             # Date conversion utilities
    templatetags/
        __init__.py
        jalali_tags.py   # Template filters
    context_processors.py
```

---

## Key Implementation Details

### Persian Month Names
```python
PERSIAN_MONTHS = [
    'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
]
```

### Date Format Standards
- **Short**: YYYY/MM/DD (e.g., 1404/01/15)
- **Long**: DD Month YYYY (e.g., 15 فروردین 1404)
- **With Time**: YYYY/MM/DD HH:MM (e.g., 1404/01/15 14:30)

### JavaScript for Admin Date Picker
Need to integrate PersianDatePicker or similar library for admin widget.

---

## Testing Checklist

- [ ] Frontend: All product dates display in Persian
- [ ] Frontend: Order dates display in Persian  
- [ ] Frontend: User registration date in Persian
- [ ] Admin: Date widgets show Persian calendar
- [ ] Admin: Month names in Persian
- [ ] Admin: List filters work with Jalali dates
- [ ] Admin: Date-based search works correctly
- [ ] Database: All dates stored in Gregorian (verify)
- [ ] Timezone: Correct handling with USE_TZ

---

## Migration Considerations

**No database migration needed** - Dates remain in Gregorian format in the database. Conversion happens at:
1. Template level (for display)
2. Admin form level (for input)

This ensures:
- No data corruption
- No migration complexity
- Full compatibility with external systems
- Standard Django date operations still work

---

## Implementation Priority

1. **High Priority**: Admin date widgets and displays (affects store management)
2. **High Priority**: Template filters for frontend display
3. **Medium Priority**: Admin list filters and search
4. **Low Priority**: Custom form validation for Jalali input

---

## Files Created/Modified

### Core Module Files
- `Core_Module/__init__.py`
- `Core_Module/apps.py`
- `Core_Module/utils.py` - Date conversion utilities
- `Core_Module/templatetags/__init__.py`
- `Core_Module/templatetags/jalali_tags.py` - Template filters
- `Core_Module/admin_widgets.py` - Admin date widgets
- `Core_Module/admin_mixins.py` - Admin mixins
- `Core_Module/admin/js/jalali-datepicker.js` - Date picker JavaScript
- `Core_Module/admin/css/jalali-datepicker.css` - Date picker CSS

### Settings Modified
- `Ario_Shop/settings.py` - Added Core_Module to INSTALLED_APPS

### Admin Files Updated
- `Cart_Module/admin.py`
- `Products_Module/admin.py`
- `Accounts_Module/admin.py`

---

## Template Usage Guide

### Loading the Template Tags

At the top of each template that needs Persian date display, add:

```django
{% load jalali_tags %}
```

### Available Template Filters

#### 1. Short Date Format (YYYY/MM/DD)
```django
{{ order.created_at|to_jalali }}
{# Output: 1403/12/04 #}
```

#### 2. Date with Time
```django
{{ order.created_at|to_jalali_datetime }}
{# Output: 1403/12/04 14:30 #}
```

#### 3. Long Date Format (DD Month YYYY)
```django
{{ order.created_at|to_jalali_long }}
{# Output: 04 اسفند 1403 #}
```

#### 4. Full Date with Weekday
```django
{{ order.created_at|to_jalali_full }}
{# Output: شنبه 04 اسفند 1403 - ساعت 14:30 #}
```

#### 5. Date with Weekday (Short Format)
```django
{{ order.created_at|to_jalali_with_weekday }}
{# Output: شنبه 1403/12/04 #}
```

#### 6. Time Ago (Persian)
```django
{{ order.created_at|time_ago }}
{# Output: 2 ساعت پیش, 5 روز پیش, 2 هفته پیش #}
```

#### 7. Custom Format
```django
{{ order.created_at|jalali_date:'short' }}
{{ order.created_at|jalali_date:'long' }}
{{ order.created_at|jalali_date:'with_time' }}
{{ order.created_at|jalali_date:'full' }}
```

### Template Tags (Functions)

#### Get Persian Month Name
```django
{% persian_month_name 1 %}
{# Output: فروردین #}
```

#### Get Persian Weekday Name
```django
{% persian_weekday_name 0 %}
{# Output: شنبه #}
```

---

## Admin Panel Usage

The admin panels for Cart, Products, and Accounts modules have been updated to:

1. **Display dates in Persian format** in list views
2. **Use Jalali date pickers** for date input fields
3. **Show Persian month names** in date widgets

---

## Deployment Steps

1. **Install jdatetime** (if not already installed):
   ```bash
   pip install jdatetime
   ```

2. **Upload all Core_Module files** to your server

3. **Update settings.py** on server with the new Core_Module configuration

4. **Collect static files**:
   ```bash
   python manage.py collectstatic
   ```

5. **Restart the Django application** on PythonAnywhere

6. **Clear browser cache** to ensure new JavaScript loads correctly

---

## Testing Checklist

- [ ] Frontend: All product dates display in Persian
- [ ] Frontend: Order dates display in Persian  
- [ ] Frontend: User registration date in Persian
- [ ] Admin: Date widgets show Persian calendar
- [ ] Admin: Month names in Persian
- [ ] Admin: List filters work with Jalali dates
- [ ] Admin: Date-based search works correctly
- [ ] Database: All dates stored in Gregorian (verify)
- [ ] Timezone: Correct handling with USE_TZ
