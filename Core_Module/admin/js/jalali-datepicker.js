/**
 * Persian (Jalali) Date Picker for Django Admin
 * 
 * This script initializes Persian date pickers on Django admin forms.
 * It uses the persian-datepicker library from CDN.
 */

(function($) {
    'use strict';
    
    // Persian month names
    var persianMonths = [
        'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
        'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
    ];
    
    // English month names mapping
    var englishMonths = [
        'Farvardin', 'Ordibehesht', 'Khordad', 'Tir', 
        'Mordad', 'Shahrivar', 'Mehr', 'Aban', 
        'Azar', 'Dey', 'Bahman', 'Esfand'
    ];
    
    // Initialize on document ready
    $(document).ready(function() {
        // Initialize for all Jalali date picker fields
        $('.jalali-date-picker').each(function() {
            var $input = $(this);
            
            // Skip if already initialized
            if ($input.data('datepicker-initialized')) {
                return;
            }
            
            $input.persianDatepicker({
                format: 'YYYY/MM/DD',
                viewMode: 'year',
                initialValue: false,
                minDate: new persianDate(1400, 1, 1),
                maxDate: new persianDate(1450, 12, 29),
                autoClose: true,
                persianNumber: true,
                theme: 'default',
                alwaysShow: false,
                toolbox: {
                    calendarSwitch: {
                        enabled: true,
                        text: {
                            fa: 'تقویم',
                            en: 'Calendar'
                        }
                    }
                },
                calendar: {
                    persian: {
                        locale: 'fa',
                        showHint: true,
                        leapYearMode: 'algorithmic'
                    },
                    gregorian: {
                        locale: 'en',
                        showHint: false
                    }
                },
                onSelect: function(unix) {
                    // Convert to Persian date string
                    var pd = new persianDate(unix);
                    var persianDateStr = pd.year() + '/' + 
                                         pd.month().toString().padStart(2, '0') + '/' + 
                                         pd.date().toString().padStart(2, '0');
                    $input.val(persianDateStr);
                    
                    // Trigger change event for Django
                    $input.trigger('change');
                }
            });
            
            $input.data('datepicker-initialized', true);
        });
        
        // Initialize for all Jalali datetime picker fields
        $('.jalali-datetime-picker').each(function() {
            var $input = $(this);
            
            // Skip if already initialized
            if ($input.data('datepicker-initialized')) {
                return;
            }
            
            $input.persianDatepicker({
                format: 'YYYY/MM/DD HH:mm',
                viewMode: 'year',
                initialValue: false,
                minDate: new persianDate(1400, 1, 1),
                maxDate: new persianDate(1450, 12, 29),
                autoClose: true,
                persianNumber: true,
                timePicker: {
                    enabled: true,
                    hour: {
                        visible: true,
                        format: 24,
                        step: 1
                    },
                    minute: {
                        visible: true,
                        format: 60,
                        step: 1
                    }
                },
                theme: 'default',
                calendar: {
                    persian: {
                        locale: 'fa',
                        showHint: true
                    },
                    gregorian: {
                        locale: 'en',
                        showHint: false
                    }
                },
                onSelect: function(unix) {
                    var pd = new persianDate(unix);
                    var hour = pd.hour().toString().padStart(2, '0');
                    var minute = pd.minute().toString().padStart(2, '0');
                    var persianDateStr = pd.year() + '/' + 
                                         pd.month().toString().padStart(2, '0') + '/' + 
                                         pd.date().toString().padStart(2, '0') + ' ' +
                                         hour + ':' + minute;
                    $input.val(persianDateStr);
                    $input.trigger('change');
                }
            });
            
            $input.data('datepicker-initialized', true);
        });
    });
    
    // Initialize when Django adds new forms dynamically
    if (typeof django !== 'undefined' && django.jQuery) {
        django.jQuery(document).on('formset:added', function(event, $row) {
            // Re-initialize datepickers in new formset rows
            $row.find('.jalali-date-picker, .jalali-datetime-picker').each(function() {
                var $input = django.jQuery(this);
                if (!$input.data('datepicker-initialized')) {
                    $input.removeData('datepicker-initialized');
                    $input.trigger('initialize-datepicker');
                }
            });
        });
        
        // Listen for the initialize event
        $(document).on('initialize-datepicker', function() {
            $('.jalali-date-picker:not([data-datepicker-initialized])').each(function() {
                var $input = $(this);
                // Similar initialization as above
            });
        });
    }
    
})(jQuery);
