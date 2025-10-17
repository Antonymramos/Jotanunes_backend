from django.db import models
from django.conf import settings

class CustomizacaoTipo(models.TextChoices):
    FORMULA = "FORMULA", "Fórmula Visual"
    SQL = "SQL", "Consulta SQL"
    RELATORIO = "RELATORIO", "Relatório"
    OUTRO = "OUTRO", "Outro"

class CustomizacaoStatus(models.TextChoices):
    ATIVA = "ATIVA", "Ativa"
    OBSOLETA = "OBSOLETA", "Obsoleta"
    EM_REVISAO = "EM_REVISAO", "Em revisão"

class AssinaturaEscopo(models.TextChoices):
    TODOS = "TODOS", "Todos"
    MODULO = "MODULO", "Por Módulo"
    ITEM = "ITEM", "Item Específico"

class AbstractCustomizacao(models.Model):
    nome = models.CharField(max_length=255, db_column="NOME", blank=True, null=True)
    descricao_tecnica = models.TextField(db_column="DESCRICAO", blank=True, null=True)
    criado_no_erp_em = models.DateTimeField(db_column="RECCREATEDON", null=True, blank=True)
    alterado_no_erp_em = models.DateTimeField(db_column="RECMODIFIEDON", null=True, blank=True)
    responsavel = models.CharField(max_length=120, db_column="RECCREATEDBY", blank=True, null=True)
    codcoligada = models.IntegerField(db_column="CODCOLIGADA", null=True, blank=True)

    # Campos para novas colunas
    tipo = models.CharField(max_length=16, choices=CustomizacaoTipo.choices, db_column="tipo", blank=True, null=True)
    status = models.CharField(max_length=16, choices=CustomizacaoStatus.choices, db_column="status", blank=True, null=True)
    versao = models.CharField(max_length=64, db_column="versao", blank=True, null=True)
    responsavel_email = models.EmailField(db_column="responsavel_email", blank=True, null=True)
    modulo = models.CharField(max_length=120, db_column="modulo", blank=True, null=True)
    identificador_erp = models.CharField(max_length=255, db_column="identificador_erp_col", blank=True, null=True)
    conteudo = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.nome or 'Sem nome'} ({self.tipo or 'Sem tipo'})"

class CustomizacaoFV(AbstractCustomizacao):
    id = models.UUIDField(primary_key=True, db_column="ID")
    categoria = models.IntegerField(db_column="IDCATEGORIA", blank=True, null=True)
    ativo = models.BooleanField(db_column="ATIVO", default=True)

    class Meta:
        managed = False
        db_table = "AUD_FV"

class CustomizacaoSQL(AbstractCustomizacao):
    id = models.CharField(primary_key=True, max_length=255, db_column="CODSENTENCA")
    tamanho = models.IntegerField(db_column="TAMANHO", blank=True, null=True)
    aplicacao = models.CharField(max_length=100, db_column="APLICACAO", blank=True, null=True)
    conteudo = models.TextField(db_column="SENTENCA", blank=True, null=True)

    class Meta:
        managed = False
        db_table = "AUD_SQL"

