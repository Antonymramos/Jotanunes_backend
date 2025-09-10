from django.db import models
from customizacoes.models import Customizacao

class CustomizacaoEmbedding(models.Model):
    customizacao = models.OneToOneField(
        Customizacao, related_name="embedding", on_delete=models.CASCADE
    )
    # Guarda o vetor como lista de floats (teste em SQLite; depois migra p/ serviço vetorial se quiser)
    vec = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Embedding({self.customizacao_id})"
