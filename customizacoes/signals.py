# customizacoes/signals.py
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from django.db import transaction
from .notifications import dispatch_notification
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.contrib.auth import get_user_model
from ai.models import CustomizacaoEmbedding
from ai.services import embed_text

from .models import (
    Customizacao, Dependencia,
    Alteracao, AlteracaoAcao,
    Notificacao, NotificacaoTipo,
    Assinatura,  # <-- novo modelo (ver models.py)
)
from core.user_context import get_user  # <-- middleware grava o usuário atual

# --- Campos rastreados para diff ---
TRACK_FIELDS = [
    "tipo", "nome", "modulo", "identificador_erp",
    "descricao_tecnica", "conteudo", "status",
    "criado_no_erp_em", "alterado_no_erp_em",
    "versao", "responsavel", "responsavel_email", "is_active",
]

# --- Helper: garantir valores serializáveis em JSON ---
def _jsonable(v):
    if v is None:
        return None
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, (UUID,)):
        return str(v)
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    return v

def _dict_jsonable(d: dict) -> dict:
    return {k: _jsonable(v) for k, v in d.items()}

# --- Controle para deletes em cascata (evita log/alerta num delete em massa) ---
_DELETING_CUSTOMIZACOES = set()

@receiver(pre_delete, sender=Customizacao)
def _mark_customizacao_deleting(sender, instance: Customizacao, **kwargs):
    _DELETING_CUSTOMIZACOES.add(instance.pk)

@receiver(post_delete, sender=Customizacao)
def _unmark_customizacao_deleting(sender, instance: Customizacao, **kwargs):
    _DELETING_CUSTOMIZACOES.discard(instance.pk)

# --- Snapshot antes de salvar ---
@receiver(pre_save, sender=Customizacao)
def snapshot_before(sender, instance: Customizacao, **kwargs):
    if instance.pk:
        try:
            antigo = sender.objects.get(pk=instance.pk)
            snap = model_to_dict(antigo, fields=TRACK_FIELDS)
            instance._old_snapshot = _dict_jsonable(snap)
        except sender.DoesNotExist:
            instance._old_snapshot = None
    else:
        instance._old_snapshot = None

# --- Resolve assinantes para uma customização (remove o próprio autor) ---
def _assinantes_para(custom: Customizacao, actor):
    users = set()
    for sub in Assinatura.objects.filter(ativo=True).select_related("usuario"):
        if sub.escopo == Assinatura.Escopo.TODOS:
            users.add(sub.usuario_id)
        elif sub.escopo == Assinatura.Escopo.MODULO and sub.modulo == custom.modulo:
            users.add(sub.usuario_id)
        elif sub.escopo == Assinatura.Escopo.ITEM and sub.customizacao_id == custom.id:
            users.add(sub.usuario_id)
    if actor:
        users.discard(actor.id)
    return list(users)

# --- Auditoria / Notificação após salvar ---
@receiver(post_save, sender=Customizacao)
def auditoria_customizacao(sender, instance: Customizacao, created, **kwargs):
    actor = get_user()  # pode ser None (admin não autenticado via middleware)

    if created:
        # log
        Alteracao.objects.create(
            customizacao=instance,
            acao=AlteracaoAcao.CRIACAO,
            ator=actor,
            campos_alterados={},
        )
        # notificações
        msg = f"Nova customização: {instance.nome}"
        destinatarios_ids = _assinantes_para(instance, actor)
        if destinatarios_ids:
            User = get_user_model()
            destinatarios = list(User.objects.filter(id__in=destinatarios_ids))
            Notificacao.objects.bulk_create([
                Notificacao(customizacao=instance, tipo=NotificacaoTipo.NOVO_REGISTRO,
                            mensagem=msg, destinatario=u, origem=actor)
                for u in destinatarios
            ])
        else:
            # broadcast genérica
            Notificacao.objects.create(customizacao=instance, tipo=NotificacaoTipo.NOVO_REGISTRO,
                                       mensagem=msg, origem=actor)
        return

    # UPDATE
    before = getattr(instance, "_old_snapshot", None)
    after = _dict_jsonable(model_to_dict(instance, fields=TRACK_FIELDS))

    changes = {}
    if before:
        for f in TRACK_FIELDS:
            if before.get(f) != after.get(f):
                changes[f] = [before.get(f), after.get(f)]

    Alteracao.objects.create(
        customizacao=instance,
        acao=AlteracaoAcao.ATUALIZACAO,
        ator=actor,
        campos_alterados=changes,
    )

    msg = f"Customização alterada: {instance.nome}"
    destinatarios_ids = _assinantes_para(instance, actor)
    if destinatarios_ids:
        User = get_user_model()
        destinatarios = list(User.objects.filter(id__in=destinatarios_ids))
        Notificacao.objects.bulk_create([
            Notificacao(customizacao=instance, tipo=NotificacaoTipo.ALTERACAO,
                        mensagem=msg, destinatario=u, origem=actor)
            for u in destinatarios
        ])
    else:
        Notificacao.objects.create(customizacao=instance, tipo=NotificacaoTipo.ALTERACAO,
                                   mensagem=msg, origem=actor)

    if hasattr(instance, "_old_snapshot"):
        delattr(instance, "_old_snapshot")

# --- Logs de Dependencia (com proteção p/ delete em cascata) ---
@receiver(post_save, sender=Dependencia)
def log_dependencia_save(sender, instance: Dependencia, created, **kwargs):
    if instance.origem_id in _DELETING_CUSTOMIZACOES:
        return
    Alteracao.objects.create(
        customizacao=instance.origem,
        acao=AlteracaoAcao.DEPENDENCIA,
        ator=get_user(),
        campos_alterados={
            "destino": str(instance.destino),
            "relacao": instance.relacao,
            "created": bool(created),
        },
    )

@receiver(post_delete, sender=Dependencia)
def log_dependencia_delete(sender, instance: Dependencia, **kwargs):
    if instance.origem_id in _DELETING_CUSTOMIZACOES:
        return
    Alteracao.objects.create(
        customizacao=instance.origem,
        acao=AlteracaoAcao.DEPENDENCIA,
        ator=get_user(),
        campos_alterados={
            "destino": str(instance.destino),
            "relacao": instance.relacao,
            "deleted": True,
        },
    )
@receiver(post_save, sender=Notificacao)
def deliver_notification(sender, instance, created, **kwargs):
    if not created or instance.destinatario_id is None:
        return
    transaction.on_commit(lambda: dispatch_notification(instance))
@receiver(post_save, sender=Customizacao)
def _update_customizacao_embedding(sender, instance: Customizacao, created, **kwargs):
    try:
        blob = "\n".join(filter(None, [
            instance.nome,
            instance.modulo,
            instance.identificador_erp,
            instance.descricao_tecnica,
            instance.conteudo,
        ]))
        vec = embed_text(blob)
        CustomizacaoEmbedding.objects.update_or_create(
            customizacao=instance, defaults={"vec": vec}
        )
    except Exception as e:
        # não falha o fluxo de save; só loga
        print("embedding error:", e)    