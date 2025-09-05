from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserNotificationConfig

User = get_user_model()

@receiver(post_save, sender=User)
def create_defaults_for_user(sender, instance, created, **kwargs):
    if not created:
        return
    # cria config de notificações (e-mail ON por padrão)
    UserNotificationConfig.objects.get_or_create(user=instance)

    # cria assinatura "TODOS" para o usuário novo
    from customizacoes.models import Assinatura
    Assinatura.objects.get_or_create(
        usuario=instance,
        escopo=Assinatura.Escopo.TODOS,
        defaults={"ativo": True},
    )
