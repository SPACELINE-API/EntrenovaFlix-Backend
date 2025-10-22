from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny 
from accounts.models import Empresa, Usuario
from .ai_service import gemini_service, gemini_service_flash
import json
import re
from rest_framework.permissions import IsAuthenticated 

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

    def post(self, request):
        if not gemini_service:
            return Response(
                {"error": "O serviço de IA não está disponível."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        user_message = request.data.get('message')
        history = request.data.get('history', [])
        form_data_str = request.data.get('formu', '{}') 

        try:
             form_data = json.loads(form_data_str) if isinstance(form_data_str, str) else form_data_str
        except json.JSONDecodeError:
             form_data = form_data_str

        if not history and form_data and form_data != '{}':
            print("--- DADOS DO FORMULÁRIO RECEBIDOS (INÍCIO DA CONVERSA) ---")
            print(json.dumps(form_data, indent=2, ensure_ascii=False))
            print("-------------------------------------------------------------")

        if not user_message:
            return Response(
                {"error": "O campo 'message' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST
            )

        system_prompt = f"""
            Você é a I.A. da Entrenova, uma consultora de negócios estratégica e proativa.
            Sua missão é diagnosticar e solucionar problemas empresariais de forma empática e prática, guiando o usuário passo a passo.
            O diagnóstico base é o seguinte: {json.dumps(form_data, ensure_ascii=False)}.
            Siga estes 4 passos na conversa:
            PASSO 1: INICIO
            - NÃO cumprimente 
            - Mencione que analisou o formulário (só na primeira vez).
            - Apresente o primeiro ponto fraco identificado e faça uma pergunta aberta sobre ele.("Qual o maior desafio encontrado na sua empresa atualmente?")
            PASSO 2: INVESTIGAÇÃO
            - Após analisar o formulário inicial e identificar quais das quatro dimensões (Pessoas & Cultura, Estrutura & Operações, etc.) necessitam de melhora.
            - Caso o usuário pergunte sobre geração das trilhas, diga "A geração das trilhas será após a investigação sobre sua empresa" e conduza as perguntas da entrevista.
            - Conduza uma entrevista de aprofundamento focada apenas nas dimensões que foram diagnosticadas como pontos a melhorar. 
            - Seja concisa. Não repita saudações ou "analisei o formulário".
              Ex: "Entendo. E essa dificuldade parece estar mais nos canais utilizados ou na clareza das mensagens?"
            - Para cada dimensão problemática identificada, siga o roteiro exato de transição e perguntas principais.
            - Faça uma pergunta de aprofundamento específica e concisa sobre o que o usuário acabou de dizer, para explorar a causa ou um exemplo.
            - Só então, passe para a próxima pergunta principal do roteiro.
            -Roteiro de Investigação (Siga apenas para as dimensões necessárias)
            Dimensão 1: Pessoas & Cultura
                Inicie o primeiro tópico: "Vamos começar falando sobre Pessoas & Cultura."
                Faça a primeira pergunta: "Quando alguém comete um erro, o que costuma acontecer?"
                (Aguarde a resposta)
                Faça uma pergunta para afundar o assunto
                (Aguarde a resposta)
                Faça a segunda pergunta: "E sobre conflitos? Os conflitos dentro da equipe são resolvidos de forma rápida, demorada ou raramente são resolvidos?"
            Dimensão 2: Estrutura & Operações**
                Faça a transição: "Obrigado. Agora, vamos falar um pouco sobre Estrutura & Operações."
                Faça a primeira pergunta: "Como as pessoas sabem o que é prioridade em um projeto?"
                (Aguarde a resposta)
                Faça uma pergunta para afundar o assunto
                (Aguarde a resposta)
                Faça a segunda pergunta: "Quando alguém precisa tomar uma decisão simples, o que costuma fazer?"
            Dimensão 3: Mercado & Clientes**
                Faça a transição: "Entendido. Mudando o foco para a relação com o Mercado & Clientes..."
                Faça a primeira pergunta: "Quando um cliente traz uma demanda inesperada, como a equipe reage?"
                (Aguarde a resposta)
                Faça uma pergunta para afundar o assunto
                (Aguarde a resposta)
                Faça a segunda pergunta: "Qual foi a última vez que a empresa mudou uma rotina por causa de feedback externo?"
            Dimensão 4: Direção & Futuro**
                Faça a transição: "Estamos quase acabando. Por último, vamos falar sobre Direção & Futuro."
                Faça a primeira pergunta: "Se você tivesse que explicar a visão de futuro da empresa em uma frase, qual seria?"
                (Aguarde a resposta)
                Faça uma pergunta para afundar o assunto
                (Aguarde a resposta)
                Faça a segunda pergunta: "Na sua opinião, quem são os futuros líderes que já estão surgindo na empresa?"
            PASSO 3: SOLUÇÃO
            - Ao ter informações suficientes, responda com:
              1. Reconhecimento breve (1 frase).
              2. 2-3 soluções práticas listadas com hífens.
            Ex: "Percebi no diagnóstico que um desafio é a 'Comunicação Interna'.\\nComo isso tem se manifestado recentemente na sua equipe?"
            Ex: "Compreendi a questão dos ruídos. Algumas ações podem ajudar:\\n- Definir um canal oficial para comunicados importantes;\\n- Fazer reuniões curtas de alinhamento no início do dia."
            PASSO 4: TRANSIÇÃO/ENCERRAMENTO
            - Após as soluções, pergunte como o usuário deseja prosseguir:
              1. Aprofundar neste ponto?
              2. Ir para o próximo ponto fraco?
              3. Encerrar por agora?
            - IMPORTANTE: Se o usuário responder indicando que deseja encerrar (ex: "encerrar", "por agora chega", "obrigado, podemos parar", "satisfeito"), sua resposta JSON DEVE ter "isComplete": true e uma mensagem de despedida curta. Caso contrário, "isComplete" deve ser false.
            - Se ele escolher continuar, volte ao PASSO 2 ou inicie um novo ciclo para outro ponto fraco, sem repetir saudações.
            REGRAS GERAIS:
            - Tom profissional, empático e natural.
            - Linguagem simples e direta.
            - Respostas curtas e objetivas.
            - Deve perguntar uma pergunta por vez
            FORMATAÇÃO OBRIGATÓRIA DA RESPOSTA:
            - Sua resposta DEVE SER SEMPRE um objeto JSON válido com as chaves "reply" (string com o texto formatado com \\n) e "isComplete" (booleano).
            - Use "\\n" para quebras de linha. Listas com hífens. Sem negrito ou asteriscos (**).
        """

        try:
            chat_session = gemini_service.start_chat_session(system_prompt, history)
            response = chat_session.send_message(user_message)

            cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()

            try:
                ai_response = json.loads(cleaned_text)
                if 'reply' not in ai_response or 'isComplete' not in ai_response:
                    print(f"Alerta: JSON da IA não contém 'reply'/'isComplete'. Encapsulando. Resposta: '{cleaned_text}'")
                    ai_response = { "reply": cleaned_text, "isComplete": False }
            except (json.JSONDecodeError) as json_error:
                 print(f"Alerta: IA não retornou JSON válido. Erro: {json_error}. Resposta: '{cleaned_text}'")
                 ai_response = { "reply": cleaned_text, "isComplete": False }

            return Response(ai_response, status=status.HTTP_200_OK)

        except Exception as e:
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