# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from customizacoes.models import (
    get_customizacoes, CadastroDependencias,
    CustomizacaoFV, CustomizacaoSQL, CustomizacaoReport
)

@login_required
def dashboard_view(request):
    tipo = request.GET.get('tipo', 'FV')
    customizacoes = get_customizacoes(tipo)[:20]
    return render(request, 'dashboard/index.html', {
        'customizacoes': customizacoes,
        'tipo': tipo
    })

@login_required
def historico_view(request):
    tipo = request.GET.get('tipo', 'FV')
    customizacoes = get_customizacoes(tipo).order_by('-alterado_no_erp_em')[:20]
    return render(request, 'dashboard/historico.html', {
        'customizacoes': customizacoes,
        'tipo': tipo
    })

@login_required
def verificacao_view(request, pk=None):
    if pk:
        dep = get_object_or_404(CadastroDependencias, pk=pk)
        return render(request, 'dashboard/verificacao_detalhe.html', {'dep': dep})
    else:
        dependencias = CadastroDependencias.objects.select_related('criado_por').all()
        resultados = []
        for dep in dependencias:
            status = "OK"
            detalhes = []
            if dep.id_aud_fv and not dep.aud_fv:
                status = "ERRO"; detalhes.append("FV não encontrada")
            if dep.id_aud_sql and not dep.aud_sql:
                status = "ERRO"; detalhes.append("SQL não encontrada")
            if dep.id_aud_report and not dep.aud_report:
                status = "ERRO"; detalhes.append("Report não encontrado")
            resultados.append({'dep': dep, 'status': status, 'detalhes': detalhes})
        return render(request, 'dashboard/verificacao.html', {'resultados': resultados})

@login_required
def dependencias_view(request):
    dependencias = CadastroDependencias.objects.select_related('criado_por').all()
    return render(request, 'dashboard/dependencias.html', {'dependencias': dependencias})

@login_required
def dependencia_cadastro_view(request):
    if request.method == 'POST':
        try:
            dep = CadastroDependencias(
                id_aud_fv=request.POST.get('id_aud_fv') or None,
                id_aud_sql=request.POST.get('id_aud_sql') or None,
                id_aud_report=request.POST.get('id_aud_report') or None,
                id_observacao_id=request.POST.get('id_observacao'),
                id_prioridade_id=request.POST.get('id_prioridade'),
                criado_por=request.user
            )
            dep.full_clean()
            dep.save()
            messages.success(request, 'Dependência cadastrada com sucesso!')
            return redirect('dependencias')
        except Exception as e:
            messages.error(request, f'Erro: {e}')
    return render(request, 'dashboard/dependencia_cadastro.html')

@login_required
def sql_view(request, pk=None):
    if pk:
        sql = get_object_or_404(CustomizacaoSQL, id=pk)
        return render(request, 'dashboard/sql_detalhe.html', {'sql': sql})
    else:
        sqls = CustomizacaoSQL.objects.all()[:20]
        return render(request, 'dashboard/sql.html', {'sqls': sqls})

@login_required
def formula_view(request):
    formulas = CustomizacaoFV.objects.all()[:20]
    return render(request, 'dashboard/formulas.html', {'formulas': formulas})

@login_required
def tabelas_view(request):
    import re
    tabelas_set = set()
    for s in CustomizacaoSQL.objects.values_list('sentenca', flat=True):
        if s:
            found = re.findall(r'\bFROM\s+([A-Z_]+)\b', s, re.I)
            tabelas_set.update(found)
    return render(request, 'dashboard/tabelas.html', {'tabelas': sorted(tabelas_set)})