# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('historico/', views.historico_view, name='historico'),
    path('verificacao/', views.verificacao_view, name='verificacao'),
    path('verificacao/<int:pk>/', views.verificacao_view, name='verificacao_pk'),
    path('dependencias/', views.dependencias_view, name='dependencias'),
    path('dependencias/cadastro/', views.dependencia_cadastro_view, name='dependencia_cadastro'),
    path('dependencias/sql/', views.sql_view, name='sql'),
    path('dependencias/sql/<int:pk>/', views.sql_view, name='sql_pk'),
    path('dependencias/formulas/', views.formula_view, name='formulas'),
    path('dependencias/tabelas/', views.tabelas_view, name='tabelas'),
]
