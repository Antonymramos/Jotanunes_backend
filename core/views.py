import json
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.db import transaction
from django.contrib.admin.models import LogEntry
from datetime import datetime, timezone
import re
import difflib
from customizacoes.models import (
    CadastroDependencias, Prioridade, Notificacao,DependenciaItem,
    CustomizacaoSQL, CustomizacaoReport, CustomizacaoFV, HistoricoAlteracao
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_label(tipo, valor):
    """Retorna label formatada para exibição"""
    if tipo == 'sql':
        try:
            obj = CustomizacaoSQL.objects.filter(codsentenca=valor).first()
            return f"SQL: {valor} - {obj.titulo if obj else ''}".strip()
        except:
            return f"SQL: {valor}"
    elif tipo == 'report':
        try:
            obj = CustomizacaoReport.objects.filter(id=int(valor)).first()
            return f"REP: {valor} - {obj.codigo if obj else ''}".strip()
        except:
            return f"REP: {valor}"
    elif tipo == 'fv':
        try:
            obj = CustomizacaoFV.objects.filter(id=int(valor)).first()
            return f"FV: {valor} - {obj.nome if obj else ''}".strip()
        except:
            return f"FV: {valor}"
    return '—'

# ============================================================================
# HISTÓRICO DE ALTERAÇÕES
# ============================================================================

@login_required
def historico_view(request):
    """Exibe página do histórico de alterações"""
    status_filtro = request.GET.get('status', '')
    prioridade_filtro = request.GET.get('prioridade', '')

    historico_query = HistoricoAlteracao.objects.all().order_by('-data_alteracao')[:50]
    if status_filtro:
        historico_query = historico_query.filter(status=status_filtro)
    if prioridade_filtro:
        historico_query = historico_query.filter(prioridade_maxima=prioridade_filtro)

    historico_lista = []
    for item in historico_query:
        historico_lista.append({
            'id': item.id,
            'objeto_tipo': item.objeto_tipo,
            'objeto_id': item.objeto_id,
            'titulo': item.titulo,
            'acao': item.acao,
            'usuario': item.usuario,
            'data': item.data_alteracao,
            'prioridade_maxima': item.prioridade_maxima,
            'dependencias_count': item.dependencias_afetadas,
            'status': item.status,
            'observacao': item.observacao,
            'valor_anterior': item.valor_anterior,
            'valor_atual': item.valor_atual,
        })

    return render(request, 'dashboard/historico.html', {
        'historico': historico_lista,
        'status_choices': HistoricoAlteracao.CHOICES_STATUS,
        'prioridade_choices': HistoricoAlteracao.PRIORIDADE_CHOICES,
        'status_selecionado': status_filtro,
        'prioridade_selecionada': prioridade_filtro,
        'active_page': 'historico'
    })

@login_required
def historico_atualizar_status(request, pk):
    """Edita status e observação de uma alteração do histórico."""
    try:
        hist = get_object_or_404(HistoricoAlteracao, pk=pk)
        if request.method == 'POST':
            novo_status = request.POST.get('status')
            observacao = request.POST.get('observacao', '')

            if novo_status not in dict(HistoricoAlteracao.CHOICES_STATUS):
                return JsonResponse({'erro': 'Status inválido'}, status=400)

            hist.status = novo_status
            hist.observacao = observacao
            hist.save()

            messages.success(request, f'Status atualizado para {novo_status}!')
            return redirect('historico')
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return redirect('historico')

    return redirect('historico')

def sincronizar_historico_alteracoes():
    """Sincroniza LogEntry com HistoricoAlteracao para garantir que só apareçam alterações reais ('sobrevividas')."""
    for log in LogEntry.objects.filter(
        content_type__model__in=['customizacaosql', 'customizacaoreport', 'customizacaofv']
    ).order_by('-action_time'):

        obj = log.get_edited_object()
        if not obj:
            HistoricoAlteracao.objects.filter(log_entry_id=log.id).delete()
            continue

        if isinstance(obj, CustomizacaoSQL):
            tipo_obj = 'sql'
            id_obj = obj.codsentenca
            titulo = obj.titulo or ''
        elif isinstance(obj, CustomizacaoReport):
            tipo_obj = 'report'
            id_obj = obj.id
            titulo = obj.codigo or ''
        elif isinstance(obj, CustomizacaoFV):
            tipo_obj = 'fv'
            id_obj = obj.id
            titulo = obj.nome or ''
        else:
            continue

        hist, created = HistoricoAlteracao.objects.update_or_create(
            log_entry_id=log.id,
            defaults={
                'objeto_tipo': tipo_obj,
                'objeto_id': str(id_obj),
                'titulo': titulo,
                'acao': log.get_action_flag_display(),
                'usuario': log.user.get_full_name() or log.user.username,
                'data_alteracao': log.action_time,
            }
        )
        hist.sincronizar_prioridade()

@login_required
def sincronizar_historico(request):
    """Endpoint manual para acionar a sincronização das entradas do histórico."""
    if request.method == 'POST':
        try:
            sincronizar_historico_alteracoes()
            messages.success(request, 'Histórico sincronizado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro durante sincronização: {str(e)}')
    return redirect('historico')

# ============================================================================
# PAINEL DE GESTÃO
# ============================================================================

@login_required
def painel_gestao(request):
    historico_alteracoes = LogEntry.objects.select_related('user').order_by('-action_time')[:10]
    em_atencao = CadastroDependencias.objects.all().count()
    alteracoes = LogEntry.objects.filter(action_flag=2).count()
    novas_notificacoes = Notificacao.objects.filter(id_usuario=request.user.username, lida=False).count()

    context = {
        'historico_alteracoes': historico_alteracoes,
        'alteracoes': alteracoes,
        'em_atencao': em_atencao,
        'novas_notificacoes': novas_notificacoes,
    }
    return render(request, 'dashboard/index.html', context)

# ============================================================================
# DASHBOARD
# ============================================================================

@login_required
def dashboard_view(request):
    """Dashboard principal com contadores"""
    tipo = request.GET.get('tipo', 'FV')
    total_sql = CustomizacaoSQL.objects.count()
    total_reports = CustomizacaoReport.objects.count()
    total_fv = CustomizacaoFV.objects.count()
    total_deps = CadastroDependencias.objects.count()

    context = {
        'total_sql': total_sql,
        'total_reports': total_reports,
        'total_fv': total_fv,
        'total_deps': total_deps,
        'tipo': tipo,
        'active_page': 'dashboard'
    }
    return render(request, 'dashboard/index.html', context)

# ============================================================================
# VERIFICAÇÃO
# ============================================================================

@login_required
def verificacao_view(request, pk=None):
    """Verificação de integridade das dependências"""
    if pk:
        dep = get_object_or_404(CadastroDependencias, pk=pk)
        return render(request, 'dashboard/verificacao_detalhe.html', {'dep': dep})
    else:
        dependencias = CadastroDependencias.objects.all()
        resultados = []

        for dep in dependencias:
            status = "OK"
            detalhes = []
            if dep.id_aud_fv and not CustomizacaoFV.objects.filter(id=dep.id_aud_fv).exists():
                status = "ERRO"
                detalhes.append("FV não encontrada")
            if dep.id_aud_sql and not CustomizacaoSQL.objects.filter(codsentenca=dep.id_aud_sql).exists():
                status = "ERRO"
                detalhes.append("SQL não encontrada")
            if dep.id_aud_report and not CustomizacaoReport.objects.filter(id=dep.id_aud_report).exists():
                status = "ERRO"
                detalhes.append("Report não encontrado")
            resultados.append({'dep': dep, 'status': status, 'detalhes': detalhes})

        return render(request, 'dashboard/verificacao.html', {'resultados': resultados})

# ============================================================================
# DEPENDÊNCIAS
# ============================================================================

@login_required
def dependencias_view(request):
    """
    Listar dependências com dados para filtros e modais.
    - Exibe principal e dependente
    - Mostra prioridade
    - Envia listas de SQL, Report e FV para modais de cadastro
    """
    # Query base
    consulta = CadastroDependencias.objects.all().order_by('-data_criacao')
    dependencias = consulta

    # Processar dados para exibição
    deps_com_dados = []
    for dep in dependencias:
        campos = {}
        if dep.id_aud_sql:
            campos['sql'] = dep.id_aud_sql
        if dep.id_aud_report:
            campos['report'] = dep.id_aud_report
        if dep.id_aud_fv:
            campos['fv'] = dep.id_aud_fv

        principal_label = '—'
        dependencia_label = '—'
        
        if len(campos) >= 2:
            itens = list(campos.items())
            principal_tipo, principal_id = itens[0]
            dep_tipo, dep_id = itens[1]
            principal_label = get_label(principal_tipo, principal_id)
            dependencia_label = get_label(dep_tipo, dep_id)
        
        prioridade_nivel = 'Sem prioridade'
        if dep.id_prioridade:
            try:
                prioridade_nivel = dep.id_prioridade.nivel
            except:
                pass

        dados = {
            'id': dep.id,
            'principal_label': principal_label,
            'dependencias_label': dependencia_label,
            'prioridade_nivel': prioridade_nivel,
            'criado_por': dep.criado_por,
            'data_criacao': dep.data_criacao,
        }
        deps_com_dados.append(dados)

    # === DADOS PARA MODAIS DE CADASTRO ===
    sqls = list(CustomizacaoSQL.objects.values('codsentenca', 'titulo'))
    relatorios = list(CustomizacaoReport.objects.values('id', 'codigo', 'descricao'))
    fvs = list(CustomizacaoFV.objects.values('id', 'nome', 'descricao'))

    return render(request, 'dashboard/dependencias.html', {
        'dependencias': deps_com_dados,
        'sqls': sqls,
        'relatorios': relatorios,
        'fvs': fvs,
        'active_page': 'dependencias'
    })
    
@login_required
def dependencia_cadastro_view(request):
    """Cadastrar nova dependência"""
    if request.method == 'POST':
        try:
            principal_tipo = request.POST.get('principal_tipo')
            principal_id = request.POST.get('principal_id')
            if not principal_tipo or not principal_id:
                raise ValueError("Selecione um item principal.")
            dependencias = []
            for tipo in ['sql', 'report', 'fv']:
                for dep_id in request.POST.getlist(f'dependencia_{tipo}[]'):
                    if not (tipo == principal_tipo and dep_id == principal_id):
                        dependencias.append({"tipo": tipo, "id": dep_id})
            if not dependencias:
                raise ValueError("Selecione pelo menos 1 dependência.")
            id_prioridade = request.POST.get('id_prioridade')
            id_prioridade = int(id_prioridade) if id_prioridade and id_prioridade.isdigit() else None
            with transaction.atomic():
                for dep_item in dependencias:
                    data = {
                        'criado_por': request.user.username or 'ANONYMOUS',
                        'id_prioridade_id': id_prioridade,
                        'id_aud_sql': None,
                        'id_aud_report': None,
                        'id_aud_fv': None,
                    }
                    if principal_tipo == 'sql':
                        data['id_aud_sql'] = principal_id
                    elif principal_tipo == 'report':
                        data['id_aud_report'] = int(principal_id)
                    elif principal_tipo == 'fv':
                        data['id_aud_fv'] = int(principal_id)
                    if dep_item['tipo'] == 'sql':
                        data['id_aud_sql'] = dep_item['id']
                    elif dep_item['tipo'] == 'report':
                        data['id_aud_report'] = int(dep_item['id'])
                    elif dep_item['tipo'] == 'fv':
                        data['id_aud_fv'] = int(dep_item['id'])
                    dep_obj = CadastroDependencias(**data)
                    dep_obj.save()
            messages.success(request, f'{len(dependencias)} dependência(s) cadastrada(s)!')
            return redirect('dependencias')
        except Exception as e:
            messages.error(request, f'Erro: {e}')
    sqls = list(CustomizacaoSQL.objects.values('codsentenca', 'titulo'))
    reports = list(CustomizacaoReport.objects.values('id', 'codigo', 'descricao'))
    fvs = list(CustomizacaoFV.objects.values('id', 'nome', 'descricao'))
    prioridades = list(Prioridade.objects.values('id', 'nivel'))
    return render(request, 'dashboard/dependencia_cadastro.html', {
        'sqls': sqls,
        'reports': reports,
        'fvs': fvs,
        'prioridades': prioridades,
        'active_page': 'dependencias'
    })

@login_required
def dependencia_visualizar_view(request, pk):
    """Visualizar detalhes de uma dependência"""
    dep = get_object_or_404(CadastroDependencias, pk=pk)
    campos = {}
    if dep.id_aud_sql: campos['sql'] = dep.id_aud_sql
    if dep.id_aud_report: campos['report'] = dep.id_aud_report
    if dep.id_aud_fv: campos['fv'] = dep.id_aud_fv
    principal_label = '—'
    dependencia_label = '—'
    if len(campos) >= 2:
        items = list(campos.items())
        principal_tipo, principal_id = items[0]
        dep_tipo, dep_id = items[1]
        principal_label = get_label(principal_tipo, principal_id)
        dependencia_label = get_label(dep_tipo, dep_id)
    prioridade_nivel = 'Sem prioridade'
    if dep.id_prioridade:
        try:
            prioridade_nivel = dep.id_prioridade.nivel
        except:
            pass
    return render(request, 'dashboard/dependencia_visualizar.html', {
        'dep': dep,
        'principal_label': principal_label,
        'dependencia_label': dependencia_label,
        'prioridade_nivel': prioridade_nivel,
    })


import json
import traceback
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from customizacoes.models import (
    CadastroDependencias, DependenciaItem, Prioridade,
    CustomizacaoSQL, CustomizacaoReport, CustomizacaoFV, HistoricoAlteracao
)


@login_required
def dependencia_editar_view(request, pk):
    """Edita uma dependência: prioridade, observações e dependências relacionadas."""
    dependencia = get_object_or_404(CadastroDependencias, pk=pk)

    if request.method == 'POST':
        prioridade_nova = request.POST.get('prioridade', '').strip()
        observacoes = request.POST.get('observacoes', '').strip()
        dependencias_json = request.POST.get('dependencias_json', '[]')

        # CORRIGIDO: id_prioridade
        prioridade_anterior = dependencia.id_prioridade.nivel if dependencia.id_prioridade else ''
        observacoes_anterior = getattr(dependencia, 'observacoes', '') or ''

        # CORRIGIDO: cadastro + id_dependente
        deps_anteriores = list(
            DependenciaItem.objects.filter(cadastro=dependencia).values_list('tipo', 'id_dependente')
        )

        mudou = False
        mudancas = []

        # === PRIORIDADE ===
        if prioridade_nova and prioridade_nova != prioridade_anterior:
            try:
                prioridade_obj = Prioridade.objects.get(nivel=prioridade_nova)
                dependencia.id_prioridade = prioridade_obj
                mudou = True
                mudancas.append(f"Prioridade: {prioridade_anterior} → {prioridade_nova}")
            except Prioridade.DoesNotExist:
                messages.error(request, f"Prioridade '{prioridade_nova}' não encontrada.")
                return redirect('dependencia_editar', pk=pk)

        # === OBSERVAÇÕES ===
        if observacoes != observacoes_anterior:
            if hasattr(dependencia, 'observacoes'):
                dependencia.observacoes = observacoes
                mudou = True
                mudancas.append("Observações atualizadas")

        # === DEPENDÊNCIAS ===
        try:
            novas_dependencias = json.loads(dependencias_json)
            if not isinstance(novas_dependencias, list):
                raise ValueError("Formato inválido")
        except (json.JSONDecodeError, ValueError):
            messages.error(request, "Erro ao processar dependências.")
            return redirect('dependencia_editar', pk=pk)

        DependenciaItem.objects.filter(cadastro=dependencia).delete()

        deps_adicionadas = []
        for item in novas_dependencias:
            tipo = item.get('tipo')
            iddep = item.get('iddependente')
            if tipo in ['sql', 'relatorio', 'formula'] and iddep:
                DependenciaItem.objects.create(
                    cadastro=dependencia,
                    tipo=tipo,
                    id_dependente=str(iddep)  # CORRIGIDO
                )
                deps_adicionadas.append(f"{tipo.upper()}: {iddep}")

        if deps_adicionadas:
            mudou = True
            mudancas.append(f"Dependências atualizadas: {', '.join(deps_adicionadas)}")

        if mudou:
            dependencia.save()
            try:
                HistoricoAlteracao.objects.create(
                    objeto_tipo='dependencia',     # CORRIGIDO
                    objeto_id=str(pk),             # CORRIGIDO
                    titulo=dependencia.get_principal_label(),
                    usuario=request.user.username,
                    acao='Alteração',
                    descricao=' | '.join(mudancas),
                    valor_anterior=json.dumps({
                        'prioridade': prioridade_anterior,
                        'observacoes': observacoes_anterior,
                        'dependencias': [{'tipo': t, 'id': i} for t, i in deps_anteriores]
                    }),
                    valor_atual=json.dumps({
                        'prioridade': prioridade_nova,
                        'observacoes': observacoes,
                        'dependencias': deps_adicionadas
                    }),
                    status='aprovado',
                    data_alteracao=timezone.now()
                )
            except Exception as e:
                print(f"Erro ao criar histórico: {e}")
                traceback.print_exc()

            messages.success(request, "Dependência atualizada com sucesso!")
        else:
            messages.info(request, "Nenhuma alteração foi realizada.")

        return redirect('dependencias')

    # === GET: DADOS PARA O TEMPLATE ===

    principal_label = dependencia.get_principal_label() if hasattr(dependencia, 'get_principal_label') else 'Nenhum'
    principal_tipo = dependencia.get_principal_tipo() if hasattr(dependencia, 'get_principal_tipo') else ''

    # ===== 1. SQLs Disponíveis =====
    sqls_list = []
    try:
        for sql in CustomizacaoSQL.objects.all():
            sqls_list.append({
                'id': sql.codsentenca,
                'label': f"{sql.codsentenca} - {sql.titulo or 'Sem título'}"
            })
        print(f"{len(sqls_list)} SQLs encontrados")
    except Exception as e:
        print(f"Erro ao buscar SQLs: {e}")
        traceback.print_exc()

    # ===== 2. Relatórios Disponíveis (SEM ativo=True) =====
    relatorios_list = []
    try:
        for rep in CustomizacaoReport.objects.all():
            relatorios_list.append({
                'id': int(rep.id),
                'label': f"{rep.id} - {rep.codigo or 'Sem código'} ({(rep.descricao or 'Sem descrição')[:50]})"
            })
        print(f"{len(relatorios_list)} Relatórios encontrados")
    except Exception as e:
        print(f"Erro ao buscar Relatórios: {e}")
        traceback.print_exc()

    # ===== 3. Fórmulas/Visões Disponíveis =====
    formulas_list = []
    try:
        for fv in CustomizacaoFV.objects.filter(ativo=True):
            formulas_list.append({
                'id': int(fv.id),
                'label': f"{fv.id} - {fv.nome or 'Sem nome'} ({(fv.descricao or 'Sem descrição')[:50]})"
            })
        print(f"{len(formulas_list)} Fórmulas encontradas")
    except Exception as e:
        print(f"Erro ao buscar Fórmulas: {e}")
        traceback.print_exc()

    # ===== 4. Tabelas principais =====
    tabelas_principais = []
    for sql in sqls_list:
        tabelas_principais.append(f"SQL: {sql['label']}")
    for rep in relatorios_list:
        tabelas_principais.append(f"REP: {rep['label']}")
    for fv in formulas_list:
        tabelas_principais.append(f"FV: {fv['label']}")

    # ===== 5. Dependências disponíveis =====
    dependencias_disponiveis = {
        'sql': sqls_list,
        'relatorio': relatorios_list,
        'formula': formulas_list
    }

    print(f"Dependências Disponíveis:")
    print(f" - SQL: {len(sqls_list)}")
    print(f" - Relatório: {len(relatorios_list)}")
    print(f" - Fórmula: {len(formulas_list)}")

    # ===== 6. Dependências atuais =====
    deps_atuais = list(
        DependenciaItem.objects.filter(cadastro=dependencia).values('tipo', 'id_dependente')
    )

    context = {
        'dependencia': dependencia,
        'principal_label': principal_label,
        'principal_tipo': principal_tipo,
        'tabelas_principais': json.dumps(tabelas_principais),
        'dependencias_disponiveis': json.dumps(dependencias_disponiveis),
        'dependencias_atuais': json.dumps(deps_atuais),
        'active_page': 'dependencias',
    }

    return render(request, 'dashboard/dependencia_editar.html', context)
@login_required
def dependencia_excluir_view(request, pk):
    """Excluir dependência"""
    if request.method == 'POST':
        dep = get_object_or_404(CadastroDependencias, pk=pk)
        dep.delete()
        messages.success(request, 'Dependência excluída com sucesso!')
        return redirect('dependencias')
    return redirect('dependencias')

# ============================================================================
# NOTIFICAÇÕES
# ============================================================================


@login_required
def notificacoes_view(request):
    """Exibir notificações"""
    contadores = Notificacao.objects.filter(
        id_usuario=request.user.username, lida=False
    ).values('prioridade').annotate(total=Count('id'))
    alta_count = next((c['total'] for c in contadores if c['prioridade'] == 'Alta'), 0)
    media_count = next((c['total'] for c in contadores if c['prioridade'] == 'Média'), 0)
    baixa_count = next((c['total'] for c in contadores if c['prioridade'] == 'Baixa'), 0)
    notificacoes = Notificacao.objects.filter(id_usuario=request.user.username).order_by('-data_hora')
    return render(request, 'dashboard/notificacoes.html', {
        'notificacoes': notificacoes,
        'alta_count': alta_count,
        'media_count': media_count,
        'baixa_count': baixa_count,
        'active_page': 'notificacoes'
    })

@login_required
def marcar_lida_view(request, pk):
    """Marcar notificação como lida"""
    notif = get_object_or_404(Notificacao, pk=pk, id_usuario=request.user.username)
    if request.method == 'POST':
        notif.lida = True
        notif.save()
        messages.success(request, 'Notificação validada.')
        return redirect('notificacoes')
    return redirect('notificacoes')

# ============================================================================
# SQL
# ============================================================================

@login_required
def sql_view(request, pk=None):
    """Listar ou visualizar SQLs"""
    if pk:
        sql = get_object_or_404(CustomizacaoSQL, pk=pk)
        return render(request, 'dashboard/sql_detalhe.html', {'sql': sql})
    else:
        sqls = CustomizacaoSQL.objects.order_by('titulo')[:20]
        return render(request, 'dashboard/sql.html', {'sqls': sqls, 'active_page': 'sql'})

# ============================================================================
# FÓRMULAS
# ============================================================================

@login_required
def formula_view(request, pk=None):
    """Listar ou visualizar fórmulas"""
    if pk:
        formula = get_object_or_404(CustomizacaoFV, pk=pk)
        return render(request, 'dashboard/formula_detalhe.html', {'formula': formula})
    else:
        formulas = CustomizacaoFV.objects.filter(ativo=True).order_by('nome')[:20]
        return render(request, 'dashboard/formulas.html', {'formulas': formulas, 'active_page': 'formulas'})

# ============================================================================
# TABELAS
# ============================================================================

@login_required
def tabelas_view(request):
    """Listar tabelas do banco"""
    tabelas_set = set()
    for sql in CustomizacaoSQL.objects.values_list('sentenca', flat=True):
        if sql:
            found = re.findall(r'\bFROM\s+([A-Z_][A-Z0-9_]*)\b', sql, re.I)
            tabelas_set.update(found)
    tabelas = [{'nome': t, 'registros': 0} for t in sorted(tabelas_set)]
    return render(request, 'dashboard/tabelas.html', {'tabelas': tabelas, 'active_page': 'tabelas'})
