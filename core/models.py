import uuid
from django.conf import settings
from django.db import models

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class BaseModel(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)
    class Meta:
        abstract = True

class ActorMixin(models.Model):
    # opcional: para logs/alterações
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="%(class)s_created",
        null=True, blank=True, on_delete=models.SET_NULL
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="%(class)s_updated",
        null=True, blank=True, on_delete=models.SET_NULL
    )
    class Meta:
        abstract = True
