
import logging
from django.conf import settings
from django.core.mail import send_mail

from .models import Notificacao, NotificacaoTipo

log = logging.getLogger(__name__)

def _subject(n: Notificacao) -> str:
    tipo = dict(NotificacaoTipo.choices).get(n.tipo, n.tipo)
    return f"[RM] {tipo} • {n.customizacao.nome}"

def _body(n: Notificacao) -> str:
    autor = getattr(n.origem, "username", "sistema")
    return (
        f"{n.mensagem}\n\n"
        f"Customização: {n.customizacao.nome} ({n.customizacao.tipo})\n"
        f"Autor: {autor}\n"
        f"Status: {n.customizacao.status} | Versão: {n.customizacao.versao}\n"
    )

def _send_webhook(url: str, payload: dict) -> bool:
    try:
        import requests  # lazy import
    except Exception:
        log.warning("Pacote 'requests' não instalado. pip install requests")
        return False
    try:
        requests.post(url, json=payload, timeout=6)
        return True
    except Exception:
        log.exception("Falha ao enviar webhook")
        return False

def notify_email(n: Notificacao) -> bool:
    dest = getattr(n.destinatario, "email", "") if n.destinatario else ""
    if not dest or not getattr(settings, "EMAIL_HOST", None):
        return False
    try:
        send_mail(
            subject=_subject(n),
            message=_body(n),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@localhost"),
            recipient_list=[dest],
            fail_silently=False,
        )
        return True
    except Exception:
        log.exception("Falha ao enviar e-mail")
        return False

def notify_slack(n: Notificacao) -> bool:
    cfg = getattr(n.destinatario, "notify_config", None)
    if not cfg or not (cfg.slack_enabled and cfg.slack_webhook_url):
        return False
    return _send_webhook(cfg.slack_webhook_url, {"text": f":bell: {_subject(n)}\n{_body(n)}"})

def notify_teams(n: Notificacao) -> bool:
    cfg = getattr(n.destinatario, "notify_config", None)
    if not cfg or not (cfg.teams_enabled and cfg.teams_webhook_url):
        return False
    # Teams webhooks aceitam payload simples {text: "..."}
    return _send_webhook(cfg.teams_webhook_url, {"text": f"🔔 {_subject(n)}\n{_body(n)}"})

def dispatch_notification(n: Notificacao) -> None:
    """
    Envia pelos canais habilitados do destinatário.
    Silencioso em caso de falha (log apenas).
    """
    if not n.destinatario_id:
        return
    cfg = getattr(n.destinatario, "notify_config", None)
    if not cfg:
        return

    sent_email = cfg.email_enabled and notify_email(n)
    sent_slack = notify_slack(n)
    sent_teams = notify_teams(n)
    log.debug("Notificação %s entregue - email=%s slack=%s teams=%s", n.id, sent_email, sent_slack, sent_teams)
