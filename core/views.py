# core/views.py
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
import re
from customizacoes.models import (
    CadastroDependencias, Prioridade, Notificacao,
    CustomizacaoSQL, CustomizacaoReport, CustomizacaoFV
)


@login_required
def dashboard_view(request):
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
        'tipo': tipo
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def historico_view(request):
    tipo = request.GET.get('tipo', 'FV')
    historico = CadastroDependencias.objects.order_by('-data_criacao')[:20]
    return render(request, 'dashboard/historico.html', {
        'historico': historico,
        'tipo': tipo
    })


@login_required
def verificacao_view(request, pk=None):
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
                status = "ERRO"; detalhes.append("FV não encontrada")
            if dep.id_aud_sql and not CustomizacaoSQL.objects.filter(codsentenca=dep.id_aud_sql).exists():
                status = "ERRO"; detalhes.append("SQL não encontrada")
            if dep.id_aud_report and not CustomizacaoReport.objects.filter(id=dep.id_aud_report).exists():
                status = "ERRO"; detalhes.append("Report não encontrado")
            resultados.append({'dep': dep, 'status': status, 'detalhes': detalhes})
        return render(request, 'dashboard/verificacao.html', {'resultados': resultados})


@login_required
def dependencias_view(request):
    dependencias = CadastroDependencias.objects.all().order_by('-data_criacao')
    deps_com_dados = []

    for dep in dependencias:
        dados = {
            'id': dep.id,
            'id_aud_sql': dep.id_aud_sql,
            'id_aud_report': dep.id_aud_report,
            'id_aud_fv': dep.id_aud_fv,
            'data_criacao': dep.data_criacao,
            'criado_por': dep.criado_por,
            'prioridade_id': dep.id_prioridade,
            'prioridade_nivel': None,
            'origem_label': '—',
            'destino_label': '—',
        }

        # PRIORIDADE
        if dep.id_prioridade:
            try:
                p = Prioridade.objects.filter(id=dep.id_prioridade).values('nivel').first()
                if p:
                    dados['prioridade_nivel'] = p['nivel']
            except:
                dados['prioridade_nivel'] = 'Desconhecida'

        # === ORIGEM ===
        if dep.id_aud_sql:
            sql = CustomizacaoSQL.objects.filter(codsentenca=dep.id_aud_sql).values('codsentenca', 'titulo').first()
            if sql:
                label = f"SQL: {sql['codsentenca']}"
                if sql['titulo']:
                    label += f" - {sql['titulo']}"
                dados['origem_label'] = label
        elif dep.id_aud_report:
            rep = CustomizacaoReport.objects.filter(id=dep.id_aud_report).values('id', 'codigo').first()
            if rep:
                label = f"REP: {rep['id']}"
                if rep['codigo']:
                    label += f" - {rep['codigo']}"
                dados['origem_label'] = label
        elif dep.id_aud_fv:
            fv = CustomizacaoFV.objects.filter(id=dep.id_aud_fv).values('id', 'nome').first()
            if fv:
                label = f"FV: {fv['id']}"
                if fv['nome']:
                    label += f" - {fv['nome']}"
                dados['origem_label'] = label

        # === DESTINO (SEPARADO!) ===
        if dep.id_aud_sql and dep.id_aud_report:
            rep = CustomizacaoReport.objects.filter(id=dep.id_aud_report).values('id', 'codigo').first()
            if rep:
                label = f"REP: {rep['id']}"
                if rep['codigo']:
                    label += f" - {rep['codigo']}"
                dados['destino_label'] = label
        elif dep.id_aud_sql and dep.id_aud_fv:
            fv = CustomizacaoFV.objects.filter(id=dep.id_aud_fv).values('id', 'nome').first()
            if fv:
                label = f"FV: {fv['id']}"
                if fv['nome']:
                    label += f" - {fv['nome']}"
                dados['destino_label'] = label
        elif dep.id_aud_report and dep.id_aud_sql:
            sql = CustomizacaoSQL.objects.filter(codsentenca=dep.id_aud_sql).values('codsentenca', 'titulo').first()
            if sql:
                label = f"SQL: {sql['codsentenca']}"
                if sql['titulo']:
                    label += f" - {sql['titulo']}"
                dados['destino_label'] = label
        elif dep.id_aud_report and dep.id_aud_fv:
            fv = CustomizacaoFV.objects.filter(id=dep.id_aud_fv).values('id', 'nome').first()
            if fv:
                label = f"FV: {fv['id']}"
                if fv['nome']:
                    label += f" - {fv['nome']}"
                dados['destino_label'] = label
        elif dep.id_aud_fv and dep.id_aud_sql:
            sql = CustomizacaoSQL.objects.filter(codsentenca=dep.id_aud_sql).values('codsentenca', 'titulo').first()
            if sql:
                label = f"SQL: {sql['codsentenca']}"
                if sql['titulo']:
                    label += f" - {sql['titulo']}"
                dados['destino_label'] = label
        elif dep.id_aud_fv and dep.id_aud_report:
            rep = CustomizacaoReport.objects.filter(id=dep.id_aud_aud_report).values('id', 'codigo').first()
            if rep:
                label = f"REP: {rep['id']}"
                if rep['codigo']:
                    label += f" - {rep['codigo']}"
                dados['destino_label'] = label

        deps_com_dados.append(dados)

    return render(request, 'dashboard/dependencias.html', {
        'dependencias': deps_com_dados
    })

@login_required
def dependencia_cadastro_view(request):
    if request.method == 'POST':
        try:
            # === RECEBE MÚLTIPLOS ===
            id_aud_sql = request.POST.getlist('id_aud_sql') or []
            id_aud_report = request.POST.getlist('id_aud_report') or []
            id_aud_fv = request.POST.getlist('id_aud_fv') or []
            prioridade_raw = request.POST.get('id_prioridade', '').strip()

            # === COLETA ORIGENS E DESTINOS ===
            origens = []
            destinos = []

            # ORIGENS
            for item in id_aud_sql:
                if item.strip(): origens.append(('sql', item.strip()))
            for item in id_aud_report:
                if item.strip(): origens.append(('report', int(item)))
            for item in id_aud_fv:
                if item.strip(): origens.append(('fv', int(item)))

            # DESTINOS
            for item in id_aud_sql:
                if item.strip() and ('sql', item.strip()) not in origens:
                    destinos.append(('sql', item.strip()))
            for item in id_aud_report:
                if item.strip() and ('report', int(item)) not in origens:
                    destinos.append(('report', int(item)))
            for item in id_aud_fv:
                if item.strip() and ('fv', int(item)) not in origens:
                    destinos.append(('fv', int(item)))

            # VALIDAÇÃO
            if not origens or not destinos:
                raise ValueError("Selecione pelo menos 1 origem e 1 destino.")

            # PRIORIDADE
            id_prioridade = None
            if prioridade_raw and prioridade_raw.isdigit():
                try:
                    prioridade_obj = Prioridade.objects.get(id=int(prioridade_raw))
                    id_prioridade = prioridade_obj.id
                except Prioridade.DoesNotExist:
                    messages.warning(request, f"Prioridade ID {prioridade_raw} não existe.")

            # === CRIA MÚLTIPLAS DEPENDÊNCIAS ===
            dependencias_criadas = 0
            for tipo_o, valor_o in origens:
                for tipo_d, valor_d in destinos:
                    data = {
                        'criado_por': request.user.username or 'ANONYMOUS',
                        'id_prioridade': id_prioridade
                    }

                    # ORIGEM
                    if tipo_o == 'sql':
                        data['id_aud_sql'] = valor_o
                    elif tipo_o == 'report':
                        data['id_aud_report'] = valor_o
                    elif tipo_o == 'fv':
                        data['id_aud_fv'] = valor_o

                    # DESTINO
                    if tipo_d == 'sql':
                        data['id_aud_sql'] = valor_d
                    elif tipo_d == 'report':
                        data['id_aud_report'] = valor_d
                    elif tipo_d == 'fv':
                        data['id_aud_fv'] = valor_d

                    dep = CadastroDependencias(**data)
                    dep.full_clean()
                    dep.save()
                    dependencias_criadas += 1

            # === NOTIFICAÇÃO PARA GESTOR ===
            if id_prioridade and dependencias_criadas > 0:
                nivel = Prioridade.objects.get(id=id_prioridade).nivel
                gestor = User.objects.filter(username='gestor').first()
                if gestor:
                    Notificacao.objects.create(
                        titulo=f"{dependencias_criadas} dependências {nivel} criadas",
                        descricao=f"{request.user.username} cadastrou {dependencias_criadas} dependências com prioridade {nivel}.",
                        prioridade=nivel,
                        id_usuario=gestor.username
                    )

            messages.success(request, f'{dependencias_criadas} dependências cadastradas com sucesso!')
            return redirect('dependencias')

        except Exception as e:
            messages.error(request, f'Erro: {e}')

    # === GET ===
    sqls = CustomizacaoSQL.objects.values('codsentenca', 'titulo').order_by('titulo')
    reports = CustomizacaoReport.objects.values('id', 'codigo', 'descricao').order_by('codigo')
    fvs = CustomizacaoFV.objects.values('id', 'nome', 'descricao').order_by('nome')
    prioridades = Prioridade.objects.all().order_by('id')

    return render(request, 'dashboard/dependencia_cadastro.html', {
        'sqls': list(sqls),
        'reports': list(reports),
        'fvs': list(fvs),
        'prioridades': prioridades,
    })

@login_required
def notificacoes_view(request):
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
    })


@login_required
def marcar_lida_view(request, pk):
    notif = get_object_or_404(Notificacao, pk=pk, id_usuario=request.user.username)
    if request.method == 'POST':
        notif.lida = True
        notif.save()
        messages.success(request, 'Notificação validada.')
    return redirect('notificacoes')


@login_required
def sql_view(request, pk=None):
    if pk:
        sql = get_object_or_404(CustomizacaoSQL, pk=pk)
        return render(request, 'dashboard/sql_detalhe.html', {'sql': sql})
    else:
        sqls = CustomizacaoSQL.objects.order_by('titulo')[:20]
        return render(request, 'dashboard/sql.html', {'sqls': sqls})


@login_required
def formula_view(request):
    formulas = CustomizacaoFV.objects.filter(ativo=True).order_by('nome')[:20]
    return render(request, 'dashboard/formulas.html', {'formulas': formulas})


@login_required
def tabelas_view(request):
    tabelas_set = set()
    for sql in CustomizacaoSQL.objects.values_list('sentenca', flat=True):
        if sql:
            found = re.findall(r'\bFROM\s+([A-Z_][A-Z0-9_]*)\b', sql, re.I)
            tabelas_set.update(found)
    
    tabelas = [{'nome': t, 'registros': 0} for t in sorted(tabelas_set)]
    return render(request, 'dashboard/tabelas.html', {'tabelas': tabelas})