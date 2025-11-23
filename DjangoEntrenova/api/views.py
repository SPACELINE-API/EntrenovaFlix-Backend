from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from accounts.models import Empresa, Usuario
from .ai_service import gemini_service, gemini_service_flash
import json
import re
from rest_framework.permissions import IsAuthenticated 
from .models import conteudoTrilha, TicketMensagem, Ticket
from .serializers import TicketSerializer
from django.db import transaction
from toon_format import encode, decode, ToonDecodeError, DecodeOptions


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
    permission_classes = [AllowAny]

    def _build_toon_catalog(self) -> str:
        try: 
            conteudos = conteudoTrilha.objects.select_related('categoria').all()
            catalogo_lista = []
            for item in conteudos:
                catalogo_lista.append({
                    "id": str(item.id),
                    "titulo": item.titulo,
                    "tags": "~".join(item.tags_problema), 
                    "dica": item.dica_rapida,
                })
            
            return encode(catalogo_lista)
        except Exception as e:
            print(f"ERRO CRÍTICO: Não foi possível carregar o catálogo de trilhas: {e}")
            return "catalogo[0,]{id,titulo,tags,dica}:"

    def _get_system_prompt(self, form_data_toon: str, catalogo_toon: str) -> str:
        
        exemplo_passo_3 = {
            "reply": "Para prioridades, sugiro 'Definindo Prioridades' (ID: uuid-1). Quer ver outro ponto?",
            "trilhas_recomendadas": [
                {"id": "uuid-1", "titulo": "Definindo Prioridades Claras"}
            ],
            "isComplete": False
        }

        exemplo_passo_4 = {
            "reply": "Combinado. Resumo:\n\n- Título 1: Dica 1\n- Título 2: Dica 2\n\nAté mais!",
            "trilhas_recomendadas": [], 
            "isComplete": True
        }

        return f"""
        Você é a I.A. da Entrenova, uma consultora de negócios estratégica e proativa.
        Sua missão é diagnosticar e solucionar problemas empresariais de forma empática e prática.
        Use textos curtos e objetivos.

        REGRAS DE FORMATO (OBRIGATÓRIO):
        - Sua resposta DEVE ser SEMPRE um ÚNICO objeto TOON válido.
        - É PROIBIDO retornar qualquer texto FORA do objeto TOON.
        - É PROIBIDO retornar listas, tabelas, cabeçalhos ou formatos como CSV (ex: 'id,titulo', 'trilhas_recomendadas[2]       ').
        - É PROIBIDO criar colunas, índices, numerações ou blocos de texto antes ou depois do objeto TOON.
        - Use somente o formato:
            key: value
            - indentação para aninhamento.
        - Use "true" e "false" literais (sem aspas).
        - Use aspas apenas quando necessário.
        - OBRIGATÓRIO: Sempre inclua "reply:" (string) e "isComplete:" (booleano).

        DIAGNÓSTICO BASE (Formato TOON):
        {form_data_toon}

        CATÁLOGO DE CONTEÚDO (Formato Tabular TOON [N,]{{id,titulo,tags,dica}}):
        {catalogo_toon}

        REGRA DE GATILHO DE ENCERRAMENTO (Prioridade Máxima):
        - Se a ÚLTIMA MENSAGEM DO USUÁRIO for um pedido claro para parar ou encerrar
          (ex: "encerrar", "por agora chega", "satisfeito", "pode encerrar"),
          você DEVE ignorar os Passos 1-3.
        - Vá direto ao PASSO 4: ENCERRAMENTO.
        - A resposta DEVE ter "isComplete: true".

        Siga estes 4 passos na conversa (a menos que a REGRA DE GATILHO seja ativada):

        PASSO 1: INICIO
        - NÃO cumprimente.
        - NÃO mencione que analisou o formulário.
        - Apresente o primeiro ponto fraco identificado e faça uma pergunta aberta.
        - Resposta curta.
        - Exemplo TOON:
          reply: "Analisei seu formulário. Qual o maior desafio hoje?"
          isComplete: false

        PASSO 2: INVESTIGAÇÃO
        - Conduza a entrevista com perguntas breves.
        - Pode usar a "dica" de um item do catálogo como mini-dica se a tag corresponder.
        - Sempre formato TOON.
        - Exemplo TOON (Pergunta):
          reply: "Entendo. E sobre o fluxo de tarefas?"
          isComplete: false
        - Exemplo TOON (com mini-dica):
          reply: "Para isso, uma dica é [dica do item]. Faz sentido?"
          isComplete: false

        PASSO 3: SOLUÇÃO (RECOMENDAÇÃO)
        - Quando tiver clareza sobre a dor, PARE de aprofundar.
        - Consulte o CATÁLOGO e selecione trilhas recomendadas.
        - EXPLIQUE cada conteúdo com 1 frase sobre como ele resolve a dor.
        - Retorne no TOON uma LISTA de objetos em "trilhas_recomendadas".
        - SEMPRE no interior do objeto TOON, nunca como tabela externa.
        - Exemplo TOON:
          {encode(exemplo_passo_3)}

        PASSO 4: ENCERRAMENTO
        - Ativado quando o usuário pede para encerrar ou confirma encerramento.
        - Despedida curta + lista de TODOS os conteúdos recomendados.
        - Exemplo TOON:
          {encode(exemplo_passo_4)}

        REGRAS GERAIS:
        - Tom profissional, empático e natural.
        - Respostas curtas e objetivas.
        - A resposta DEVE SEMPRE ser um objeto TOON com:
            "reply": string
            "isComplete": booleano
        - REGRA CRÍTICA:
            - Perguntas/transições → isComplete: false
            - Despedida final → isComplete: true
        """

    def post(self, request):
        if not gemini_service:
            print("ERRO CRÍTICO NA CHATBOTVIEW: O gemini_service não foi inicializado.")
            return Response(
                {"reply": "O serviço de IA não está disponível.", "isComplete": True}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            parsed_request = request.data
            
            user_message = parsed_request.get('message')
            history = parsed_request.get('history', []) 
            form_data = parsed_request.get('formu', {}) 

            if not user_message:
                return Response(
                    {"reply": "O campo 'message' é obrigatório.", "isComplete": True}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            form_data_toon = encode(form_data)
            catalogo_toon = self._build_toon_catalog()
            system_prompt = self._get_system_prompt(form_data_toon, catalogo_toon)

            chat_session = gemini_service.start_chat_session(system_prompt, history)
            response = chat_session.send_message(user_message)
            
            ai_response_toon = response.text.strip()
            ai_response_dict = {}
            
            try:
                ai_response_dict = decode(ai_response_toon, DecodeOptions(strict=False))
            except Exception as e:
                print(f"Alerta: IA não retornou TOON válido ou ocorreu um erro de decodificação. Erro: {e}. Resposta bruta: '{ai_response_toon}'")

            if not isinstance(ai_response_dict, dict) or 'reply' not in ai_response_dict or 'isComplete' not in ai_response_dict:
                
                print(f"DEBUG: Ativando Fallback. TOON inválido recebido: '{ai_response_toon}'.")
                
                clean_reply = ai_response_toon.strip().replace('{', '').replace('}', '').replace(':', '')

                ai_response_dict = {
                    "reply": clean_reply, 
                    "isComplete": False 
                }
            
            return Response(ai_response_dict, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"ERRO CRÍTICO NA CHATBOTVIEW (Geral): {e}")
            return Response(
                {"reply": f"Ocorreu um erro interno no servidor: {e}", "isComplete": True}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
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
            chat_session = gemini_service_flash.start_chat_session(system_prompt)
            response = chat_session.send_message(user_message)
            cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned_text)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Erro ao chamar ou processar a resposta do Gemini Flash: {e}")
            return None 

    def post(self, request):
        if not gemini_service_flash:
            return Response({"error": "Serviço de IA (Flash) indisponível."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        all_responses = request.data.get('responses')
        if not all_responses:
            return Response({"error": "Nenhuma resposta fornecida."}, status=status.HTTP_400_BAD_REQUEST)

        selected_dimensions = all_responses.get('dimensoesAvaliar', [])
        if not selected_dimensions:
            return Response({"error": "Nenhuma dimensão para avaliar foi selecionada."}, status=status.HTTP_400_BAD_REQUEST)

        final_diagnosis = {}
        
        system_prompt_template = """
            Você é um especialista em desenvolvimento organizacional. Sua tarefa é analisar os resultados de uma ÚNICA dimensão de um diagnóstico empresarial: '{dimension_title}'.
            
            Com base nos dados fornecidos, gere um relatório em formato JSON com 6 chaves: "fortes", "fracos", "recomendacao", "score", "soft_skills_sugeridas", e "tags_de_interesse".

            1.  Para "fortes": Identifique os tópicos com os melhores resultados (estágios 'Estratégico' ou 'Otimizado') e crie uma frase descritiva para cada.
                Exemplo: "Comunicação e Alinhamento (Otimizado): A empresa demonstra uma comunicação clara e eficaz."
            2.  Para "fracos": Identifique os tópicos com os piores resultados (estágios 'Inicial' ou 'Reativo') e descreva-os de forma semelhante.
            3.  Para "recomendacao": Forneça 2 a 3 sugestões práticas e acionáveis focadas nos pontos fracos. Esta é a recomendação principal para esta dimensão.
            4.  Para "score": Gere um número inteiro de 0 a 100 que represente a maturidade desta dimensão. (100 = Otimizado, 0 = Reativo).
            5.  Para "soft_skills_sugeridas": Com base nos pontos fracos, sugira de 3 a 5 soft skills que deveriam ser desenvolvidas. (Ex: "Comunicação Clara", "Gestão de Tempo").
            6.  Para "tags_de_interesse": Com base no contexto geral da dimensão, sugira 3 a 4 tags de interesse ou conceitos relacionados. (Ex: "Cultura de Feedback", "Metodologias Ágeis", "OKRs").

            Formate sua resposta EXCLUSIVAMENTE como um objeto JSON com a estrutura:
            {{ "summary": {{ 
                "fortes": [], 
                "fracos": [], 
                "recomendacao": [], 
                "score": <numero_de_0_a_100>,
                "soft_skills_sugeridas": [],
                "tags_de_interesse": []
            }} }}
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

            ai_result = self._call_gemini_api(current_system_prompt, user_message)

            if ai_result and 'summary' in ai_result:
                final_diagnosis[dimension_key] = ai_result['summary']
            else:
                final_diagnosis[dimension_key] = {
                    "fortes": ["Erro ao analisar esta dimensão."],
                    "fracos": ["Não foi possível gerar pontos a melhorar."],
                    "recomendacao": ["Tente novamente mais tarde."],
                    "score": 0,
                    "soft_skills_sugeridas": ["N/A"],
                    "tags_de_interesse": ["N/A"]
                }

        return Response(final_diagnosis, status=status.HTTP_200_OK)

class ProximosPassosView(APIView):
    permission_classes = [AllowAny]

    def _call_gemini_api(self, system_prompt, user_message):
        try:
            chat_session = gemini_service_flash.start_chat_session(system_prompt)
            response = chat_session.send_message(user_message)
            
            match = re.search(r'\{[\s\S]*\}', response.text)
            
            if not match:
                print("Erro: Nenhum JSON encontrado na resposta da IA. Resposta bruta:")
                print(response.text)
                return None

            cleaned_text = match.group(0)
            return json.loads(cleaned_text)
        
        except json.JSONDecodeError:
            return None
        except Exception as e:
            print(f"Erro inesperado ao chamar a IA: {e}")
            return None

    def post(self, request):
        if not gemini_service_flash:
            return Response(
                {"error": "O serviço de IA não está disponível"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        pontos_a_melhorar = request.data.get('pontos_a_melhorar')
        if not pontos_a_melhorar or not isinstance(pontos_a_melhorar, list) or len(pontos_a_melhorar) == 0:
            return Response(
                {"error": "Nenhum 'pontos_a_melhorar' foi fornecido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        system_prompt_template = """Você é um especialista em desenvolvimento organizacional.
        Analise a lista de pontos fracos, identifique os 3 mais críticos e crie um **plano de ação único e agregado** para resolvê-los.
        O plano deve ser dividido em horizontes de tempo:
        - curto_prazo (1-2 semanas)
        - medio_prazo (2-4 semanas)
        - longo_prazo (+6 semanas)

        Para cada horizonte, defina um "foco" (a área principal de melhoria) e uma lista de "acoes".
        Retorne **apenas JSON válido**, sem markdown ou explicações adicionais.

        Exemplo de formato de resposta esperado:
        {
        "curto_prazo": {"foco": "Liderança e Engajamento", "acoes": ["Ação 1", "Ação 2", "Ação 3"]},
        "medio_prazo": {"foco": "Estrutura & Processos", "acoes": ["Ação 1", "Ação 2", "Ação 3"]},
        "longo_prazo": {"foco": "Transformação Estratégica", "acoes": ["Ação 1", "Ação 2", "Ação 3"]}
        }
        """
        
        formatted_pontos = "\n".join(f"- {p}" for p in pontos_a_melhorar)
        user_message = f"Analise a seguinte lista de pontos a melhorar e crie o plano de ação agregado focado nos 3 mais críticos:\n\n{formatted_pontos}"
        ai_result_json = self._call_gemini_api(system_prompt_template, user_message)
        expected_keys = ["curto_prazo", "medio_prazo", "longo_prazo"]
        if ai_result_json and isinstance(ai_result_json, dict) and all(k in ai_result_json for k in expected_keys):
            return Response(ai_result_json, status=status.HTTP_200_OK)
        
        fallback = {
            "curto_prazo": {"foco": "", "acoes": []},
            "medio_ prazo": {"foco": "", "acoes": []},
            "longo_prazo": {"foco": "", "acoes": []},
        }
        return Response(fallback, status=status.HTTP_200_OK)
        
def _get_media_importancia_points(media):
    if media <= 2: return 0
    if media == 3: return 1
    if media == 4: return 2
    if media == 5: return 3
    return 0

class LeadScoreView(APIView):
    """
    Calcula o Lead Score com base nas respostas do formulário inicial (Etapa 1 e 2).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        if not data:
            return Response({"error": "Nenhum dado fornecido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            profile = {
                "colaboradores": data.get("numeroColaboradores"),
                "porte": data.get("porteEmpresa"),
                "investimento": data.get("faixaInvestimento"),
                "decisor": data.get("decisorContratacao"),
                "aberturaInovacao": data.get("aberturaInovacao"),
                "projetosAnteriores": data.get("implementouProjetosInovadores"),
                "urgencia": data.get("tempoInicio"),
            }
            media_importancia = (
                float(data.get("importanciaDesenvolvimento", '0') or '0') +
                float(data.get("importanciaSoftSkills", '0') or '0') +
                float(data.get("importanciaCultura", '0') or '0') +
                float(data.get("importanciaImpacto", '0') or '0')
            ) / 4

            points = {
                "colaboradores": {"ate10": 1, "11a30": 2, "30a100": 3, "acima100": 4, "acima500": 5},
                "porte": {"Startup": 2, "PME": 3, "Grande Empresa": 5},
                "investimento": {"ate10k": 1, "10ka50k": 3, "acima50k": 5},
                "decisor": {"CEO/Diretor": 3, "RH/T&D": 2, "Marketing": 1, "Outro": 0},
                "aberturaInovacao": {"1": 0, "2": 0, "3": 1, "4": 2, "5": 3},
                "projetosAnteriores": {"Sim": 2, "Nao": 0},
                "urgencia": {"Imediatamente": 3, "ate3meses": 2, "6mesesoumais": 1}
            }

            total_score = 0
            total_score += points["colaboradores"].get(profile["colaboradores"], 0)
            total_score += points["porte"].get(profile["porte"], 0)
            total_score += points["investimento"].get(profile["investimento"], 0)
            total_score += points["decisor"].get(profile["decisor"], 0)
            total_score += points["aberturaInovacao"].get(profile["aberturaInovacao"], 0)
            total_score += _get_media_importancia_points(media_importancia)
            total_score += points["projetosAnteriores"].get(profile["projetosAnteriores"], 0)
            total_score += points["urgencia"].get(profile["urgencia"], 0)

            if total_score >= 19:
                classification, className = "Quente", "quente"
            elif total_score >= 11:
                classification, className = "Morno", "morno"
            else:
                classification, className = "Frio", "frio"
                
            return Response({
                "score": total_score,
                "classification": classification,
                "className": className
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Erro ao calcular lead score: {e}")
            return Response({"error": "Erro ao processar dados do lead."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TicketCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        autor = request.user
        assunto = request.data.get("assunto")
        texto = request.data.get("texto")

        if not assunto or not texto:
            return Response(
                {"error": "Assunto e texto são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket = Ticket.objects.create(
            assunto=assunto,
            autor=autor,
            empresa=autor.empresa,
            status="Aberto"
        )

        TicketMensagem.objects.create(
            ticket=ticket,
            autor=autor,
            texto=texto
        )

        return Response(
            TicketSerializer(ticket).data, 
            status=status.HTTP_201_CREATED
        )



class AdminTicketListView(APIView):
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        if request.user.role == "admin":
            tickets = Ticket.objects.all().order_by('-created_at')
        else:
            tickets = Ticket.objects.filter(empresa=request.user.empresa).order_by('-created_at')
        serializer = TicketSerializer(tickets, many=True)

        return Response(serializer.data)
    
    
class RHTicketListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "rh":
            return Response({"error": "Acesso negado."}, status=403)
        
        tickets = Ticket.objects.filter(
            empresa=request.user.empresa
        ).order_by('-created_at')

        return Response(TicketSerializer(tickets, many=True).data)
