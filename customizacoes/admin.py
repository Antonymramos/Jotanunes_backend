# customizacoes/admin.py (use exatamente este)
from django.contrib import admin
from .models import (
    Usuario, Notificacao, Observacao, Prioridade, CadastroDependencias,
    CustomizacaoFV, CustomizacaoSQL, CustomizacaoReport
)

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id_usuario', 'nome', 'email', 'cargo')
    search_fields = ('nome', 'email')

@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ('id_notificacao', 'titulo', 'id_usuario', 'data_hora', 'lida')
    list_filter = ('lida', 'data_hora')
    search_fields = ('titulo',)
    readonly_fields = ('data_hora',)

@admin.register(CadastroDependencias)
class CadastroDependenciasAdmin(admin.ModelAdmin):
    list_display = ('id', 'fv_id', 'sql_id', 'report_id', 'criado_por', 'data_criacao')
    list_filter = ('data_criacao',)
    search_fields = ('id_aud_fv', 'id_aud_sql', 'id_aud_report')

    def fv_id(self, obj): return f"FV:{obj.id_aud_fv}" if obj.id_aud_fv else "-"
    fv_id.short_description = "FV"

    def sql_id(self, obj): return f"SQL:{obj.id_aud_sql}" if obj.id_aud_sql else "-"
    sql_id.short_description = "SQL"

    def report_id(self, obj): return f"REP:{obj.id_aud_report}" if obj.id_aud_report else "-"
    report_id.short_description = "Report"

@admin.register(CustomizacaoFV)
class CustomizacaoFVAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'tipo', 'status', 'ativo')
    list_filter = ('tipo', 'status', 'ativo')
    search_fields = ('nome', 'descricao_tecnica')

@admin.register(CustomizacaoSQL)
class CustomizacaoSQLAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'tipo', 'status', 'aplicacao')
    list_filter = ('tipo', 'status')
    search_fields = ('nome', 'sentenca')

@admin.register(CustomizacaoReport)
class CustomizacaoReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'tipo', 'status', 'codigo')
    list_filter = ('tipo', 'status')
    search_fields = ('nome', 'codigo')