from django.contrib import admin
from django.http import HttpResponse
from io import BytesIO
import csv

from .models import Customizacao, Dependencia, Alteracao, Notificacao,Assinatura


# ========= AÇÕES DE EXPORTAÇÃO =========

def export_customizacoes_csv(modeladmin, request, queryset):
    headers = [
        "ID", "Tipo", "Nome", "Módulo", "Identificador ERP", "Status",
        "Versão", "Resp.", "E-mail", "Criado ERP", "Alterado ERP"
    ]
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="customizacoes.csv"'
    w = csv.writer(resp)
    w.writerow(headers)
    for c in queryset.order_by("nome"):
        w.writerow([
            str(c.pk), c.tipo, c.nome, c.modulo, c.identificador_erp, c.status,
            c.versao, c.responsavel, c.responsavel_email,
            c.criado_no_erp_em.isoformat() if c.criado_no_erp_em else "",
            c.alterado_no_erp_em.isoformat() if c.alterado_no_erp_em else "",
        ])
    return resp
export_customizacoes_csv.short_description = "Exportar CSV (seleção/filtro atual)"


def export_customizacoes_xlsx(modeladmin, request, queryset):
    try:
        from openpyxl import Workbook
    except ImportError:
        modeladmin.message_user(request, "Instale 'openpyxl' (pip install openpyxl).", level="error")
        return
    wb = Workbook()
    ws = wb.active
    ws.title = "Customizacoes"
    ws.append([
        "ID", "Tipo", "Nome", "Módulo", "Identificador ERP", "Status",
        "Versão", "Resp.", "E-mail", "Criado ERP", "Alterado ERP"
    ])
    for c in queryset.order_by("nome"):
        ws.append([
            str(c.pk), c.tipo, c.nome, c.modulo, c.identificador_erp, c.status,
            c.versao, c.responsavel, c.responsavel_email,
            c.criado_no_erp_em.isoformat() if c.criado_no_erp_em else "",
            c.alterado_no_erp_em.isoformat() if c.alterado_no_erp_em else "",
        ])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    resp = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="customizacoes.xlsx"'
    return resp
export_customizacoes_xlsx.short_description = "Exportar XLSX (seleção/filtro atual)"


def export_customizacoes_pdf(modeladmin, request, queryset):
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        modeladmin.message_user(request, "Instale 'reportlab' (pip install reportlab).", level="error")
        return

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20
    )
    styles = getSampleStyleSheet()

    data = [["ID", "Tipo", "Nome", "Módulo", "Identificador ERP", "Status", "Versão"]]
    for c in queryset.order_by("nome"):
        data.append([str(c.pk), c.tipo, c.nome, c.modulo, c.identificador_erp, c.status, c.versao])

    from reportlab.platypus import Table  # já importado acima, redundância segura
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.beige]),
    ]))

    story = [Paragraph("Relatório de Customizações", styles["Title"]), Spacer(1, 8), table]
    doc.build(story)

    pdf = buf.getvalue()
    buf.close()
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="customizacoes.pdf"'
    return resp
export_customizacoes_pdf.short_description = "Exportar PDF (seleção/filtro atual)"


# ========= ADMIN =========

@admin.register(Customizacao)
class CustomizacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "modulo", "status", "versao", "identificador_erp", "updated_at")
    search_fields = ("nome", "modulo", "descricao_tecnica", "conteudo", "identificador_erp")
    list_filter = ("tipo", "modulo", "status", "is_active")
    ordering = ("nome",)
    actions = [export_customizacoes_csv, export_customizacoes_xlsx, export_customizacoes_pdf]
    actions_on_top = True,
    actions_on_bottom = True,


@admin.register(Dependencia)
class DependenciaAdmin(admin.ModelAdmin):
    list_display = ("origem", "relacao", "destino", "observacao", "updated_at")
    list_filter = ("relacao",)
    search_fields = ("origem__nome", "destino__nome", "observacao")


@admin.register(Alteracao)
class AlteracaoAdmin(admin.ModelAdmin):
    list_display = ("customizacao", "acao", "ator", "ocorreu_em")
    list_filter = ("acao",)
    search_fields = ("customizacao__nome", "comentario")


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ("customizacao", "tipo", "mensagem", "lida", "criada_em")
    list_filter = ("tipo", "lida")
    search_fields = ("customizacao__nome", "mensagem")

@admin.register(Assinatura)
class AssinaturaAdmin(admin.ModelAdmin):
    list_display = ("usuario","escopo","modulo","customizacao","ativo")
    list_filter = ("escopo","ativo","modulo")
    search_fields = ("usuario__username","modulo","customizacao__nome")