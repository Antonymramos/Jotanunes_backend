# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from customizacoes.models import Customizacao, Dependencia, Alteracao, Notificacao
from django.core.paginator import Paginator

@login_required(login_url='login')
def dashboard_view(request):
    # Resumo para cards do painel
    total_customizacoes = Customizacao.objects.count()
    alteracoes_pendentes = Alteracao.objects.filter().count()
    dependencias_ativas = Dependencia.objects.filter(ativo=True).count()
    novas_notificacoes = Notificacao.objects.filter(lida=False, destinatario=request.user).count()
    context = {
        "total_alertas": total_customizacoes,
        "alteracoes": alteracoes_pendentes,
        "em_atencao": dependencias_ativas,
        "novas_notificacoes": novas_notificacoes,
        "active_page": "dashboard",
    }
    return render(request, "dashboard/index.html", context)


@login_required(login_url='login')
def historico_view(request):
    qs = Alteracao.objects.select_related('customizacao', 'ator').order_by('-created')
    paginator = Paginator(qs, 25)
    page = request.GET.get('page', 1)
    historico = paginator.get_page(page)
    return render(request, "dashboard/historico.html", {"historico": historico, "active_page": "historico"})


@login_required(login_url='login')
def verificacao_view(request, pk=None):
    """
    Se pk for informado, carregar a customização alvo da verificação.
    Caso contrário, renderizar a tela em branco para seleção.
    """
    versao_antiga = ""
    versao_nova = ""
    if pk:
        obj = get_object_or_404(Customizacao, pk=pk)
        # Ex.: comparar conteudo atual com última alteração (se houver)
        versao_nova = obj.conteudo or ""
        last_alt = Alteracao.objects.filter(customizacao=obj).order_by("-created").first()
        versao_antiga = last_alt.campos_alterados.get("conteudo") if last_alt and isinstance(last_alt.campos_alterados, dict) else ""
    return render(request, "dashboard/verificacao.html", {
        "versao_antiga": versao_antiga,
        "versao_nova": versao_nova,
        "active_page": "verificacao",
    })


@login_required(login_url='login')
def dependencias_view(request):
    # Exibe botões para SQL, Fórmulas e Tabelas
    return render(request, "dashboard/dependencias.html", {"active_page": "dependencias"})


@login_required(login_url='login')
def sql_view(request, pk=None):
    """
    Se pk fornecido, carrega a dependência SQL correspondente; caso contrário exibe lista.
    """
    query = ""
    dependencias = Dependencia.objects.filter(tipo__icontains="SQL").order_by("-created")[:50]
    if pk:
        d = get_object_or_404(Dependencia, pk=pk)
        query = d.conteudo or ""
    return render(request, "dashboard/sql.html", {
        "dependencias": dependencias,
        "query": query,
        "active_page": "dependencias",
    })


@login_required(login_url='login')
def formula_view(request):
    # Lista fórmulas (tipo FORMULA)
    formulas = Customizacao.objects.filter(tipo=Customizacao.TIPO_SQL if hasattr(Customizacao, 'TIPO_SQL') else "FORMULA")
    return render(request, "dashboard/formulas.html", {"formulas": formulas, "active_page": "dependencias"})


@login_required(login_url='login')
def tabelas_view(request):
    # Exemplo: listar tabelas relacionadas (se houver modelo que armazene metadados)
    tabelas = []  # caso exista modelo, trocar por query real
    # Povoar com dados de exemplo se preferir:
    # tabelas = [{"nome": "clientes", "registros": 1245}, ...]
    return render(request, "dashboard/tabelas.html", {"tabelas": tabelas, "active_page": "dependencias"})
