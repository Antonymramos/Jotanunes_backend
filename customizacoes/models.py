# customizacoes/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_column="data_criacao")
    class Meta:
        abstract = True


class ActorMixin(models.Model):
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column="criado_por",
        related_name="%(class)s_criado"
    )
    class Meta:
        abstract = True


# === TABELAS LEGADAS (NÃO GERENCIADAS) ===
class CustomizacaoFV(models.Model):
    id = models.IntegerField(primary_key=True, db_column="ID")
    codcoligada = models.IntegerField(db_column="CODCOLIGADA", null=True)
    nome = models.CharField(max_length=255, db_column="NOME", blank=True, null=True)
    descricao = models.TextField(db_column="DESCRICAO", blank=True, null=True)
    idcategoria = models.IntegerField(db_column="IDCATEGORIA", null=True)
    ativo = models.BooleanField(db_column="ATIVO", default=True)

    class Meta:
        managed = False
        db_table = "AUD_FV"

    def __str__(self):
        return f"FV {self.id}: {self.nome or 'Sem nome'}"


class CustomizacaoSQL(models.Model):
    id = models.IntegerField(primary_key=True, db_column="CODSENTENCA")
    codcoligada = models.IntegerField(db_column="CODCOLIGADA", null=True)
    aplicacao = models.CharField(max_length=100, db_column="APLICACAO", blank=True, null=True)
    titulo = models.CharField(max_length=255, db_column="TITULO", blank=True, null=True)
    sentenca = models.TextField(db_column="SENTENCA", blank=True, null=True)

    class Meta:
        managed = False
        db_table = "AUD_SQL"

    def __str__(self):
        return f"SQL {self.id}: {self.titulo or 'Sem título'}"


class CustomizacaoReport(models.Model):
    id = models.IntegerField(primary_key=True, db_column="ID")
    codcoligada = models.IntegerField(db_column="CODCOLIGADA", null=True)
    codaplicacao = models.IntegerField(db_column="CODAPLICACAO", null=True)
    codigo = models.CharField(max_length=100, db_column="CODIGO", blank=True, null=True)
    descricao = models.TextField(db_column="DESCRICAO", blank=True, null=True)

    class Meta:
        managed = False
        db_table = "AUD_REPORT"

    def __str__(self):
        return f"REP {self.id}: {self.codigo or 'Sem código'}"


# === TABELAS NOVAS ===
class Observacao(TimeStampedModel, ActorMixin):
    texto = models.TextField(db_column="texto")
    data = models.DateTimeField(auto_now_add=True, db_column="data")

    class Meta:
        managed = True
        db_table = "Observacao"

    def __str__(self):
        return f"Obs {self.id}: {self.texto[:30]}"


class Prioridade(models.Model):
    nivel = models.CharField(max_length=50, unique=True, db_column="nivel")

    class Meta:
        managed = True
        db_table = "Prioridade"

    def __str__(self):
        return self.nivel


class CadastroDependencias(TimeStampedModel, ActorMixin):
    id_aud_sql = models.IntegerField(null=True, blank=True, db_column="id_aud_sql")
    id_aud_report = models.IntegerField(null=True, blank=True, db_column="id_aud_report")
    id_aud_fv = models.IntegerField(null=True, blank=True, db_column="id_aud_fv")
    id_observacao = models.ForeignKey(Observacao, on_delete=models.SET_NULL, null=True, blank=True, db_column="id_observacao")
    id_prioridade = models.ForeignKey(Prioridade, on_delete=models.SET_NULL, null=True, blank=True, db_column="id_prioridade")

    class Meta:
        managed = True
        db_table = "Cadastro_Dependencias"
        constraints = [
            models.UniqueConstraint(
                fields=['id_aud_sql', 'id_aud_report', 'id_aud_fv'],
                name='unique_dependencia_par',
                condition=models.Q(
                    models.Q(id_aud_sql__isnull=False) |
                    models.Q(id_aud_report__isnull=False) |
                    models.Q(id_aud_fv__isnull=False)
                )
            )
        ]

    def __str__(self):
        return f"{self.get_origem_display()} → {self.get_destino_display()}"

    @property
    def aud_sql(self): return CustomizacaoSQL.objects.filter(id=self.id_aud_sql).first() if self.id_aud_sql else None
    @property
    def aud_report(self): return CustomizacaoReport.objects.filter(id=self.id_aud_report).first() if self.id_aud_report else None
    @property
    def aud_fv(self): return CustomizacaoFV.objects.filter(id=self.id_aud_fv).first() if self.id_aud_fv else None

    def get_origem_display(self):
        if self.id_aud_sql: return f"SQL {self.id_aud_sql}: {self.aud_sql.titulo if self.aud_sql else 'N/D'}"
        if self.id_aud_report: return f"REP {self.id_aud_report}: {self.aud_report.codigo if self.aud_report else 'N/D'}"
        if self.id_aud_fv: return f"FV {self.id_aud_fv}: {self.aud_fv.nome if self.aud_fv else 'N/D'}"
        return "Nenhuma"

    def get_destino_display(self):
        preenchidos = [self.id_aud_sql, self.id_aud_report, self.id_aud_fv]
        count = sum(1 for x in preenchidos if x is not None)
        if count != 2: return "Inválido"
        if self.id_aud_report: return f"REP {self.id_aud_report}: {self.aud_report.codigo if self.aud_report else 'N/D'}"
        if self.id_aud_fv: return f"FV {self.id_aud_fv}: {self.aud_fv.nome if self.aud_fv else 'N/D'}"
        if self.id_aud_sql: return f"SQL {self.id_aud_sql}: {self.aud_sql.titulo if self.aud_sql else 'N/D'}"
        return "Nenhum"

    def clean(self):
        preenchidos = sum(1 for x in [self.id_aud_sql, self.id_aud_report, self.id_aud_fv] if x is not None)
        if preenchidos != 2:
            raise ValidationError("Exatamente 1 origem + 1 destino devem ser preenchidos.")

        if self.id_aud_sql and not CustomizacaoSQL.objects.filter(id=self.id_aud_sql).exists():
            raise ValidationError("SQL não encontrada.")
        if self.id_aud_report and not CustomizacaoReport.objects.filter(id=self.id_aud_report).exists():
            raise ValidationError("Relatório não encontrado.")
        if self.id_aud_fv and not CustomizacaoFV.objects.filter(id=self.id_aud_fv).exists():
            raise ValidationError("Fórmula Visual não encontrada.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Notificacao(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    prioridade = models.CharField(max_length=10)
    data_hora = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customizacoes_notificacoes'
    )

    class Meta:
        managed = True
        db_table = "NOTIFICACAO"

    def __str__(self):
        return f"{self.titulo} - {self.id_usuario.username}"