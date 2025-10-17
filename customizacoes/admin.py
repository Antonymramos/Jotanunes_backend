from django.contrib import admin
from .models import Customizacao, Dependencia, Assinatura, Alteracao, Notificacao

@admin.register(Customizacao)
class CustomizacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'status', 'criado_no_erp_em', 'responsavel', 'codcoligada')  # Campos existentes
    list_filter = ('tipo', 'status', 'criado_no_erp_em')  # Filtros baseados em campos existentes
    search_fields = ('nome', 'descricao_tecnica', 'responsavel')  # Campos para busca
    list_per_page = 25

@admin.register(Dependencia)
class DependenciaAdmin(admin.ModelAdmin):
    list_display = ('origem', 'destino', 'relacao', 'observacao')
    list_filter = ('relacao',)
    search_fields = ('observacao',)

@admin.register(Assinatura)
class AssinaturaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'escopo', 'modulo', 'customizacao', 'ativo')
    list_filter = ('escopo', 'ativo')
    search_fields = ('modulo',)

@admin.register(Alteracao)
class AlteracaoAdmin(admin.ModelAdmin):
    list_display = ('customizacao', 'acao', 'ator', 'ocorreu_em', 'comentario')
    list_filter = ('acao', 'ocorreu_em')
    search_fields = ('comentario',)

@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ('customizacao', 'tipo', 'mensagem', 'destinatario', 'origem', 'lida', 'criada_em')
    list_filter = ('tipo', 'lida', 'criada_em')
    search_fields = ('mensagem',)