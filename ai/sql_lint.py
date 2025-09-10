import re

RULES = [
    (re.compile(r"\bSELECT\s+\*\b", re.I), "Evite SELECT *. Especifique colunas."),
    (re.compile(r"\b(DELETE|UPDATE)\s+\w+\s*(;|$)", re.I), "DELETE/UPDATE sem WHERE."),
    (re.compile(r"\bNOLOCK\b", re.I), "Cuidado com NOLOCK (dirty reads)."),
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "DROP TABLE detectado — bloqueie em produção."),
]

def lint_sql(sql: str):
    issues = []
    for rx, msg in RULES:
        if rx.search(sql or ""):
            issues.append(msg)
    return issues
