from django.conf import settings
from django.db import models

class UserNotificationConfig(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notify_config",
    )

    # canais
    email_enabled = models.BooleanField(default=True)
    teams_enabled = models.BooleanField(default=False)
    slack_enabled = models.BooleanField(default=False)

    # webhooks (opcionais)
    teams_webhook_url = models.URLField(blank=True, default="")
    slack_webhook_url = models.URLField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notificações de {self.user}"
