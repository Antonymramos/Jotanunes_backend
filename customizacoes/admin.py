# customizacoes/admin.py
from django.contrib import admin
from .models import (
    CadastroDependencias, Prioridade, Notificacao,
    CustomizacaoFV, CustomizacaoSQL, CustomizacaoReport
)


@admin.register(CadastroDependencias)
class CadastroDependenciasAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_aud_sql', 'id_aud_report', 'id_aud_fv', 'data_criacao')
    list_filter = ('data_criacao', 'id_prioridade')
    search_fields = ('id_aud_sql', 'id_aud_report', 'id_aud_fv')


@admin.register(CustomizacaoFV)
class CustomizacaoFVAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'codcoligada', 'ativo')
    list_filter = ('ativo', 'codcoligada')
    search_fields = ('nome', 'descricao')


@admin.register(CustomizacaoSQL)
class CustomizacaoSQLAdmin(admin.ModelAdmin):
    list_display = ('codsentenca', 'titulo', 'aplicacao', 'codcoligada')
    list_filter = ('aplicacao', 'codcoligada')
    search_fields = ('codsentenca', 'titulo', 'sentenca')


@admin.register(CustomizacaoReport)
class CustomizacaoReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'codaplicacao', 'codcoligada')
    list_filter = ('codaplicacao', 'codcoligada')
    search_fields = ('codigo', 'descricao')


@admin.register(Prioridade)
class PrioridadeAdmin(admin.ModelAdmin):
    list_display = ('id', 'nivel')
    search_fields = ('nivel',)