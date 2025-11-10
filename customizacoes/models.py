from django.db import models
from django.core.exceptions import ValidationError


# ============================================================================
# TABELAS LEGADAS (NÃO GERENCIADAS)
# ============================================================================

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


# ============================================================================
# TABELAS NOVAS
# ============================================================================

class Prioridade(models.Model):
    nivel = models.CharField(max_length=50, db_column="nivel", unique=True)
    data_criacao = models.DateTimeField(auto_now_add=True, db_column="data_criacao")

    class Meta:
        managed = True
        db_table = "Prioridade"
        ordering = ['nivel']

    def __str__(self):
        return self.nivel


class CadastroDependencias(models.Model):
    id_aud_sql = models.CharField(max_length=100, null=True, blank=True)
    id_aud_report = models.IntegerField(null=True, blank=True)
    id_aud_fv = models.IntegerField(null=True, blank=True)

    id_prioridade = models.ForeignKey(
        Prioridade,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='dependencias'
    )

    data_criacao = models.DateTimeField(auto_now_add=True)
    criado_por = models.CharField(max_length=100)

    class Meta:
        managed = True
        db_table = "Cadastro_Dependencias"

    def clean(self):
        preenchidos = sum([bool(self.id_aud_sql), bool(self.id_aud_report), bool(self.id_aud_fv)])
        if preenchidos == 0:
            raise ValidationError("Selecione pelo menos um item principal.")

    def get_principal_tipo(self):
        if self.id_aud_sql: return 'sql'
        if self.id_aud_report: return 'report'
        if self.id_aud_fv: return 'fv'
        return None

    def get_principal_id(self):
        if self.id_aud_sql: return self.id_aud_sql
        if self.id_aud_report: return self.id_aud_report
        if self.id_aud_fv: return self.id_aud_fv
        return None

    def get_principal_label(self):
        tipo = self.get_principal_tipo()
        id_val = self.get_principal_id()
        if not tipo or not id_val: return '—'

        if tipo == 'sql':
            obj = CustomizacaoSQL.objects.filter(codsentenca=id_val).first()
            return f"SQL: {id_val} - {obj.titulo if obj else ''}".strip()
        elif tipo == 'report':
            try:
                obj = CustomizacaoReport.objects.filter(id=int(id_val)).first()
                return f"REP: {id_val} - {obj.codigo if obj else ''}".strip()
            except:
                return f"REP: {id_val}"
        elif tipo == 'fv':
            try:
                obj = CustomizacaoFV.objects.filter(id=int(id_val)).first()
                return f"FV: {id_val} - {obj.nome if obj else ''}".strip()
            except:
                return f"FV: {id_val}"
        return '—'

    def __str__(self):
        return f"Dependência {self.id}: {self.get_principal_label()}"

    def get_prioridade_mais_alta(self):
        """
        Retorna a prioridade mais alta entre todas as dependências relacionadas
        que usam este cadastro como principal.
        """
        from .models import DependenciaItem
        deps = DependenciaItem.objects.filter(cadastro=self)
        prioridades = Prioridade.objects.filter(dependencias__in=deps).distinct()
        if not prioridades:
            return None
        ordem = {'Alta': 3, 'Média': 2, 'Baixa': 1}
        return max(prioridades, key=lambda p: ordem.get(p.nivel, 0))


