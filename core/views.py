# core/views.py
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
import re
from customizacoes.models import (
    CadastroDependencias, Prioridade, Notificacao,
    CustomizacaoSQL, CustomizacaoReport, CustomizacaoFV
)


@login_required
def dashboard_view(request):
    """Dashboard principal - mostra resumo"""
    tipo = request.GET.get('tipo', 'FV')
    
    # Contadores para dashboard
    total_sql = CustomizacaoSQL.objects.count()
    total_reports = CustomizacaoReport.objects.count()
    total_fv = CustomizacaoFV.objects.count()
    total_deps = CadastroDependencias.objects.count()
    
    context = {
        'total_sql': total_sql,
        'total_reports': total_reports,
        'total_fv': total_fv,
        'total_deps': total_deps,
        'tipo': tipo
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def historico_view(request):
    """Histórico de alterações"""
    tipo = request.GET.get('tipo', 'FV')
    # Simula histórico (pode conectar com logs depois)
    historico = CadastroDependencias.objects.order_by('-created_at')[:20]
    return render(request, 'dashboard/historico.html', {
        'historico': historico,
        'tipo': tipo
    })


@login_required
def verificacao_view(request, pk=None):
    """Verificação de dependências"""
    if pk:
        dep = get_object_or_404(CadastroDependencias, pk=pk)
        return render(request, 'dashboard/verificacao_detalhe.html', {'dep': dep})
    else:
        dependencias = CadastroDependencias.objects.all()
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
    """Lista todas as dependências"""
    dependencias = CadastroDependencias.objects.select_related(
        'criado_por', 'id_prioridade'
    ).order_by('-created_at')
    return render(request, 'dashboard/dependencias.html', {
        'dependencias': dependencias
    })


@login_required
def dependencia_cadastro_view(request):
    if request.method == 'POST':
        try:
            # === RECEBE CAMPOS ===
            id_aud_sql = request.POST.getlist('id_aud_sql')
            id_aud_report = request.POST.getlist('id_aud_report')
            id_aud_fv = request.POST.getlist('id_aud_fv')
            prioridade_id = request.POST.get('id_prioridade') or None

            # === VALIDAÇÃO OBRIGATÓRIA ===
            todos_ids = id_aud_sql + id_aud_report + id_aud_fv
            if len(todos_ids) != 2:
                messages.error(request, f"Selecione exatamente 1 origem e 1 destino. (Recebido: {len(todos_ids)})")
                return redirect('dependencia_cadastro')

            # === BUSCA OBJETO PRIORIDADE ===
            prioridade_obj = None
            if prioridade_id:
                prioridade_obj = get_object_or_404(Prioridade, id=prioridade_id)

            # === CRIA DEPENDÊNCIAS ===
            dependencias = []
            for campo, valor in [
                ('id_aud_sql', id_aud_sql),
                ('id_aud_report', id_aud_report),
                ('id_aud_fv', id_aud_fv)
            ]:
                if valor:
                    for v in valor:
                        data = {
                            campo: int(v),
                            'id_prioridade': prioridade_obj,
                            'criado_por': request.user
                        }
                        dep = CadastroDependencias(**data)
                        dep.full_clean()  # ← VALIDAÇÃO DO MODEL
                        dependencias.append(dep)

            CadastroDependencias.objects.bulk_create(dependencias)

            # === ALERTA VISUAL + NOTIFICAÇÃO ===
            if prioridade_obj:
                nivel = prioridade_obj.nivel

                # ALERTA VISUAL
                request.session['alerta_tipo'] = {
                    'Baixa': 'success',
                    'Média': 'warning',
                    'Alta': 'danger'
                }[nivel]
                request.session['alerta_mensagem'] = f"Dependência {nivel} cadastrada com sucesso!"

                # NOTIFICAÇÃO
                for usuario in User.objects.all():
                    Notificacao.objects.create(
                        titulo=f"Dependência {nivel} criada",
                        descricao=f"{request.user.username} cadastrou uma nova dependência.",
                        prioridade=nivel,
                        id_usuario=usuario
                    )

            # === AVISO DE SUCESSO (SEMPRE) ===
            messages.success(request, f'{len(dependencias)} dependências cadastradas com sucesso!')
            return redirect('dependencias')

        except Exception as e:
            messages.error(request, f'Erro ao cadastrar: {e}')
            return redirect('dependencia_cadastro')

    # === DADOS ===
    sqls = CustomizacaoSQL.objects.values('id', 'titulo').order_by('titulo')
    reports = CustomizacaoReport.objects.values('id', 'codigo', 'descricao').order_by('codigo')
    fvs = CustomizacaoFV.objects.values('id', 'nome', 'descricao').order_by('nome')
    prioridades = Prioridade.objects.all().order_by('nivel')

    return render(request, 'dashboard/dependencia_cadastro.html', {
        'sqls': list(sqls),
        'reports': list(reports),
        'fvs': list(fvs),
        'prioridades': prioridades,
    })


@login_required
def notificacoes_view(request):
    # === CONTADORES ===
    contadores = Notificacao.objects.filter(
        id_usuario=request.user, lida=False
    ).values('prioridade').annotate(total=Count('id'))

    alta_count = next((c['total'] for c in contadores if c['prioridade'] == 'Alta'), 0)
    media_count = next((c['total'] for c in contadores if c['prioridade'] == 'Média'), 0)
    baixa_count = next((c['total'] for c in contadores if c['prioridade'] == 'Baixa'), 0)

    notificacoes = Notificacao.objects.filter(id_usuario=request.user).order_by('-data_hora')

    return render(request, 'dashboard/notificacoes.html', {
        'notificacoes': notificacoes,
        'alta_count': alta_count,
        'media_count': media_count,
        'baixa_count': baixa_count,
    })


@login_required
def marcar_lida_view(request, pk):
    notif = get_object_or_404(Notificacao, pk=pk, id_usuario=request.user)
    if request.method == 'POST':
        notif.lida = True
        notif.save()
        messages.success(request, 'Notificação validada.')
    return redirect('notificacoes')


@login_required
def sql_view(request, pk=None):
    """Lista e detalha consultas SQL"""
    if pk:
        sql = get_object_or_404(CustomizacaoSQL, id=pk)
        return render(request, 'dashboard/sql_detalhe.html', {'sql': sql})
    else:
        sqls = CustomizacaoSQL.objects.order_by('titulo')[:20]
        return render(request, 'dashboard/sql.html', {'sqls': sqls})


@login_required
def formula_view(request):
    """Lista fórmulas visuais"""
    formulas = CustomizacaoFV.objects.filter(ativo=True).order_by('nome')[:20]
    return render(request, 'dashboard/formulas.html', {'formulas': formulas})


@login_required
def tabelas_view(request):
    """Extrai tabelas das consultas SQL"""
    tabelas_set = set()
    for sql in CustomizacaoSQL.objects.values_list('sentenca', flat=True):
        if sql:
            found = re.findall(r'\bFROM\s+([A-Z_][A-Z0-9_]*)\b', sql, re.I)
            tabelas_set.update(found)
    
    tabelas = [{'nome': t, 'registros': 0} for t in sorted(tabelas_set)]
    return render(request, 'dashboard/tabelas.html', {'tabelas': tabelas})