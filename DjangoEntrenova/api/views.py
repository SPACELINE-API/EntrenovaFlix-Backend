from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .supabase_client import supabase
import os
import google.generativeai as genai
from rest_framework import status
from django.conf import settings
from rest_framework.permissions import AllowAny 

class ChatbotView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return Response(
                {"error": "A chave da API do Gemini não foi configurada no servidor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        genai.configure(api_key=api_key)

        user_message = request.data.get('message')
        history_from_frontend = request.data.get('history', [])

        if not user_message:
            return Response(
                {"error": "Nenhuma mensagem fornecida."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        system_prompt = "Seu objetivo é ser um assistente amigável e educado, seu objetivo é extrair todas as informações da empresa de quem está digitando, como quantidade de funcionários, porte de empresa, cargo de quem está digitando..."
        
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-001",
            system_instruction=system_prompt
        )

        api_history = []
        for message in history_from_frontend:
            if message.get('role') and message.get('text'):
                 api_history.append({
                    'role': message['role'],
                    'parts': [{'text': message['text']}]
                })

        try:
            chat_session = model.start_chat(history=api_history)
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
