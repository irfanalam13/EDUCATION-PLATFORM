from django.apps import AppConfig


class BillingConfig(AppConfig):
    name = "apps.billing"

    def ready(self):
        # Wire post_save signal that seeds Free-tier feature access for new users.
        from . import signals  # noqa: F401
