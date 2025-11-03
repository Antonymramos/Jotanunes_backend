# customizacoes/models.py
from django.db import models
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

    class Meta:
        managed = False
        db_table = "AUD_FV"

    def __str__(self):
        return f"FV {self.id}: {self.nome or 'Sem nome'}"


class CustomizacaoSQL(models.Model):
    codsentenca = models.CharField(primary_key=True, max_length=100, db_column="CODSENTENCA")
    codcoligada = models.IntegerField(db_column="CODCOLIGADA", null=True)
    aplicacao = models.CharField(max_length=100, db_column="APLICACAO", blank=True, null=True)
    titulo = models.CharField(max_length=255, db_column="TITULO", blank=True, null=True)
    sentenca = models.TextField(db_column="SENTENCA", blank=True, null=True)
    tamanho = models.IntegerField(db_column="TAMANHO", null=True)
    reccreatedby = models.CharField(max_length=100, db_column="RECCREATEDBY", blank=True, null=True)
    reccreatedon = models.DateTimeField(db_column="RECCREATEDON", null=True)

    class Meta:
        managed = False
        db_table = "AUD_SQL"

    def __str__(self):
        return f"SQL {self.codsentenca}: {self.titulo or 'Sem título'}"


class CustomizacaoReport(models.Model):
    id = models.IntegerField(primary_key=True, db_column="ID")
    codcoligada = models.IntegerField(db_column="CODCOLIGADA", null=True)
    codaplicacao = models.IntegerField(db_column="CODAPLICACAO", null=True)
    codigo = models.CharField(max_length=100, db_column="CODIGO", blank=True, null=True)
    descricao = models.TextField(db_column="DESCRICAO", blank=True, null=True)
    reccreatedby = models.CharField(max_length=100, db_column="RECCREATEDBY", blank=True, null=True)
    reccreatedon = models.DateTimeField(db_column="RECCREATEDON", null=True)

    class Meta:
        managed = False
        db_table = "AUD_REPORT"

    def __str__(self):
        return f"REP {self.id}: {self.codigo or 'Sem código'}"


# === TABELAS NOVAS ===
class Prioridade(models.Model):
    nivel = models.CharField(max_length=50, db_column="nivel")

    class Meta:
        managed = True
        db_table = "Prioridade"

    def __str__(self):
        return self.nivel


class CadastroDependencias(models.Model):
    id_aud_sql = models.CharField(max_length=100, null=True, blank=True, db_column="id_aud_sql")
    id_aud_report = models.IntegerField(null=True, blank=True, db_column="id_aud_report")
    id_aud_fv = models.IntegerField(null=True, blank=True, db_column="id_aud_fv")
    id_prioridade = models.IntegerField(null=True, blank=True, db_column="id_prioridade")
    data_criacao = models.DateTimeField(auto_now_add=True, db_column="data_criacao")
    criado_por = models.CharField(max_length=100, db_column="criado_por")

    class Meta:
        managed = True
        db_table = "Cadastro_Dependencias"

    def __str__(self):
        partes = []
        if self.id_aud_sql: partes.append(f"SQL:{self.id_aud_sql}")
        if self.id_aud_report: partes.append(f"REP:{self.id_aud_report}")
        if self.id_aud_fv: partes.append(f"FV:{self.id_aud_fv}")
        return " → ".join(partes)

    def clean(self):
        preenchidos = sum(1 for x in [self.id_aud_sql, self.id_aud_report, self.id_aud_fv] if x is not None)
        if preenchidos != 2:
            raise ValidationError("Selecione exatamente 1 origem e 1 destino.")
        if not self.criado_por:
            raise ValidationError("Usuário criador é obrigatório.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Notificacao(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    prioridade = models.CharField(max_length=10)
    data_hora = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)
    id_usuario = models.CharField(max_length=150, db_column="id_usuario")

    class Meta:
        managed = True
        db_table = "NOTIFICACAO"