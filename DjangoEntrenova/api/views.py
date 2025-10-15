# api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny 
from .ai_service import gemini_service
import json
from rest_framework.permissions import IsAuthenticated 

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



class DiagnosticAIView(APIView):
    permission_classes = [AllowAny] 

    def _format_responses_for_prompt(self, responses):
        formatted_string = ""
        for item in responses:
            data = item
            if isinstance(item, str):
                try:
                    data = json.loads(item)
                except json.JSONDecodeError:
                    continue
            
            dimension = data.get('dimension', 'N/A')
            maturity = data.get('maturityStage', 'N/A')
            formatted_string += f"- Dimensão: {dimension}, Estágio de Maturidade: {maturity}\n"
        return formatted_string

    def post(self, request):
        if not gemini_service:
            return Response(
                {"error": "O serviço de IA não está disponível devido a um erro de configuração."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        diagnosis_responses = request.data.get('responses')
        if not diagnosis_responses:
            return Response(
                {"error": "Nenhuma resposta de diagnóstico foi fornecida."},
                status=status.HTTP_400_BAD_REQUEST
            )

        formatted_responses = self._format_responses_for_prompt(diagnosis_responses)

        system_prompt = """
              Você é um especialista em desenvolvimento organizacional e comunicação corporativa. 
              Sua tarefa é analisar os resultados de um diagnóstico de comunicação e engajamento 
              de uma empresa e fornecer uma análise detalhada e acionável.

              Com base nos dados a seguir, que representam a maturidade da empresa em diferentes dimensões, 
              gere um relatório em formato JSON contendo três seções principais: "fortes" (pontos fortes), 
              "fracos" (pontos a melhorar) e "recomendacao" (recomendações práticas).

              - Para "fortes", identifique as dimensões com os melhores resultados (estágios 'Estratégico' ou 'Otimizado').
              - Para "fracos", identifique as dimensões com os piores resultados (estágios 'Inicial' ou 'Reativo').
              - Para "recomendacao", forneça 3 a 5 sugestões claras e práticas para a empresa melhorar, 
                focando principalmente nos pontos fracos identificados. As recomendações devem ser acionáveis.

              Formate sua resposta EXCLUSIVAMENTE como um objeto JSON válido, com a seguinte estrutura:
              {
                "summary": {
                  "fortes": ["string", "string", ...],
                  "fracos": ["string", "string", ...],
                  "recomendacao": ["string", "string", ...]
                }
              }
        """

        user_message = f"Aqui estão os resultados do diagnóstico da empresa:\n{formatted_responses}"

        try:
            chat_session = gemini_service.start_chat_session(system_prompt)
            response = chat_session.send_message(user_message)
            cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()

            print(f"DEBUG: Resposta da IA (texto limpo): '{cleaned_text}'")
            
            ai_summary = json.loads(cleaned_text)

            print(f"DEBUG: JSON enviado para o frontend: {ai_summary}")    
                    
            return Response(ai_summary, status=status.HTTP_200_OK)

        except json.JSONDecodeError:
            print(f"ERRO: A IA retornou um JSON inválido. Resposta recebida: '{cleaned_text}'")
            return Response(
                {"error": "A IA retornou uma resposta em um formato JSON inválido."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            print(f"Erro na API do Gemini: {e}")
            return Response(
                {"error": "Ocorreu um erro ao processar a avaliação da IA."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
