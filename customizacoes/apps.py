from django.apps import AppConfig

class CustomizacoesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "customizacoes"
    verbose_name = "Customizações"

    def ready(self):
        from . import signals
