# customizacoes/models.py
from django.db import models
from django.conf import settings


# ==============================
# ENUMS
# ==============================

class CustomizacaoTipo(models.TextChoices):
    FORMULA = "FORMULA", "Fórmula Visual"
    SQL = "SQL", "Consulta SQL"
    RELATORIO = "RELATORIO", "Relatório"
    OUTRO = "OUTRO", "Outro"

class CustomizacaoStatus(models.TextChoices):
    ATIVA = "ATIVA", "Ativa"
    OBSOLETA = "OBSOLETA", "Obsoleta"
    EM_REVISAO = "EM_REVISAO", "Em revisão"


# ==============================
# MODELOS BASE
# ==============================

class AbstractCustomizacao(models.Model):
    nome = models.CharField(max_length=255, db_column="NOME", blank=True, null=True)
    descricao_tecnica = models.TextField(db_column="DESCRICAO", blank=True, null=True)
    criado_no_erp_em = models.DateTimeField(db_column="RECCREATEDON", null=True, blank=True)
    alterado_no_erp_em = models.DateTimeField(db_column="RECMODIFIEDON", null=True, blank=True)
    responsavel = models.CharField(max_length=120, db_column="RECCREATEDBY", blank=True, null=True)
    codcoligada = models.IntegerField(db_column="CODCOLIGADA", null=True, blank=True)

    tipo = models.CharField(max_length=16, choices=CustomizacaoTipo.choices, blank=True, null=True)
    status = models.CharField(max_length=16, choices=CustomizacaoStatus.choices, blank=True, null=True)
    versao = models.CharField(max_length=64, blank=True, null=True)
    responsavel_email = models.EmailField(blank=True, null=True)
    modulo = models.CharField(max_length=120, blank=True, null=True)
    identificador_erp = models.CharField(max_length=255, blank=True, null=True)
    conteudo = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.nome or 'Sem nome'} ({self.tipo or 'Sem tipo'})"


# ==============================
# TABELAS LEGADAS DO ERP (AUD_*)
# ==============================

class CustomizacaoFV(AbstractCustomizacao):
    id = models.IntegerField(primary_key=True, db_column="ID")
    categoria = models.IntegerField(db_column="IDCATEGORIA", blank=True, null=True)
    ativo = models.BooleanField(db_column="ATIVO", default=True)

    class Meta:
        managed = False
        db_table = "AUD_FV"


class CustomizacaoSQL(AbstractCustomizacao):
    id = models.IntegerField(primary_key=True, db_column="CODSENTENCA")
    tamanho = models.IntegerField(db_column="TAMANHO", blank=True, null=True)
    aplicacao = models.CharField(max_length=100, db_column="APLICACAO", blank=True, null=True)
    conteudo = models.TextField(db_column="SENTENCA", blank=True, null=True)

    class Meta:
        managed = False
        db_table = "AUD_SQL"


class CustomizacaoReport(AbstractCustomizacao):
    id = models.IntegerField(primary_key=True, db_column="ID")
    codigo = models.CharField(max_length=100, db_column="CODIGO", blank=True, null=True)
    aplicacao = models.CharField(max_length=100, db_column="CODAPLICACAO", blank=True, null=True)

    class Meta:
        managed = False
        db_table = "AUD_REPORT"


# ==============================
# TABELAS NOVAS (CONTROLADAS)
# ==============================

class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True, db_column="id_usuario")
    nome = models.CharField(max_length=255, db_column="nome")
    email = models.EmailField(unique=True, db_column="email")
    cargo = models.CharField(max_length=100, blank=True, db_column="cargo")

    class Meta:
        managed = True
        db_table = "USUARIO"

    def __str__(self):
        return self.nome


class Notificacao(models.Model):
    id_notificacao = models.AutoField(primary_key=True, db_column="id_notificacao")
    titulo = models.CharField(max_length=255, db_column="titulo")
    descricao = models.TextField(blank=True, db_column="descricao")
    prioridade = models.CharField(max_length=50, blank=True, db_column="prioridade")
    data_hora = models.DateTimeField(auto_now_add=True, db_column="data_hora")
    lida = models.BooleanField(default=False, db_column="lida")
    id_usuario = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        db_column="id_usuario", related_name="notificacoes"
    )

    class Meta:
        managed = True
        db_table = "NOTIFICACAO"
        ordering = ["-data_hora"]


