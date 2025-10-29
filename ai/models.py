# ai/models.py
from django.db import models

class CustomizacaoEmbedding(models.Model):
    TIPO_CHOICES = [
        ("FV", "Fórmula Visual"),
        ("SQL", "Consulta SQL"),
        ("REPORT", "Relatório"),
    ]

    tipo = models.CharField(max_length=6, choices=TIPO_CHOICES)
    customizacao_id = models.IntegerField()

    vec = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("tipo", "customizacao_id")
        indexes = [models.Index(fields=["tipo", "customizacao_id"])]

    def __str__(self):
        return f"Embedding[{self.tipo}:{self.customizacao_id}]"

    @property
    def customizacao(self):
        from customizacoes.models import get_customizacoes
        return get_customizacoes(self.tipo).filter(id=self.customizacao_id).first()