"""
Custom Admin Widgets for Persian (Jalali) Calendar

Provides custom form widgets for Django admin that use Persian
calendar for date selection.
"""

from django import forms
from datetime import datetime
import jdatetime


class JalaliDateWidget(forms.TextInput):
    """
    Persian (Jalali) Date Widget for Django Admin
    
    This widget provides a text input with JavaScript-based Persian
    date picker integration.
    
    Usage:
        class MyModelAdmin(admin.ModelAdmin):
            formfield_overrides = {
                models.DateField: {'widget': JalaliDateWidget},
                models.DateTimeField: {'widget': JalaliDateTimeWidget},
            }
    """
    
    class Media:
        # Include jQuery and Persian date picker library
        js = (
            'admin/js/jquery.init.js',
            'Core_Module/admin/js/jalali-datepicker.js',
        )
        css = {
            'all': (
                'Core_Module/admin/css/jalali-datepicker.css',
            )
        }
    
    def __init__(self, attrs=None, format='%Y/%m/%d'):
        self.format = format
        super().__init__(attrs)
    
    def render(self, name, value, attrs=None, renderer=None):
        # Convert value to Jalali for display
        display_value = ''
        if value:
            if isinstance(value, str):
                # Try to parse the string
                try:
                    dt = datetime.strptime(value, '%Y-%m-%d')
                    jd = jdatetime.datetime.fromgregorian(datetime=dt)
                    display_value = f'{jd.year}/{jd.month:02d}/{jd.day:02d}'
                except ValueError:
                    display_value = value
            elif hasattr(value, 'strftime'):
                # It's a date/datetime object
                try:
                    jd = jdatetime.datetime.fromgregorian(datetime=value)
                    display_value = f'{jd.year}/{jd.month:02d}/{jd.day:02d}'
                except:
                    display_value = str(value)
        
        # Add Persian date picker class
        attrs = attrs or {}
        attrs['class'] = 'vDateField jalali-date-picker' + attrs.get('class', '')
        attrs['placeholder'] = '1403/12/04'
        
        return super().render(name, display_value, attrs, renderer)
    
    def value_from_datadict(self, data, files, name):
        value = data.get(name, '')
        if value:
            # Convert Persian date to Gregorian for storage
            try:
                parts = value.split('/')
                if len(parts) == 3:
                    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                    jd = jdatetime.date(year, month, day)
                    gregorian_date = jd.togregorian()
                    return gregorian_date.strftime('%Y-%m-%d')
            except (ValueError, IndexError):
                pass
        return value


class JalaliDateTimeWidget(forms.TextInput):
    """
    Persian (Jalali) DateTime Widget for Django Admin
    
    This widget provides a text input with JavaScript-based Persian
    date and time picker integration.
    """
    
    class Media:
        js = (
            'admin/js/jquery.init.js',
            'Core_Module/admin/js/jalali-datepicker.js',
        )
        css = {
            'all': (
                'Core_Module/admin/css/jalali-datepicker.css',
            )
        }
    
    def __init__(self, attrs=None, format='%Y/%m/%d %H:%M'):
        self.format = format
        super().__init__(attrs)
    
    def render(self, name, value, attrs=None, renderer=None):
        # Convert value to Jalali for display
        display_value = ''
        if value:
            if isinstance(value, str):
                # Try to parse the string
                try:
                    dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    jd = jdatetime.datetime.fromgregorian(datetime=dt)
                    display_value = f'{jd.year}/{jd.month:02d}/{jd.day:02d} {jd.hour:02d}:{jd.minute:02d}'
                except ValueError:
                    try:
                        dt = datetime.strptime(value, '%Y-%m-%d')
                        jd = jdatetime.datetime.fromgregorian(datetime=dt)
                        display_value = f'{jd.year}/{jd.month:02d}/{jd.day:02d}'
                    except:
                        display_value = value
            elif hasattr(value, 'strftime'):
                # It's a date/datetime object
                try:
                    jd = jdatetime.datetime.fromgregorian(datetime=value)
                    display_value = f'{jd.year}/{jd.month:02d}/{jd.day:02d} {jd.hour:02d}:{jd.minute:02d}'
                except:
                    display_value = str(value)
        
        # Add Persian date time picker class
        attrs = attrs or {}
        attrs['class'] = 'vDateTimeField jalali-datetime-picker' + attrs.get('class', '')
        attrs['placeholder'] = '1403/12/04 14:30'
        
        return super().render(name, display_value, attrs, renderer)
    
    def value_from_datadict(self, data, files, name):
        value = data.get(name, '')
        if value:
            # Convert Persian date to Gregorian for storage
            try:
                # Split date and time
                parts = value.split()
                if len(parts) >= 1:
                    date_parts = parts[0].split('/')
                    if len(date_parts) == 3:
                        year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                        
                        hour = 0
                        minute = 0
                        if len(parts) >= 2:
                            time_parts = parts[1].split(':')
                            hour = int(time_parts[0]) if len(time_parts) > 0 else 0
                            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                        
                        jd = jdatetime.datetime(year, month, day, hour, minute)
                        gregorian_dt = jd.togregorian()
                        return gregorian_dt.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, IndexError):
                pass
        return value


