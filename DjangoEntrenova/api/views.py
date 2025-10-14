from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
import os
import google.generativeai as genai

try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("A chave da API do Gemini não foi configurada no ambiente.")
    
    genai.configure(api_key=api_key)

    SYSTEM_PROMPT = "Seu objetivo é ser um assistente amigável e educado, seu objetivo é extrair todas as informações da empresa de quem está digitando, como quantidade de funcionários, porte de empresa, cargo de quem está digitando..., Não devolva DE FORMA ALGUMA respostas que contenham ** como forma de negrito"
    
    MODEL = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_PROMPT
    )
except Exception as e:
    print(f"ERRO CRÍTICO: Falha ao inicializar o modelo Gemini: {e}")
    MODEL = None


class ChatbotView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not MODEL:
            return Response(
                {"error": "O serviço de IA não está configurado corretamente no servidor."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        history_from_frontend = request.data.get('history')
        
        if not history_from_frontend or not isinstance(history_from_frontend, list):
            return Response(
                {"error": "O campo 'history' é inválido ou não foi fornecido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        latest_user_message_obj = history_from_frontend[-1]
        user_message_text = latest_user_message_obj.get('content', '')
        conversation_history_for_api = history_from_frontend[:-1]
    
        api_history_formatted = []
        for message in conversation_history_for_api:
            role = 'model' if message.get('role') == 'bot' else 'user'
            
            api_history_formatted.append({
                'role': role,
                'parts': [{'text': message.get('content', '')}]
            })
        
        try:
            chat_session = MODEL.start_chat(history=api_history_formatted)
            response = chat_session.send_message(user_message_text)
            
            return Response(
                {'reply': response.text},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(f"Erro na comunicação com a API do Gemini: {e}")
            return Response(
                {"error": "Ocorreu um erro ao se comunicar com o serviço de IA."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class funcionarios(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        nome = request.data.get("nome")
        sobrenome = request.data.get("sobrenome")
        cpf = request.data.get("cpf")
        email = request.data.get("email")
        telefone = request.data.get("telefone")
        nascimento = request.data.get("nascimento")
        senha = request.data.get("senha")

        print("--- DADOS DO FUNCIONÁRIO RECEBIDOS ---")
        print(f"Nome: {nome}")
        print(f"Sobrenome: {sobrenome}")
        print(f"CPF: {cpf}")
        print(f"Email: {email}")
        print(f"Telefone: {telefone}")
        print(f"Nascimento: {nascimento}")
        print(f"Senha: {senha}")
        print("------------------------------------")
        
        return Response(
            {"message": "Funcionário recebido com sucesso!"},
            status=status.HTTP_201_CREATED
        )