# core/api_views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from customizacoes.models import (
    CadastroDependencias, Prioridade,
    CustomizacaoSQL, CustomizacaoReport, CustomizacaoFV
)


@login_required
@require_http_methods(["GET"])
def dependencia_detalhe_api(request, pk):
    try:
        dep = CadastroDependencias.objects.get(pk=pk)

        # === ORIGEM ===
        origem = {}
        if dep.id_aud_sql:
            sql = CustomizacaoSQL.objects.filter(codsentenca=dep.id_aud_sql).first()
            if sql:
                origem = {
                    'tipo': 'SQL',
                    'codsentenca': sql.codsentenca,
                    'titulo': sql.titulo or '—',
                    'aplicacao': sql.aplicacao or '—',
                    'sentenca': sql.sentenca or '—',
                    'tamanho': sql.tamanho,
                    'reccreatedby': sql.reccreatedby,
                    'reccreatedon': sql.reccreatedon.strftime('%d/%m/%Y %H:%M') if sql.reccreatedon else '—',
                }
        elif dep.id_aud_report:
            rep = CustomizacaoReport.objects.filter(id=dep.id_aud_report).first()
            if rep:
                origem = {
                    'tipo': 'REPORT',
                    'id': rep.id,
                    'codigo': rep.codigo or '—',
                    'descricao': rep.descricao or '—',
                    'codaplicacao': rep.codaplicacao,
                    'codcoligada': rep.codcoligada,
                    'reccreatedby': rep.reccreatedby,
                    'reccreatedon': rep.reccreatedon.strftime('%d/%m/%Y %H:%M') if rep.reccreatedon else '—',
                }
        elif dep.id_aud_fv:
            fv = CustomizacaoFV.objects.filter(id=dep.id_aud_fv).first()
            if fv:
                origem = {
                    'tipo': 'FV',
                    'id': fv.id,
                    'nome': fv.nome or '—',
                    'descricao': fv.descricao or '—',
                    'ativo': 'Sim' if fv.ativo else 'Não',
                    'codcoligada': fv.codcoligada,
                    'idcategoria': fv.idcategoria,
                    'reccreatedby': fv.reccreatedby,
                    'reccreatedon': fv.reccreatedon.strftime('%d/%m/%Y %H:%M') if fv.reccreatedon else '—',
                }

        # === DESTINOS (múltiplos) ===
        destinos = []
        if dep.id_aud_sql and dep.id_aud_report:
            rep = CustomizacaoReport.objects.filter(id=dep.id_aud_report).first()
            if rep:
                destinos.append({
                    'tipo': 'REPORT',
                    'id': rep.id,
                    'codigo': rep.codigo or '—',
                    'descricao': rep.descricao or '—',
                    'codaplicacao': rep.codaplicacao,
                    'codcoligada': rep.codcoligada,
                    'reccreatedby': rep.reccreatedby,
                    'reccreatedon': rep.reccreatedon.strftime('%d/%m/%Y %H:%M') if rep.reccreatedon else '—',
                })
        if dep.id_aud_fv and dep.id_aud_sql:
            fv = CustomizacaoFV.objects.filter(id=dep.id_aud_fv).first()
            if fv:
                destinos.append({
                    'tipo': 'FV',
                    'id': fv.id,
                    'nome': fv.nome or '—',
                    'descricao': fv.descricao or '—',
                    'ativo': 'Sim' if fv.ativo else 'Não',
                    'codcoligada': fv.codcoligada,
                    'idcategoria': fv.idcategoria,
                    'reccreatedby': fv.reccreatedby,
                    'reccreatedon': fv.reccreatedon.strftime('%d/%m/%Y %H:%M') if fv.reccreatedon else '—',
                })

        # === PRIORIDADE ===
        nivel = 'Sem prioridade'
        badge_class = 'bg-secondary'
        if dep.id_prioridade:
            try:
                p = Prioridade.objects.get(id=dep.id_prioridade)
                nivel = p.nivel
                badge_class = 'bg-danger' if nivel == 'Alta' else 'bg-warning text-dark' if nivel == 'Média' else 'bg-success'
            except:
                pass

        return JsonResponse({
            'origem': origem,
            'destinos': destinos,
            'id_prioridade': dep.id_prioridade,
            'prioridade_badge': f'<span class="badge {badge_class}">{nivel}</span>',
            'criado_por': dep.criado_por,
            'data_criacao': dep.data_criacao.strftime('%d/%m/%Y %H:%M')
        })
    except CadastroDependencias.DoesNotExist:
        return JsonResponse({'error': 'Não encontrada'}, status=404)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def dependencia_editar_api(request, pk):
    try:
        dep = CadastroDependencias.objects.get(pk=pk)
        prioridade_id = request.POST.get('id_prioridade', '').strip()

        if prioridade_id == '' or prioridade_id is None:
            dep.id_prioridade = None
        else:
            dep.id_prioridade = int(prioridade_id)

        dep.full_clean()
        dep.save()

        nivel = 'Sem prioridade'
        badge_class = 'bg-secondary'
        if dep.id_prioridade:
            try:
                p = Prioridade.objects.get(id=dep.id_prioridade)
                nivel = p.nivel
                badge_class = 'bg-danger' if nivel == 'Alta' else 'bg-warning text-dark' if nivel == 'Média' else 'bg-success'
            except:
                nivel = 'Desconhecida'

        return JsonResponse({
            'success': True,
            'prioridade_html': f'<span class="badge {badge_class}">{nivel}</span>'
        })
    except CadastroDependencias.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Dependência não encontrada'}, status=404)
    except ValueError:
        return JsonResponse({'success': False, 'error': 'ID de prioridade inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)