class DependenciaItem(models.Model):
    cadastro = models.ForeignKey(CadastroDependencias, on_delete=models.CASCADE, related_name='dependentes')
    tipo = models.CharField(max_length=20, choices=[('sql', 'SQL'), ('report', 'Report'), ('fv', 'Fórmula')])
    id_dependente = models.CharField(max_length=100)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "Dependencia_Item"
        unique_together = [['cadastro', 'tipo', 'id_dependente']]

    def get_label(self):
        if self.tipo == 'sql':
            obj = CustomizacaoSQL.objects.filter(codsentenca=self.id_dependente).first()
            return f"SQL: {self.id_dependente} - {obj.titulo if obj else ''}".strip()
        elif self.tipo == 'report':
            try:
                obj = CustomizacaoReport.objects.filter(id=int(self.id_dependente)).first()
                return f"REP: {self.id_dependente} - {obj.codigo if obj else ''}".strip()
            except:
                return f"REP: {self.id_dependente}"
        elif self.tipo == 'fv':
            try:
                obj = CustomizacaoFV.objects.filter(id=int(self.id_dependente)).first()
                return f"FV: {self.id_dependente} - {obj.nome if obj else ''}".strip()
            except:
                return f"FV: {self.id_dependente}"
        return '—'

    def __str__(self):
        return self.get_label()


class Notificacao(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    prioridade = models.ForeignKey(Prioridade, on_delete=models.SET_NULL, null=True, blank=True, related_name='notificacoes')
    data_hora = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)
    id_usuario = models.CharField(max_length=150)

    class Meta:
        managed = True
        db_table = "NOTIFICACAO"
        ordering = ['-data_hora']

    def __str__(self):
        return self.titulo
class HistoricoAlteracao(models.Model):
    CHOICES_STATUS = [
        ('em_analise', 'Em Análise'),
        ('aprovado', 'Aprovado'),
        ('reprovado', 'Reprovado'),
    ]
    PRIORIDADE_CHOICES = [
        ('Alta', 'Alta'),
        ('Média', 'Média'),
        ('Baixa', 'Baixa'),
    ]

    log_entry_id = models.IntegerField(unique=True, db_column="log_entry_id")
    objeto_tipo = models.CharField(max_length=50, db_column="objeto_tipo")
    objeto_id = models.CharField(max_length=100, db_column="objeto_id")
    titulo = models.CharField(max_length=255, blank=True, db_column="titulo")
    valor_atual = models.TextField(blank=True, null=True, db_column="valor_atual")
    valor_anterior = models.TextField(blank=True, null=True, db_column="valor_anterior")
    acao = models.CharField(max_length=50, db_column="acao")
    usuario = models.CharField(max_length=150, db_column="usuario")
    data_alteracao = models.DateTimeField(db_column="data_alteracao")
    prioridade_maxima = models.CharField(
        max_length=20, choices=PRIORIDADE_CHOICES, default='Baixa', db_column="prioridade_maxima"
    )
    status = models.CharField(
        max_length=20, choices=CHOICES_STATUS, default='em_analise', db_column="status"
    )
    observacao = models.TextField(blank=True, null=True, db_column="observacao")
    dependencias_afetadas = models.IntegerField(default=0, db_column="dependencias_afetadas")
    data_criacao = models.DateTimeField(auto_now_add=True, db_column="data_criacao")

    class Meta:
        managed = True
        db_table = "Historico_Alteracao"
        ordering = ['-data_alteracao']

    def __str__(self):
        return f"{self.objeto_tipo.upper()} {self.objeto_id} - {self.status}"

    def sincronizar_prioridade(self):
        from django.db.models import Q
        deps = CadastroDependencias.objects.filter(
            Q(id_aud_sql=self.objeto_id if self.objeto_tipo == 'sql' else None) |
            Q(id_aud_report=int(self.objeto_id) if self.objeto_tipo == 'report' else None) |
            Q(id_aud_fv=int(self.objeto_id) if self.objeto_tipo == 'fv' else None)
        ).select_related('id_prioridade')
        self.dependencias_afetadas = deps.count()
        prioridade_maxima = 'Baixa'
        ordem = {'Alta': 3, 'Média': 2, 'Baixa': 1}
        for dep in deps:
            if dep.id_prioridade:
                nivel = dep.id_prioridade.nivel
                if ordem.get(nivel, 0) > ordem.get(prioridade_maxima, 1):
                    prioridade_maxima = nivel
        self.prioridade_maxima = prioridade_maxima
        self.save(update_fields=['prioridade_maxima', 'dependencias_afetadas'])
