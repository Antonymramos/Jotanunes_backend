from django.contrib.auth import get_user_model
from users.models import UserNotificationConfig
from customizacoes.models import Assinatura

User = get_user_model()
for u in User.objects.all():
    UserNotificationConfig.objects.get_or_create(user=u)
    Assinatura.objects.get_or_create(usuario=u, escopo=Assinatura.Escopo.TODOS, defaults={"ativo": True})
print("OK")
exit()
