import os, math, hashlib, random
from typing import List

# Modo real (OpenAI) se houver chave; caso contrário, mock determinístico p/ dev
_OPENAI_KEY = os.getenv("OPENAI_API_KEY")

def _mock_embed(text: str, dim: int = 384) -> List[float]:
    """Gera um vetor determinístico (não-aleatório) p/ testes, sem dependência externa."""
    seed = int(hashlib.sha256((text or "").encode("utf-8")).hexdigest(), 16) % (10**8)
    rnd = random.Random(seed)
    v = [rnd.uniform(-1.0, 1.0) for _ in range(dim)]
    # normaliza
    norm = math.sqrt(sum(x*x for x in v)) or 1.0
    return [x / norm for x in v]

def embed_text(text: str) -> List[float]:
    if not _OPENAI_KEY:
        return _mock_embed(text)
    # OpenAI oficial (requer: pip install openai)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=_OPENAI_KEY)
        text = (text or "").replace("\n", " ")[:8000]
        out = client.embeddings.create(model="text-embedding-3-small", input=text)
        return out.data[0].embedding
    except Exception:
        # se der qualquer erro, volta pro mock (não quebra fluxo)
        return _mock_embed(text)

def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b: return 0.0
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a)) or 1.0
    nb = math.sqrt(sum(y*y for y in b)) or 1.0
    return dot / (na * nb)
