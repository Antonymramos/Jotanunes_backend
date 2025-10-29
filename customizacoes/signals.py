# customizacoes/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from ai.models import CustomizacaoEmbedding
from ai.services import embed_text
from .models import CustomizacaoFV, CustomizacaoSQL, CustomizacaoReport

@receiver(post_save)
def update_embedding(sender, instance, created, **kwargs):
    if sender not in {CustomizacaoFV, CustomizacaoSQL, CustomizacaoReport}:
        return

    try:
        texts = [
            getattr(instance, 'nome', ''),
            getattr(instance, 'modulo', ''),
            getattr(instance, 'identificador_erp', ''),
            getattr(instance, 'descricao_tecnica', ''),
            getattr(instance, 'conteudo', ''),
        ]
        blob = "\n".join(filter(str.strip, texts))
        if not blob:
            return

        vec = embed_text(blob)
        tipo_map = {CustomizacaoFV: "FV", CustomizacaoSQL: "SQL", CustomizacaoReport: "REPORT"}
        tipo = tipo_map[sender]

        CustomizacaoEmbedding.objects.update_or_create(
            tipo=tipo,
            customizacao_id=instance.id,
            defaults={"vec": vec}
        )
    except Exception as e:
        print(f"[EMBEDDING ERROR] {sender.__name__} {instance.id}: {e}")