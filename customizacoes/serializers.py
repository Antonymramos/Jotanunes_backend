from rest_framework import serializers
from .models import Customizacao, Dependencia, Alteracao, Notificacao

class AlteracaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alteracao
        fields = "__all__"

class NotificacaoSerializer(serializers.ModelSerializer):
    customizacao_nome = serializers.ReadOnlyField(source="customizacao.nome")
    origem_username = serializers.ReadOnlyField(source="origem.username")

    class Meta:
        model = Notificacao
        fields = [
            "id", "tipo", "mensagem", "lida", "criada_em",
            "customizacao", "customizacao_nome",
            "origem", "origem_username",
        ]
        read_only_fields = fields


class DependenciaSerializer(serializers.ModelSerializer):
    origem_nome = serializers.CharField(source="origem.nome", read_only=True)
    destino_nome = serializers.CharField(source="destino.nome", read_only=True)

    class Meta:
        model = Dependencia
        fields = ["id","origem","origem_nome","destino","destino_nome","relacao","observacao","created_at","updated_at"]

class CustomizacaoListSerializer(serializers.ModelSerializer):
    total_dependentes = serializers.IntegerField(source="dependencias_destino.count", read_only=True)

    class Meta:
        model = Customizacao
        fields = ["id","tipo","nome","modulo","status","versao","identificador_erp","total_dependentes","updated_at"]

class CustomizacaoDetailSerializer(serializers.ModelSerializer):
    dependencias_origem = DependenciaSerializer(many=True, read_only=True)
    dependencias_destino = DependenciaSerializer(many=True, read_only=True)
    alteracoes = AlteracaoSerializer(many=True, read_only=True)

    class Meta:
        model = Customizacao
        fields = "__all__"
