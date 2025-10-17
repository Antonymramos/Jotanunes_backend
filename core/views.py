from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from customizacoes.models import Customizacao, Alteracao, Dependencia, Notificacao
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator

@login_required(login_url='login')
def dashboard_view(request):
    total_customizacoes = Customizacao.get_queryset().count()
    alteracoes_pendentes = 0
    try:
        alteracoes_pendentes = Alteracao.objects.count()
    except ObjectDoesNotExist:
        pass
    dependencias_ativas = 0
    try:
        dependencias_ativas = Dependencia.objects.filter(relacao="ATIVA").count()
    except ObjectDoesNotExist:
        pass
    novas_notificacoes = 0
    try:
        novas_notificacoes = Notificacao.objects.filter(lida=False, destinatario=request.user).count()
    except ObjectDoesNotExist:
        pass
    alteracoes_recentes = []
    try:
        alteracoes_recentes = Alteracao.objects.select_related('ator').order_by('-ocorreu_em')[:4]  # Removido 'customizacao' temporariamente
    except ObjectDoesNotExist:
        pass

    context = {
        "total_alertas": total_customizacoes,
        "alteracoes": alteracoes_pendentes,
        "em_atencao": dependencias_ativas,
        "novas_notificacoes": novas_notificacoes,
        "alteracoes_recentes": alteracoes_recentes,
        "active_page": "dashboard",
    }
    return render(request, "dashboard/index.html", context)

@login_required(login_url='login')
def historico_view(request):
    qs = Alteracao.objects.select_related('ator').order_by('-ocorreu_em')  # Removido 'customizacao' temporariamente
    paginator = Paginator(qs, 25)
    page = request.GET.get('page', 1)
    historico = paginator.get_page(page)
    return render(request, "dashboard/historico.html", {"historico": historico, "active_page": "historico"})

@login_required(login_url='login')
def verificacao_view(request, pk=None):
    versao_antiga = ""
    versao_nova = ""
    if pk:
        obj = get_object_or_404(Customizacao.get_queryset(), pk=pk)
        versao_nova = obj.conteudo or ""
        last_alt = Alteracao.objects.filter(customizacao=obj).order_by("-created_at").first()
        versao_antiga = last_alt.campos_alterados.get("conteudo") if last_alt and isinstance(last_alt.campos_alterados, dict) else ""
    return render(request, "dashboard/verificacao.html", {
        "versao_antiga": versao_antiga,
        "versao_nova": versao_nova,
        "active_page": "verificacao",
    })

@login_required(login_url='login')
def dependencias_view(request):
    return render(request, "dashboard/dependencias.html", {"active_page": "dependencias"})

@login_required(login_url='login')
def sql_view(request, pk=None):
    query = ""
    dependencias = Dependencia.objects.filter(relacao__icontains="SQL").order_by("-created_at")[:50]
    if pk:
        d = get_object_or_404(Dependencia, pk=pk)
        query = d.observacao or ""
    return render(request, "dashboard/sql.html", {
        "dependencias": dependencias,
        "query": query,
        "active_page": "dependencias",
    })

@login_required(login_url='login')
def formula_view(request):
    formulas = Customizacao.get_queryset(tipo=Customizacao.FORMULA)
    return render(request, "dashboard/formulas.html", {"formulas": formulas, "active_page": "dependencias"})

@login_required(login_url='login')
def tabelas_view(request):
    tabelas = []  # Ajustar se houver modelo de tabelas
    return render(request, "dashboard/tabelas.html", {"tabelas": tabelas, "active_page": "dependencias"})

@login_required(login_url='login')
def dependencia_cadastro_view(request):
    if request.method == "POST":
        tipo = request.POST.get('tipo')
        origem_id = request.POST.get('origem')
        destino_id = request.POST.get('destino')
        variaveis = request.POST.get('variaveis', '').split(',')
        status = request.POST.get('status')
        origem = get_object_or_404(Customizacao.get_queryset(), pk=origem_id)
        destino = get_object_or_404(Customizacao.get_queryset(), pk=destino_id)
        observacao = ''
        if tipo == 'SQL':
            observacao = request.POST.get('observacao')
        elif tipo == 'FORMULA':
            observacao = request.POST.get('expressao')
        elif tipo == 'TABELA':
            observacao = request.POST.get('estrutura')
        dependencia = Dependencia.objects.create(
            origem=origem,
            destino=destino,
            relacao=status,
            observacao=observacao,
        )
        messages.success(request, f"Dependência {tipo} cadastrada com sucesso!")
        return redirect('dependencia_cadastro')
    customizacoes = Customizacao.get_queryset()
    impactos = []
    if request.method == "POST" and 'variaveis' in request.POST:
        for var in variaveis:
            var = var.strip()
            if var == "pessoa":
                impactos.append({
                    'dependencia': 'Outra Dependência',
                    'variavel': 'trabalhador',
                    'descricao': 'Alteração em "pessoa" pode afetar "trabalhador"'
                })
    return render(request, 'dashboard/dependencia_cadastro.html', {
        'customizacoes': customizacoes,
        'impactos': impactos,
    })