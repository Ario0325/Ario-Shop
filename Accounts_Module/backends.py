"""
بک‌اند احراز هویت - امکان ورود با نام کاربری یا ایمیل
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """ورود با نام کاربری یا آدرس ایمیل"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        if '@' in username:
            kwargs = {'email': username}
        else:
            kwargs = {'username': username}
        try:
            user = User.objects.get(**kwargs)
        except User.DoesNotExist:
            User().set_password(password)  # محدود کردن زمان حمله
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
