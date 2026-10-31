"""میان‌افزارهای امنیتی پروژه."""


class ContentSecurityPolicyMiddleware:
    """افزودن هدر Content-Security-Policy به پاسخ‌های HTML.

    دارایی‌های سایت (فونت، CSS و JS) همگی از دامنهٔ خود سایت بارگذاری می‌شوند؛
    بنابراین می‌توان منابع خارجی را مسدود کرد تا تزریق اسکریپت بیرونی ممکن نباشد.
    ``unsafe-inline`` فقط برای اسکریپت‌های کوچک اولیه و استایل‌های درون‌خطی لازم است.
    """

    CSP = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "media-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        content_type = response.get('Content-Type', '')
        if content_type.startswith('text/html'):
            response.setdefault('Content-Security-Policy', self.CSP)
        return response