class CustomizacaoReport(AbstractCustomizacao):
    id = models.UUIDField(primary_key=True, db_column="ID")
    codigo = models.CharField(max_length=100, db_column="CODIGO", blank=True, null=True)
    aplicacao = models.CharField(max_length=100, db_column="CODAPLICACAO", blank=True, null=True)
    alterado_por = models.CharField(max_length=120, db_column="USRULTALTERACAO", blank=True, null=True)
    alterado_no_erp_em = models.DateTimeField(db_column="DATAULTALTERACAO", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "AUD_REPORT"

class Customizacao(AbstractCustomizacao):
    class Meta:
        managed = False
        db_table = "AUD_FV"  # Padrão, mas não usada diretamente

    @classmethod
    def get_queryset(cls, tipo=None):
        if tipo == "SQL":
            return CustomizacaoSQL.objects.all()
        elif tipo == "RELATORIO":
            return CustomizacaoReport.objects.all()
        else:
            return CustomizacaoFV.objects.all()

# Outros modelos ajustados
class Dependencia(models.Model):
    id = models.UUIDField(primary_key=True, db_column="ID")
    origem = models.ForeignKey(Customizacao, related_name="dependencias_origem", db_column="ORIGEM_ID", on_delete=models.CASCADE)
    destino = models.ForeignKey(Customizacao, related_name="dependencias_destino", db_column="DESTINO_ID", on_delete=models.CASCADE)
    relacao = models.CharField(max_length=32, db_column="RELACAO", default="DEPENDE_DE")
    observacao = models.CharField(max_length=255, db_column="OBSERVACAO", blank=True, default="")

    class Meta:
        managed = False
        db_table = "customizacoes_dependencia"  # Ajustado para o nome real
        unique_together = ("origem", "destino", "relacao")

class Assinatura(models.Model):
    id = models.UUIDField(primary_key=True, db_column="ID")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, db_column="USUARIO_ID", on_delete=models.CASCADE)
    escopo = models.CharField(max_length=10, db_column="ESCOPO", choices=AssinaturaEscopo.choices)
    modulo = models.CharField(max_length=120, db_column="MODULO", blank=True, default="")
    customizacao = models.ForeignKey(Customizacao, db_column="CUSTOMIZACAO_ID", null=True, blank=True, on_delete=models.CASCADE)
    ativo = models.BooleanField(db_column="ATIVO", default=True)

    class Meta:
        managed = False
        db_table = "ASSINATURA"
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

class Alteracao(models.Model):
    id = models.UUIDField(primary_key=True, db_column="ID")
    customizacao = models.ForeignKey(
        Customizacao, related_name="alteracoes", db_column="CUSTOMIZACAO_ID", on_delete=models.SET_NULL, null=True, blank=True
    )
    acao = models.CharField(max_length=20, db_column="ACAO", choices=AlteracaoAcao.choices)
    ator = models.ForeignKey(settings.AUTH_USER_MODEL, db_column="ATOR_ID", null=True, blank=True, on_delete=models.SET_NULL)
    campos_alterados = models.JSONField(db_column="CAMPOS_ALTERADOS", default=dict, blank=True)
    comentario = models.CharField(max_length=255, db_column="COMENTARIO", blank=True, default="")
    ocorreu_em = models.DateTimeField(db_column="OCORREU_EM", auto_now_add=True)

    class Meta:
        managed = False
        db_table = "ALTERACAO"
        ordering = ["-ocorreu_em"]

class NotificacaoTipo(models.TextChoices):
    NOVO_REGISTRO = "NOVO_REGISTRO", "Novo registro"
    ALTERACAO = "ALTERACAO", "Alteração"

class Notificacao(models.Model):
    id = models.UUIDField(primary_key=True, db_column="ID")
    customizacao = models.ForeignKey(Customizacao, related_name="notificacoes", db_column="CUSTOMIZACAO_ID", on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, db_column="TIPO", choices=NotificacaoTipo.choices)
    mensagem = models.CharField(max_length=255, db_column="MENSAGEM")
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL, db_column="DESTINATARIO_ID", null=True, blank=True, related_name="notificacoes", on_delete=models.CASCADE
    )
    origem = models.ForeignKey(
        settings.AUTH_USER_MODEL, db_column="ORIGEM_ID", null=True, blank=True, related_name="notificacoes_originadas", on_delete=models.SET_NULL
    )
    lida = models.BooleanField(db_column="LIDA", default=False)
    criada_em = models.DateTimeField(db_column="CRIADA_EM", auto_now_add=True)

    class Meta:
        managed = False
        db_table = "DBO_NOTIFICACAO"
        indexes = [
            models.Index(fields=["destinatario", "lida", "-criada_em"]),
        ]