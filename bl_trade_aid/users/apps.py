from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "bl_trade_aid.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import bl_trade_aid.users.signals  # noqa F401
        except ImportError:
            pass
