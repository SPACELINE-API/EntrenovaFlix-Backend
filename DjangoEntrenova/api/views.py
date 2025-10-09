# api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny 
from .ai_service import gemini_service

class ChatbotView(APIView):
    permission_classes = [AllowAny] #Necessário mudança, qualquer um tem acesso

    def post(self, request):
        if not gemini_service:
            return Response(
                {"error": "O serviço de IA não está disponível devido a um erro de configuração."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        user_message = request.data.get('message')
        history = request.data.get('history', [])

        if not user_message:
            return Response(
                {"error": "Nenhuma mensagem fornecida."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        system_prompt = "Seu objetivo é ser um assistente amigável e educado, seu objetivo é extrair todas as informações da empresa de quem está digitando, como quantidade de funcionários, porte de empresa, cargo de quem está digitando..."
        
        try:
            chat_session = gemini_service.start_chat_session(system_prompt, history)
            response = chat_session.send_message(user_message)
            
            return Response(
                {'reply': response.text},
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            print(f"Erro na API do Gemini: {e}")
            return Response(
                {"error": "Ocorreu um erro ao se comunicar com a IA"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )