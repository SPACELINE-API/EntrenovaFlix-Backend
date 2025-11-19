from rest_framework import serializers
from accounts.serializers import UsuarioSimplesSerializer
from .models import Ticket, TicketMensagem

class TicketMensagemSerializer(serializers.ModelSerializer):
    autor = UsuarioSimplesSerializer(read_only=True)

    class Meta:
        model = TicketMensagem
        fields = ['id', 'autor', 'texto', 'created_at']


class TicketSerializer(serializers.ModelSerializer):
    mensagens = TicketMensagemSerializer(many=True, read_only=True)
    autor = UsuarioSimplesSerializer(read_only=True)
    empresa = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 
            'assunto', 
            'autor', 
            'empresa', 
            'status', 
            'created_at', 
            'mensagens' 
        ]  