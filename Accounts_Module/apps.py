from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Accounts_Module'
    verbose_name = 'ماژول کاربران'

    def ready(self):
        import Accounts_Module.signals  # noqa: F401
