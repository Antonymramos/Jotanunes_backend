from argparse import Action
import time
from rest_framework import viewsets, mixins, decorators, response, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Customizacao, Dependencia, Alteracao, Notificacao, CustomizacaoTipo
from .serializers import (
    CustomizacaoListSerializer, CustomizacaoDetailSerializer,
    DependenciaSerializer, AlteracaoSerializer, NotificacaoSerializer
)
from django.http import HttpResponse, JsonResponse
import csv, io, json
from django.contrib.auth.decorators import login_required

class CustomizacaoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo", "modulo", "status", "codcoligada"]

    def get_queryset(self):
        tipo = self.request.query_params.get("tipo", "").strip()
        return Customizacao.get_queryset(tipo=tipo)

    def get_serializer_class(self):
        if self.action in ["list"]:
            return CustomizacaoListSerializer
        return CustomizacaoDetailSerializer

    def get_permissions(self):
        open_actions = {
            "search", "advanced_search", "export_csv", "export_xlsx", "export_pdf",
            "dashboard", "semantic_search", "lint",
        }
        if getattr(self, "action", None) in open_actions:
            return [AllowAny()]
        return super().get_permissions()

    @Action(detail=False, methods=["get"], url_path="search", permission_classes=[AllowAny])
    def search(self, request):
        q = request.query_params.get("q", "").strip()
        qs = self.get_queryset()
        if q:
            qs = qs.filter(
                Q(nome__icontains=q)
                | Q(descricao_tecnica__icontains=q)
                | Q(conteudo__icontains=q)
                | Q(modulo__icontains=q)
                | Q(identificador_erp__icontains=q)
            )
        page = self.paginate_queryset(qs)
        ser = CustomizacaoListSerializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else response.Response(ser.data)

    @Action(detail=False, methods=["get"], url_path="advanced-search", permission_classes=[AllowAny])
    def advanced_search(self, request):
        q = request.query_params.get("q", "").strip()
        modulo = request.query_params.get("modulo", "").strip()
        tipo = request.query_params.get("tipo", "").strip()
        status_p = request.query_params.get("status", "").strip()
        campo_alterado = request.query_params.get("campo_alterado", "").strip()
        codcoligada = request.query_params.get("codcoligada", "").strip()

        qs = self.get_queryset()
        if q:
            qs = qs.filter(
                Q(nome__icontains=q)
                | Q(modulo__icontains=q)
                | Q(identificador_erp__icontains=q)
                | Q(descricao_tecnica__icontains=q)
                | Q(conteudo__icontains=q)
            )
        if modulo:
            qs = qs.filter(modulo__icontains=modulo)
        if tipo:
            qs = qs.filter(tipo=tipo)
        if status_p:
            qs = qs.filter(status=status_p)
        if codcoligada:
            qs = qs.filter(codcoligada=codcoligada)

        results = list(qs)
        if campo_alterado:
            ids = set()
            for alt in Alteracao.objects.filter(customizacao__in=results).only("customizacao_id", "campos_alterados"):
                if isinstance(alt.campos_alterados, dict) and campo_alterado in alt.campos_alterados.keys():
                    ids.add(alt.customizacao_id)
            results = [c for c in results if c.pk in ids]

        payload = []
        for c in results[:200]:
            highlight = None
            if q and c.conteudo:
                idx = c.conteudo.lower().find(q.lower())
                if idx >= 0:
                    start = max(0, idx - 40)
                    end = min(len(c.conteudo), idx + len(q) + 40)
                    highlight = c.conteudo[start:end]
            payload.append({
                "id": str(c.pk),
                "tipo": c.tipo,
                "nome": c.nome,
                "modulo": c.modulo,
                "identificador_erp": c.identificador_erp,
                "status": c.status,
                "versao": c.versao,
                "codcoligada": c.codcoligada,
                "highlight": highlight,
            })
        return response.Response({"count": len(payload), "results": payload})

    @Action(detail=False, methods=["get"], url_path="export/csv", permission_classes=[AllowAny])
    def export_csv(self, request):
        import csv, io
        qs = self.filter_queryset(self.get_queryset()).order_by("nome")
        tipos = _normalize_tipos(request)
        if tipos:
            qs = qs.filter(tipo__in=tipos)
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(["id", "tipo", "nome", "modulo", "status", "versao", "identificador_erp", "codcoligada"])
        for c in qs:
            writer.writerow([c.id, c.tipo, c.nome, c.modulo, c.status, c.versao, c.identificador_erp, c.codcoligada])
        resp = HttpResponse(stream.getvalue(), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="customizacoes.csv"'
        return resp

    @Action(detail=False, methods=["get"], url_path="export/xlsx", permission_classes=[AllowAny])
    def export_xlsx(self, request):
        try:
            from openpyxl import Workbook
        except ImportError:
            return response.Response(
                {"detail": "Instale 'openpyxl' (pip install openpyxl)."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        qs = self.filter_queryset(self.get_queryset()).order_by("nome")
        tipos = _normalize_tipos(request)
        if tipos:
            qs = qs.filter(tipo__in=tipos)
        wb = Workbook()
        ws = wb.active
        ws.title = "Customizacoes"
        headers = [
            "ID", "Tipo", "Nome", "Módulo", "Identificador ERP", "Status",
            "Versão", "Resp.", "E-mail", "Criado ERP", "Alterado ERP", "Codcoligada"
        ]
        ws.append(headers)
        for c in qs:
            ws.append([
                str(c.pk), c.tipo, c.nome, c.modulo, c.identificador_erp, c.status,
                c.versao, c.responsavel, c.responsavel_email,
                c.criado_no_erp_em.isoformat() if c.criado_no_erp_em else "",
                c.alterado_no_erp_em.isoformat() if c.alterado_no_erp_em else "",
                c.codcoligada,
            ])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        resp = HttpResponse(
            buf.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = 'attachment; filename="customizacoes.xlsx"'
        return resp

    @Action(detail=False, methods=["get"], url_path="export/pdf", permission_classes=[AllowAny])
    def export_pdf(self, request):
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError:
            return response.Response(
                {"detail": "Instale 'reportlab' (pip install reportlab)."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        qs_base = self.filter_queryset(self.get_queryset()).order_by("nome")
        tipos = _normalize_tipos(request)
        if tipos:
            qs_base = qs_base.filter(tipo__in=tipos)
        qs = qs_base.values_list(
            "pk", "tipo", "nome", "modulo", "identificador_erp", "status", "versao", "codcoligada"
        )
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=landscape(A4),
            leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20
        )
        styles = getSampleStyleSheet()
        data = [["ID", "Tipo", "Nome", "Módulo", "Identificador ERP", "Status", "Versão", "Codcoligada"]]
        for row in qs:
            data.append([str(row[0]), row[1], row[2], row[3], row[4], row[5], row[6], row[7]])
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
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

    @Action(detail=False, methods=["get"], url_path="dashboard", permission_classes=[AllowAny])
    def dashboard(self, request):
        total = Customizacao.get_queryset().count()
        by_status = list(Customizacao.get_queryset().values("status").annotate(qtd=Count("id")).order_by("-qtd"))
        by_tipo = list(Customizacao.get_queryset().values("tipo").annotate(qtd=Count("id")).order_by("-qtd"))
        top_modulos = list(
            Customizacao.get_queryset().exclude(modulo="")
            .values("modulo").annotate(qtd=Count("id")).order_by("-qtd")[:10]
        )
        recentes = list(
            Alteracao.objects.select_related("customizacao")
            .order_by("-ocorreu_em").values("acao", "ocorreu_em", "customizacao_id", "customizacao__nome")[:10]
        )
        mais_dependem = list(
            Customizacao.get_queryset().annotate(qtd=Count("dependencias_origem"))
            .filter(qtd__gt=0).values("id", "nome", "qtd").order_by("-qtd")[:10]
        )
        mais_referenciadas = list(
            Customizacao.get_queryset().annotate(qtd=Count("dependencias_destino"))
            .filter(qtd__gt=0).values("id", "nome", "qtd").order_by("-qtd")[:10]
        )
        return response.Response({
            "total": total,
            "by_status": by_status,
            "by_tipo": by_tipo,
            "top_modulos": top_modulos,
            "alteracoes_recentes": recentes,
            "mais_dependem": mais_dependem,
            "mais_referenciadas": mais_referenciadas,
        })

    @Action(detail=False, methods=["get"], url_path="semantic-search", permission_classes=[AllowAny])
    def semantic_search(self, request):
        from ai.models import CustomizacaoEmbedding
        from ai.services import embed_text, cosine
        q = (request.query_params.get("q") or "").strip()
        k = int(request.query_params.get("k", 20))
        if not q:
            return response.Response({"detail": "param q obrigatório (?q=...)"}, status=400)
        qvec = embed_text(q)
        hits = []
        for emb in CustomizacaoEmbedding.objects.select_related("customizacao"):
            score = round(cosine(qvec, emb.vec or []), 4)
            c = emb.customizacao
            hits.append({
                "id": str(c.pk), "score": score,
                "nome": c.nome, "tipo": c.tipo, "modulo": c.modulo,
                "status": c.status, "identificador_erp": c.identificador_erp,
                "codcoligada": c.codcoligada,
            })
        hits.sort(key=lambda x: x["score"], reverse=True)
        return response.Response({"results": hits[:k]})

    @Action(detail=True, methods=["post"], url_path="lint")
    def lint(self, request, pk=None):
        from ai.sql_lint import lint_sql
        obj = self.get_object()
        issues = lint_sql(obj.conteudo or "")
        return response.Response({"issues": issues, "ok": len(issues) == 0})

# Função auxiliar para normalizar tipos
def _normalize_tipos(request):
    raw = request.query_params.getlist("tipo") or _parse_multi(request.query_params.get("tipo"))
    if not raw:
        return []
    value_map = {value.lower(): value for value, _ in CustomizacaoTipo.choices}
    label_map = {label.lower(): value for value, label in CustomizacaoTipo.choices}
    out = []
    for item in raw:
        k = item.lower()
        out.append(value_map.get(k) or label_map.get(k))
    return [x for x in out if x]

class DependenciaViewSet(viewsets.ModelViewSet):
    queryset = Dependencia.objects.select_related("origem", "destino")
    serializer_class = DependenciaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["relacao", "origem", "destino"]

class AlteracaoViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Alteracao.objects.select_related("customizacao", "ator")
    serializer_class = AlteracaoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["acao", "customizacao"]

class NotificacaoViewSet(viewsets.ModelViewSet):
    serializer_class = NotificacaoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo", "lida", "customizacao"]

    def get_queryset(self):
        u = self.request.user
        if not u.is_authenticated:
            return Notificacao.objects.none()
        return Notificacao.objects.select_related("customizacao", "origem").filter(
            Q(destinatario=u) | Q(destinatario__isnull=True)
        ).order_by("-criada_em")

    @Action(detail=False, methods=["get"], url_path="unread")
    def unread(self, request):
        qs = self.get_queryset().filter(lida=False)[:200]
        return response.Response(self.get_serializer(qs, many=True).data)

    @Action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        n = self.get_object()
        n.lida = True
        n.save(update_fields=["lida"])
        return response.Response({"ok": True})

    @Action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        count = self.get_queryset().filter(lida=False).update(lida=True)
        return response.Response({"updated": count})

    @Action(detail=False, methods=["get"], url_path="stream")
    def stream(self, request):
        if not request.user.is_authenticated:
            return HttpResponse(status=401)
        try:
            last_id = int(request.GET.get("last_id", "0") or 0)
        except ValueError:
            last_id = 0
        user = request.user

        def gen():
            nonlocal last_id
            for _ in range(60):
                news = Notificacao.objects.filter(
                    destinatario=user, id__gt=last_id
                ).order_by("id")[:50]
                for n in news:
                    payload = {
                        "id": n.id,
                        "tipo": n.tipo,
                        "mensagem": n.mensagem,
                        "customizacao_id": str(n.customizacao_id),
                        "criada_em": n.criada_em.isoformat(),
                    }
                    yield f"event: alerta\ndata: {json.dumps(payload)}\nid: {n.id}\n\n"
                    last_id = n.id
                time.sleep(1)
            yield "event: ping\ndata: {}\n\n"

        resp = HttpResponse(gen(), content_type="text/event-stream")
        resp["Cache-Control"] = "no-cache"
        resp["X-Accel-Buffering"] = "no"
        return resp

@login_required(login_url="login")
def carregar_dependencias(request):
    data = {
        "status": "ok",
        "dependencias": ["django", "pandas", "numpy"]
    }
    return JsonResponse(data)