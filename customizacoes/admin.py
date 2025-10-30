# customizacoes/admin.py
from django.contrib import admin
from .models import (
    Observacao, Prioridade, CadastroDependencias,
    CustomizacaoFV, CustomizacaoSQL, CustomizacaoReport,
    Notificacao
)

# === DEPENDÊNCIAS ===
@admin.register(CadastroDependencias)
class CadastroDependenciasAdmin(admin.ModelAdmin):
    list_display = ('id', 'origem', 'destino', 'criado_por', 'created_at', 'prioridade_badge')
    list_filter = ('created_at', 'id_prioridade__nivel')
    search_fields = ('id_aud_sql', 'id_aud_report', 'id_aud_fv')
    readonly_fields = ('created_at',)

    def origem(self, obj):
        return obj.get_origem_display()
    origem.short_description = "Origem"

    def destino(self, obj):
        return obj.get_destino_display()
    destino.short_description = "Destino"

    def prioridade_badge(self, obj):
        if not obj.id_prioridade:
            return "—"
        nivel = obj.id_prioridade.nivel
        if nivel == "Alta":
            return '<span class="badge bg-danger">Alta</span>'
        elif nivel == "Média":
            return '<span class="badge bg-warning">Média</span>'
        else:
            return '<span class="badge bg-success">Baixa</span>'
    prioridade_badge.short_description = "Prioridade"
    prioridade_badge.allow_tags = True


# === TABELAS LEGADAS ===
@admin.register(CustomizacaoFV)
class CustomizacaoFVAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'codcoligada', 'ativo')
    list_filter = ('ativo', 'codcoligada')
    search_fields = ('nome', 'descricao')


@admin.register(CustomizacaoSQL)
class CustomizacaoSQLAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'aplicacao', 'codcoligada')
    list_filter = ('aplicacao', 'codcoligada')
    search_fields = ('titulo', 'sentenca')


@admin.register(CustomizacaoReport)
class CustomizacaoReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'codaplicacao', 'codcoligada')
    list_filter = ('codaplicacao', 'codcoligada')
    search_fields = ('codigo', 'descricao')


# === OUTRAS TABELAS ===
@admin.register(Observacao)
class ObservacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'texto', 'data', 'criado_por')
    list_filter = ('data',)
    search_fields = ('texto',)


@admin.register(Prioridade)
class PrioridadeAdmin(admin.ModelAdmin):
    list_display = ('id', 'nivel')
    search_fields = ('nivel',)


# === NOTIFICAÇÃO ===
@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'id_usuario', 'prioridade', 'data_hora', 'lida')
    list_filter = ('prioridade', 'lida', 'data_hora')
    search_fields = ('titulo', 'descricao', 'id_usuario__username')
    readonly_fields = ('data_hora',)
    ordering = ('-data_hora',)

    def has_add_permission(self, request):
        return False