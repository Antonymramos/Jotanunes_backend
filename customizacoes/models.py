# customizacoes/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


# === TABELAS LEGADAS (NÃO GERENCIADAS) ===
class CustomizacaoFV(models.Model):
    id = models.IntegerField(primary_key=True, db_column="ID")
    codcoligada = models.IntegerField(db_column="CODCOLIGADA", null=True)
    nome = models.CharField(max_length=255, db_column="NOME", blank=True, null=True)
    descricao = models.TextField(db_column="DESCRICAO", blank=True, null=True)
    idcategoria = models.IntegerField(db_column="IDCATEGORIA", null=True)
    ativo = models.BooleanField(db_column="ATIVO", default=True)
    reccreatedby = models.CharField(max_length=100, db_column="RECCREATEDBY", blank=True, null=True)
    reccreatedon = models.DateTimeField(db_column="RECCREATEDON", null=True)
    recmodifiedby = models.CharField(max_length=100, db_column="RECMODIFIEDBY", blank=True, null=True)
    recmodifiedon = models.DateTimeField(db_column="RECMODIFIEDON", null=True)

    class Meta:
        managed = False
        db_table = "AUD_FV"

    def __str__(self):
        return f"FV {self.id}: {self.nome or 'Sem nome'}"


class CustomizacaoSQL(models.Model):
    id = models.CharField(primary_key=True, max_length=100, db_column="CODSENTENCA")  # STRING
    codcoligada = models.IntegerField(db_column="CODCOLIGADA", null=True)
    aplicacao = models.CharField(max_length=100, db_column="APLICACAO", blank=True, null=True)
    titulo = models.CharField(max_length=255, db_column="TITULO", blank=True, null=True)
    sentenca = models.TextField(db_column="SENTENCA", blank=True, null=True)
    tamanho = models.IntegerField(db_column="TAMANHO", null=True)
    reccreatedby = models.CharField(max_length=100, db_column="RECCREATEDBY", blank=True, null=True)
    reccreatedon = models.DateTimeField(db_column="RECCREATEDON", null=True)
    recmodifiedby = models.CharField(max_length=100, db_column="RECMODIFIEDBY", blank=True, null=True)
    recmodifiedon = models.DateTimeField(db_column="RECMODIFIEDON", null=True)

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
    reccreatedby = models.CharField(max_length=100, db_column="RECCREATEDBY", blank=True, null=True)
    reccreatedon = models.DateTimeField(db_column="RECCREATEDON", null=True)
    recmodifiedby = models.CharField(max_length=100, db_column="RECMODIFIEDBY", blank=True, null=True)
    recmodifiedon = models.DateTimeField(db_column="RECMODIFIEDON", null=True)

    class Meta:
        managed = False
        db_table = "AUD_REPORT"

    def __str__(self):
        return f"REP {self.id}: {self.codigo or 'Sem código'}"


# === TABELAS NOVAS ===
class Observacao(models.Model):
    texto = models.TextField(db_column="texto")
    data = models.DateTimeField(auto_now_add=True, db_column="data")
    criado_por = models.IntegerField(null=True, blank=True, db_column="criado_por")

    class Meta:
        managed = True
        db_table = "Observacao"

    def __str__(self):
        return f"Obs {self.id}: {self.texto[:30]}"


class Prioridade(models.Model):
    nivel = models.CharField(max_length=50, db_column="nivel")

    class Meta:
        managed = True
        db_table = "Prioridade"

    def __str__(self):
        return self.nivel


class CadastroDependencias(models.Model):
    id_aud_sql = models.CharField(max_length=100, null=True, blank=True, db_column="id_aud_sql")  # STRING
    id_aud_report = models.IntegerField(null=True, blank=True, db_column="id_aud_report")
    id_aud_fv = models.IntegerField(null=True, blank=True, db_column="id_aud_fv")
    id_observacao = models.IntegerField(null=True, blank=True, db_column="id_observacao")
    id_prioridade = models.IntegerField(null=True, blank=True, db_column="id_prioridade")
    data_criacao = models.DateTimeField(auto_now_add=True, db_column="data_criacao")
    criado_por = models.IntegerField(null=True, blank=True, db_column="criado_por")

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
        return f"Dep {self.id}: {self.get_origem_display()} → {self.get_destino_display()}"

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
        if self.id_aud_sql and self.id_aud_report and self.id_aud_fv: return "Nenhum destino"
        if self.id_aud_report: return f"REP {self.id_aud_report}: {self.aud_report.codigo if self.aud_report else 'N/D'}"
        if self.id_aud_fv: return f"FV {self.id_aud_fv}: {self.aud_fv.nome if self.aud_fv else 'N/D'}"
        if self.id_aud_sql: return f"SQL {self.id_aud_sql}: {self.aud_sql.titulo if self.aud_sql else 'N/D'}"
        return "Nenhuma"

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
    id_usuario = models.IntegerField(db_column="id_usuario")

    class Meta:
        managed = True
        db_table = "NOTIFICACAO"

    def __str__(self):
        return f"{self.titulo} - ID {self.id_usuario}"