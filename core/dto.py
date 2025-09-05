from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict
from uuid import uuid4, UUID

@dataclass
class CustomizacaoDTO:
    id: UUID = field(default_factory=uuid4)
    tipo: str = "OUTRO"           # FORMULA | SQL | RELATORIO | OUTRO
    nome: str = ""
    modulo: str = ""
    identificador_erp: str = ""
    descricao_tecnica: str = ""
    conteudo: str = ""
    status: str = "ATIVA"         # ATIVA | OBSOLETA | EM_REVISAO
    criado_no_erp_em: Optional[datetime] = None
    alterado_no_erp_em: Optional[datetime] = None
    versao: str = ""
    responsavel: str = ""
    responsavel_email: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class DependenciaDTO:
    id: UUID = field(default_factory=uuid4)
    origem: UUID = None
    destino: UUID = None
    relacao: str = "DEPENDE_DE"
    observacao: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class AlteracaoDTO:
    id: UUID = field(default_factory=uuid4)
    customizacao: UUID = None
    acao: str = "ATUALIZACAO"     # CRIACAO | ATUALIZACAO | EXCLUSAO | STATUS | DEPENDENCIA
    campos_alterados: Dict = field(default_factory=dict)
    comentario: str = ""
    ocorreu_em: datetime = field(default_factory=datetime.utcnow)

@dataclass
class NotificacaoDTO:
    id: UUID = field(default_factory=uuid4)
    customizacao: UUID = None
    tipo: str = "ALTERACAO"       # NOVO_REGISTRO | ALTERACAO
    mensagem: str = ""
    lida: bool = False
    criada_em: datetime = field(default_factory=datetime.utcnow)
