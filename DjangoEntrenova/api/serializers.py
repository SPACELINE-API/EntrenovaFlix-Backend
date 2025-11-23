from rest_framework import serializers
from accounts.serializers import UsuarioSimplesSerializer
from .models import Ticket, TicketMensagem, aprimoramentoPessoal


class TicketMensagemSerializer(serializers.ModelSerializer):
    autor_nome = serializers.ReadOnlyField(source='autor.nome')

    class Meta:
        model = TicketMensagem
        fields = ['id', 'autor_nome', 'texto', 'created_at']


class TicketSerializer(serializers.ModelSerializer):
    mensagens = TicketMensagemSerializer(many=True, read_only=True)
    autor_nome = serializers.ReadOnlyField(source='autor.nome')
    empresa_nome = serializers.ReadOnlyField(source='empresa.nome')
    encaminhado = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id', 
            'assunto', 
            'autor', 
            'empresa', 
            'status', 
            'created_at', 
            'mensagens',
            'autor_nome', 
            'empresa_nome',
            'encaminhado',      
        ]

    def get_encaminhado(self, obj):
        
        return obj.autor == "RH"
    
class AprimoramentoPessoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = aprimoramentoPessoal
        fields = ['id', 'resultado', 'created_at'] 
        read_only_fields = ['id', 'created_at']