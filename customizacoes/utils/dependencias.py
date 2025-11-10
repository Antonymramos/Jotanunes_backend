from django.db.models import Q
from customizacoes.models import CustomizacaoSQL, CustomizacaoReport, CustomizacaoFV


def get_destinos_para_origem(tipo_origem, id_origem):
    """
    Busca destinos relacionados a qualquer tipo de origem.
    
    Args:
        tipo_origem: 'sql', 'report', ou 'fv'
        id_origem: ID/codsentenca da origem
    
    Returns:
        dict: {'sql': [], 'report': [], 'fv': []} com destinos filtrados
    """
    
    destinos = {'sql': [], 'report': [], 'fv': []}
    
    # Busca o objeto da origem para extrair texto relevante
    if tipo_origem == 'sql':
        origem = CustomizacaoSQL.objects.filter(codsentenca=id_origem).first()
        if not origem:
            return destinos
        texto_origem = f"{id_origem} {origem.titulo or ''}".upper()
    
    elif tipo_origem == 'report':
        origem = CustomizacaoReport.objects.filter(id=id_origem).first()
        if not origem:
            return destinos
        texto_origem = f"{id_origem} {origem.codigo or ''} {origem.descricao or ''}".upper()
    
    elif tipo_origem == 'fv':
        origem = CustomizacaoFV.objects.filter(id=id_origem).first()
        if not origem:
            return destinos
        texto_origem = f"{id_origem} {origem.nome or ''} {origem.descricao or ''}".upper()
    
    else:
        return destinos
    
    # === BUSCA DESTINOS ===
    
    # SQLs que citam a origem (raramente, mas possível)
    sqls = CustomizacaoSQL.objects.filter(
        Q(titulo__icontains=texto_origem) |
        Q(sentenca__icontains=id_origem)
    )  # ✅ CORRIGIDO: Parêntese fechado
    
    for s in sqls:
        destinos['sql'].append({
            'id': s.codsentenca,
            'texto': f"{s.codsentenca} - {s.titulo or 'Sem título'}"
        })
    
    # REPORTs que citam a origem
    reports = CustomizacaoReport.objects.filter(
        Q(descricao__icontains=texto_origem) |
        Q(codigo__icontains=id_origem)
    )  # ✅ CORRIGIDO: Parêntese fechado
    
    for r in reports:
        destinos['report'].append({
            'id': r.id,
            'texto': f"{r.id} - {r.codigo or ''} - {r.descricao or 'Sem descrição'}"
        })
    
    # FVs que citam a origem
    fvs = CustomizacaoFV.objects.filter(
        Q(descricao__icontains=texto_origem) |
        Q(nome__icontains=id_origem)
    )  # ✅ CORRIGIDO: Parêntese fechado
    
    for f in fvs:
        destinos['fv'].append({
            'id': f.id,
            'texto': f"{f.id} - {f.nome or ''} - {f.descricao or 'Sem descrição'}"
        })
    
    return destinos