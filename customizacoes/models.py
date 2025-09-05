from django.conf import settings
from django.db import models
from core.models import BaseModel
from django.core.serializers.json import DjangoJSONEncoder


class CustomizacaoTipo(models.TextChoices):
    FORMULA = "FORMULA", "Fórmula Visual"
    SQL = "SQL", "Consulta SQL"
    RELATORIO = "RELATORIO", "Relatório"
    OUTRO = "OUTRO", "Outro"


class CustomizacaoStatus(models.TextChoices):
    ATIVA = "ATIVA", "Ativa"
    OBSOLETA = "OBSOLETA", "Obsoleta"
    EM_REVISAO = "EM_REVISAO", "Em revisão"


class Customizacao(BaseModel):
    tipo = models.CharField(max_length=16, choices=CustomizacaoTipo.choices)
    nome = models.CharField(max_length=255, db_index=True)
    modulo = models.CharField(max_length=120, blank=True, default="", db_index=True)
    identificador_erp = models.CharField(max_length=255, blank=True, default="", db_index=True)
    descricao_tecnica = models.TextField(blank=True, default="")   # documentação
    conteudo = models.TextField(blank=True, default="")            # trecho de código/expressão
    status = models.CharField(max_length=16, choices=CustomizacaoStatus.choices, default=CustomizacaoStatus.ATIVA)

    criado_no_erp_em = models.DateTimeField(null=True, blank=True)
    alterado_no_erp_em = models.DateTimeField(null=True, blank=True)
    versao = models.CharField(max_length=64, blank=True, default="")

    # autoria
    responsavel = models.CharField(max_length=120, blank=True, default="")
    responsavel_email = models.EmailField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["tipo", "modulo", "status"]),
        ]
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.tipo})"


class Dependencia(BaseModel):
    origem = models.ForeignKey(Customizacao, related_name="dependencias_origem", on_delete=models.CASCADE)
    destino = models.ForeignKey(Customizacao, related_name="dependencias_destino", on_delete=models.CASCADE)
    relacao = models.CharField(max_length=32, default="DEPENDE_DE") 
    observacao = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        unique_together = ("origem", "destino", "relacao")
class Assinatura(models.Model):
    class Escopo(models.TextChoices):
        TODOS = "TODOS", "Todos"
        MODULO = "MODULO", "Por Módulo"
        ITEM = "ITEM", "Item Específico"

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    escopo = models.CharField(max_length=10, choices=Escopo.choices)
    modulo = models.CharField(max_length=120, blank=True, default="")
    customizacao = models.ForeignKey(Customizacao, null=True, blank=True, on_delete=models.CASCADE)
    ativo = models.BooleanField(default=True)

    class Meta:
        unique_together = (("usuario", "escopo", "modulo", "customizacao"),)

    def __str__(self):
        alvo = "todos" if self.escopo == "TODOS" else (self.modulo or self.customizacao_id)
        return f"{self.usuario} -> {self.escopo} ({alvo})"


class AlteracaoAcao(models.TextChoices):
    CRIACAO = "CRIACAO", "Criação"
    ATUALIZACAO = "ATUALIZACAO", "Atualização"
    EXCLUSAO = "EXCLUSAO", "Exclusão"
    STATUS = "STATUS", "Mudança de status"
    DEPENDENCIA = "DEPENDENCIA", "Alteração em dependências"


class Alteracao(BaseModel):
    customizacao = models.ForeignKey(
        Customizacao,
        related_name="alteracoes",
        on_delete=models.SET_NULL,
        null=True, blank= True
    )
    acao = models.CharField(max_length=20, choices=AlteracaoAcao.choices)
    ator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    campos_alterados = models.JSONField(default=dict, blank=True)
    comentario = models.CharField(max_length=255, blank=True, default="")
    ocorreu_em = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ["-ocorreu_em"]


class NotificacaoTipo(models.TextChoices):
    NOVO_REGISTRO = "NOVO_REGISTRO", "Novo registro"
    ALTERACAO = "ALTERACAO", "Alteração"


class Notificacao(BaseModel):
    customizacao = models.ForeignKey(Customizacao, related_name="notificacoes", on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=NotificacaoTipo.choices)
    mensagem = models.CharField(max_length=255)

    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name="notificacoes", on_delete=models.CASCADE
    )
    origem = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name="notificacoes_originadas", on_delete=models.SET_NULL
    )

    lida = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["destinatario", "lida", "-criada_em"]),
        ]
