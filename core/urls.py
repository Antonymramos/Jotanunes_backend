# core/urls.py - ROTAS COMPLETAS COM PAINEL DE GESTÃO

from django.urls import path
from . import views

urlpatterns = [
    # Painel de Gestão
    path('painel-gestao/', views.painel_gestao, name='painel_gestao'),
    
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),
    
    # Histórico
    path('historico/', views.historico_view, name='historico'),

    
    # Verificação
    path('verificacao/', views.verificacao_view, name='verificacao'),
    path('verificacao/<int:pk>/', views.verificacao_view, name='verificacao_pk'),
    
    # Dependências
    path('dependencias/', views.dependencias_view, name='dependencias'),
    path('dependencia/cadastro/', views.dependencia_cadastro_view, name='dependencia_cadastro'),
    path('dependencia/<int:pk>/visualizar/', views.dependencia_visualizar_view, name='dependencia_visualizar'),
    path('dependencia/<int:pk>/editar/', views.dependencia_editar_view, name='dependencia_editar'),
    path('dependencia/<int:pk>/excluir/', views.dependencia_excluir_view, name='dependencia_excluir'),
    
    # SQL
    path('dependencias/sql/', views.sql_view, name='sql'),
    path('dependencias/sql/<str:pk>/', views.sql_view, name='sql_pk'),
    
    # Fórmulas
    path('dependencias/formulas/', views.formula_view, name='formulas'),
    path('dependencias/formulas/<int:pk>/', views.formula_view, name='formulas_pk'),
    
    # Tabelas
    path('dependencias/tabelas/', views.tabelas_view, name='tabelas'),
    
    # Notificações
    path('notificacoes/', views.notificacoes_view, name='notificacoes'),
    path('notificacao/<int:pk>/marcar-lida/', views.marcar_lida_view, name='marcar_lida'),
]
