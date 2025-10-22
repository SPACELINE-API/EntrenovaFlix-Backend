# api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.models import Empresa, Usuario
from .supabase_client import supabase
from .ai_service import gemini_service
from rest_framework.permissions import IsAuthenticated, AllowAny
import json

class AprovarPagamentoView (APIView):
    permission_classes = [AllowAny]
    def post(self, request, cnpj):
        try:
            empresa = Empresa.objects.get(cnpj=cnpj)
            empresa.aprovar_pagamento()
            return Response({"message": "Pagamento aprovado"}, status=status.HTTP_200_OK)
        except Empresa.DoesNotExist:
            return Response ({"error": "Empresa não encontrada"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
             return Response ({"error": f"Erro ao aprovar pagamento: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ChatbotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        empresa = user.empresa

        if not empresa:
            return Response(
                {"error": "Usuário não está vinculado a uma empresa. Acesso negado."},
                status=status.HTTP_403_FORBIDDEN
            )

        if empresa.status_pagamento != "aprovado":
            return Response(
                {"error": "Pagamento pendente. O acesso ao diagnóstico aprofundado está bloqueado"},
                status=status.HTTP_402_PAYMENT_REQUIRED
            ) 
        
        if not gemini_service:
            return Response(
                {"error": "O serviço de IA não está disponível devido a um erro de configuração"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        user_message = request.data.get('message')
        history = request.data.get('history', [])

        if not user_message:
            return Response(
                {"error": "O campo 'history' é inválido ou não foi fornecido."},
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
            print(f"Erro na comunicação com a API do Gemini: {e}")
            return Response(
                {"error": "Ocorreu um erro ao se comunicar com o serviço de IA."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DiagnosticAIView(APIView):
    permission_classes = [AllowAny]

    DIMENSION_MAPPING = {
        "pessoasCultura": {
            "title": "Pessoas & Cultura",
            "questions": {
                "1": "Comunicação e Alinhamento", "2": "Liderança e Engajamento", "3": "Resolução de Problemas",
                "4": "Rotina e Processos", "5": "Valores e Comportamentos", "6": "Ferramentas e Recursos"
            }
        },
        "estruturaOperacoes": {
            "title": "Estrutura & Operações",
            "questions": {
                "1": "Troca de Informações", "2": "Delegação e Responsabilidades", "3": "Processos e Fluxos",
                "4": "Autonomia e Tomada de Decisão", "5": "Qualidade e Melhoria Contínua", "6": "Ferramentas e Sistemas"
            }
        },
        "mercadoClientes": {
            "title": "Mercado & Clientes",
            "questions": {
                "1": "Escuta Ativa do Cliente", "2": "Colaboração com Clientes", "3": "Reação a Mudanças de Mercado",
                "4": "Metas e Indicadores de Cliente", "5": "Diferencial Competitivo", "6": "Ferramentas de Relacionamento"
            }
        },
        "direcaoFuturo": {
            "title": "Direção & Futuro",
            "questions": {
                "1": "Visão de Futuro", "2": "Estratégia e Planejamento", "3": "Inovação e Experimentação",
                "4": "Conexão da Estratégia com o Dia a Dia", "5": "Propósito e Missão", "6": "Ferramentas de Gestão Estratégica"
            }
        }
    }

    def _call_gemini_api(self, system_prompt, user_message):
        try:
            chat_session = gemini_service.start_chat_session(system_prompt)
            response = chat_session.send_message(user_message)
            cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned_text)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Erro ao chamar ou processar a resposta do Gemini: {e}")
            return None 

    def post(self, request):
        if not gemini_service:
            return Response({"error": "Serviço de IA indisponível."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        all_responses = request.data.get('responses')
        if not all_responses:
            return Response({"error": "Nenhuma resposta fornecida."}, status=status.HTTP_400_BAD_REQUEST)

        selected_dimensions = all_responses.get('dimensoesAvaliar', [])
        if not selected_dimensions:
             return Response({"error": "Nenhuma dimensão para avaliar foi selecionada."}, status=status.HTTP_400_BAD_REQUEST)

        final_diagnosis = {}

        system_prompt_template = """
            Você é um especialista em desenvolvimento organizacional. Sua tarefa é analisar os resultados de uma ÚNICA dimensão de um diagnóstico empresarial.
            Com base nos dados a seguir para a dimensão '{dimension_title}', gere um relatório em formato JSON com "fortes", "fracos" e "recomendacao".

            Para "fortes" e "fracos", não retorne apenas o nome do tópico. Em vez disso, crie uma frase descritiva que explique o significado do resultado.
            Por exemplo, se o tópico 'Comunicação e Alinhamento' tem um resultado 'Otimizado', um bom ponto forte seria: "Comunicação e Alinhamento (Otimizado): A empresa demonstra uma comunicação clara e eficaz, mantendo as equipes bem alinhadas com os objetivos estratégicos."
            
            - Para "fortes", identifique os tópicos com os melhores resultados (estágios 'Estratégico' ou 'Otimizado') e descreva-os como no exemplo.
            - Para "fracos", identifique os tópicos com os piores resultados (estágios 'Inicial' ou 'Reativo') e descreva-os de forma semelhante.
            - Para "recomendacao", forneça 2 a 3 sugestões práticas e acionáveis focadas nos pontos fracos.

            Formate sua resposta EXCLUSIVAMENTE como um objeto JSON com a estrutura:
            {{ "summary": {{ "fortes": [], "fracos": [], "recomendacao": [] }} }}
        """

        for dimension_key in selected_dimensions:
            if dimension_key not in self.DIMENSION_MAPPING:
                continue

            dimension_info = self.DIMENSION_MAPPING[dimension_key]
            dimension_title = dimension_info["title"]
            
            specific_answers = []
            for num, question_title in dimension_info["questions"].items():
                response_key = f"{dimension_key}_{num}"
                answer = all_responses.get(response_key, "N/A")
                specific_answers.append(f"- {question_title}: {answer}")
            
            formatted_responses = "\n".join(specific_answers)
            
            current_system_prompt = system_prompt_template.format(dimension_title=dimension_title)
            user_message = f"Aqui estão os resultados para a dimensão '{dimension_title}':\n{formatted_responses}"
            
            print(f"--- Enviando para IA (Dimensão: {dimension_title}) ---\n{user_message}\n--------------------")

            ai_result = self._call_gemini_api(current_system_prompt, user_message)

            if ai_result and 'summary' in ai_result:
                final_diagnosis[dimension_key] = ai_result['summary']
            else:
                final_diagnosis[dimension_key] = {
                    "fortes": ["Erro ao analisar esta dimensão."],
                    "fracos": ["Não foi possível gerar pontos a melhorar."],
                    "recomendacao": ["Tente novamente mais tarde."]
                }

        print(f"DEBUG: JSON final enviado para o frontend: {final_diagnosis}")
        return Response(final_diagnosis, status=status.HTTP_200_OK)
    
    
class funcionarios(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        empresa = user.empresa

        if not empresa:
             return Response(
                {"error": "Usuário não está vinculado a uma empresa ou plano."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            plano = empresa.plano
            
            if not plano or not plano.limite_usuarios:
                 return Response(
                    {"error": "Plano não encontrado ou limite não configurado."},
                    status=status.HTTP_403_FORBIDDEN
                )

            limite_usuarios = plano.limite_usuarios

            usuarios_atuais = Usuario.objects.filter(empresa=empresa).count()

            if usuarios_atuais >= limite_usuarios:
                return Response(
                    {"error": f"Limite de usuários atingido ({usuarios_atuais}/{limite_usuarios}). Faça um upgrade do plano."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
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
            print(f"Data de Nascimento: {nascimento}")
            print(f"Senha: {senha}")
            print("------------------------------------")

            return Response(
             {"message": "Funcionário cadastrado com sucesso!"},
             status=status.HTTP_201_CREATED
        )

        except Exception as e:
            print(f"Erro ao verificar limite de usuários: {e}")
            return Response(
                {"error": "Erro interno ao verificar limite."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