class Observacao(models.Model):
    id = models.AutoField(primary_key=True)
    texto = models.TextField(db_column="texto")
    data = models.DateTimeField(auto_now_add=True, db_column="data")
    criado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        db_column="criado_por", related_name="observacoes_criadas"
    )

    class Meta:
        managed = True
        db_table = "Observacao"


class Prioridade(models.Model):
    id = models.AutoField(primary_key=True)
    nivel = models.CharField(max_length=50, unique=True, db_column="nivel")

    class Meta:
        managed = True
        db_table = "Prioridade"


# ==============================
# CADASTRO DEPENDÊNCIAS (FKs LÓGICAS)
# ==============================

class CadastroDependencias(models.Model):
    id = models.AutoField(primary_key=True)

    id_aud_sql = models.IntegerField(null=True, blank=True, db_column="id_aud_sql")
    id_aud_report = models.IntegerField(null=True, blank=True, db_column="id_aud_report")
    id_aud_fv = models.IntegerField(null=True, blank=True, db_column="id_aud_fv")

    id_observacao = models.ForeignKey(Observacao, on_delete=models.SET_NULL, null=True, blank=True, db_column="id_observacao")
    id_prioridade = models.ForeignKey(Prioridade, on_delete=models.SET_NULL, null=True, blank=True, db_column="id_prioridade")
    criado_por = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column="criado_por")
    data_criacao = models.DateTimeField(auto_now_add=True, db_column="data_criacao")

    class Meta:
        managed = True
        db_table = "Cadastro_Dependencias"

    def __str__(self):
        itens = []
        if self.id_aud_fv: itens.append(f"FV:{self.id_aud_fv}")
        if self.id_aud_sql: itens.append(f"SQL:{self.id_aud_sql}")
        if self.id_aud_report: itens.append(f"REP:{self.id_aud_report}")
        return f"Dep {self.id}: {', '.join(itens) or 'Nenhuma'}"

    @property
    def aud_fv(self):
        return CustomizacaoFV.objects.filter(id=self.id_aud_fv).first() if self.id_aud_fv else None

    @property
    def aud_sql(self):
        return CustomizacaoSQL.objects.filter(id=self.id_aud_sql).first() if self.id_aud_sql else None

    @property
    def aud_report(self):
        return CustomizacaoReport.objects.filter(id=self.id_aud_report).first() if self.id_aud_report else None

    def clean(self):
        from django.core.exceptions import ValidationError
        errors = {}
        if self.id_aud_fv and not CustomizacaoFV.objects.filter(id=self.id_aud_fv).exists():
            errors['id_aud_fv'] = "Fórmula Visual não encontrada."
        if self.id_aud_sql and not CustomizacaoSQL.objects.filter(id=self.id_aud_sql).exists():
            errors['id_aud_sql'] = "Consulta SQL não encontrada."
        if self.id_aud_report and not CustomizacaoReport.objects.filter(id=self.id_aud_report).exists():
            errors['id_aud_report'] = "Relatório não encontrado."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ==============================
# FUNÇÃO AUXILIAR (substitui Customizacao)
# ==============================

def get_customizacoes(tipo=None):
    """Retorna queryset unificado"""
    if tipo == "SQL":
        return CustomizacaoSQL.objects.all()
    elif tipo == "RELATORIO":
        return CustomizacaoReport.objects.all()
    else:
        return CustomizacaoFV.objects.all()
    
def get_customizacoes(tipo=None):
    """Retorna queryset unificado para qualquer tipo de customização"""
    if tipo == "SQL":
        return CustomizacaoSQL.objects.all()
    elif tipo == "RELATORIO":
        return CustomizacaoReport.objects.all()
    else:
        return CustomizacaoFV.objects.all()