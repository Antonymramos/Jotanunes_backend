from django.contrib import admin # type: ignore
from .models import UserNotificationConfig

@admin.register(UserNotificationConfig)
class UserNotificationConfigAdmin(admin.ModelAdmin):
    list_display = ("user", "email_enabled", "teams_enabled", "slack_enabled", "updated_at")
    search_fields = ("user__username", "user__email")
