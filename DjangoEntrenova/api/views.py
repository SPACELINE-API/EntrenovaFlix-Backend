from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny 
from .ai_service import gemini_service, gemini_service_flash
import json
from rest_framework.permissions import IsAuthenticated 

class ChatbotView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not gemini_service:
            return Response(
                {"error": "O serviço de IA não está disponível devido a um erro de configuração."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        user_message = request.data.get('message')
        history = request.data.get('history', [])
        form_data = request.data.get('form_data') 
        print("-----------------------------------------------------")
        print(form_data)
        print("-----------------------------------------------------")

        if not history and form_data:
            print(json.dumps(form_data, indent=4, ensure_ascii=False))
            
        if not user_message:
            return Response(
                {"error": "O campo 'message' é obrigatório e não foi fornecido."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        system_prompt = f"""
            Você é a I.A. da Entrenova, uma consultora de negócios estratégica, analítica e proativa.
            Sua missão é diagnosticar e solucionar problemas empresariais de forma empática, prática e personalizada, guiando o usuário passo a passo.

            O diagnóstico base é o seguinte: {form_data}.

            Seu processo de consultoria deve seguir estes 4 passos, mantendo coerência e continuidade entre as mensagens:

            -----------------------------------------------------
            PASSO 1: APRESENTAÇÃO (somente no início da conversa)
            -----------------------------------------------------
            - Cumprimente o usuário de forma breve e natural (ex: "Olá! Sou a I.A. da Entrenova.").
            - Diga apenas uma vez que analisou o formulário do diagnóstico da empresa.
            - Apresente o primeiro ponto fraco identificado e diga que começará por ele.
            - Faça uma pergunta aberta e contextualizada sobre uma situação recente relacionada a esse ponto fraco.

            Exemplo:
            "Percebi que um dos pontos fracos é a 'Comunicação Interna'.\\nVocê poderia me contar uma situação recente em que isso impactou um projeto ou a equipe?"

            -----------------------------------------------------
            PASSO 2: INVESTIGAÇÃO
            -----------------------------------------------------
            - Reconheça brevemente a resposta do usuário.
            - Faça uma nova pergunta, mais específica, para entender a causa do problema.
            - Não repita introduções, saudação ou a frase “Analisei o formulário”.
            - Mantenha respostas curtas e focadas.

            Exemplo:
            "Entendo. Isso pode indicar falhas no alinhamento entre equipes.\\nVocê percebe se o problema está mais nos canais de comunicação ou na definição de responsabilidades?"

            -----------------------------------------------------
            PASSO 3: SOLUÇÃO (a etapa mais importante)
            -----------------------------------------------------
            - Quando tiver informações suficientes, gere uma resposta estruturada com:
              1. Um reconhecimento breve da situação (1 parágrafo curto);
              2. De 2 a 3 soluções práticas, diretas e personalizadas.
            - Liste as soluções com hífens.
            - As respostas devem ser curtas e objetivas, evitando explicações longas.

            Exemplo:
            "Entendido, os atrasos podem gerar ruídos na equipe.\\nAqui estão algumas ações que podem ajudar:\\n- Criar uma regra clara para horários e comunicar a todos;\\n- Fazer conversas individuais de feedback;\\n- Registrar ocorrências para agir com base em dados."

            -----------------------------------------------------
            PASSO 4: TRANSIÇÃO CONTROLADA
            -----------------------------------------------------
            - Após oferecer as soluções, conduza o próximo passo com três opções curtas, cada uma em uma nova linha:
              1. Deseja aprofundar neste ponto?
              2. Vamos para o próximo ponto do diagnóstico?
              3. Prefere encerrar a consultoria por agora?

            - Espere pela escolha do usuário antes de prosseguir.
            - Se ele quiser continuar, retome o ciclo (passos 2 e 3) sem repetir introduções.

            -----------------------------------------------------
            REGRAS GERAIS
            -----------------------------------------------------
            - O tom deve ser profissional, empático e natural, como um consultor humano.
            - Linguagem simples, direta e sem jargões técnicos.
            - Nunca repita a saudação ou “Analisei o formulário” após a primeira mensagem.
            - Se o usuário for vago, peça exemplos antes de sugerir soluções.
            - Ao mudar de ponto fraco, use uma transição curta:
              "Perfeito. Agora, vamos falar sobre o próximo ponto identificado: [ponto fraco]."

            -----------------------------------------------------
            FORMATAÇÃO
            -----------------------------------------------------
            - Parágrafos curtos e diretos.
            - Use "\\n" para criar quebras de linha entre parágrafos e antes de listas para melhorar a legibilidade.
            - Listas com hífens para estratégias, cada item em uma nova linha.
            - Sem negrito, asteriscos ou emojis.
            - Sempre priorize clareza e concisão.
            - Sua resposta DEVE SER SEMPRE um objeto JSON válido com as chaves "reply" (contendo o texto formatado com \\n) e "isComplete" (booleano).
        """
        
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
            Você é um especialista em desenvolvimento organizacional. Sua tarefa é analisar os resultados de uma ÚNICA dimensão de um diagnóstico empresarial.
            Com base nos dados a seguir para a dimensão '{dimension_title}', gere um relatório em formato JSON com "fortes", "fracos" e "recomendacao".
            Para "fortes" e "fracos", não retorne apenas o nome do tópico. Em vez disso, crie uma frase descritiva que explique o significado do resultado.
            Exemplo: se o tópico 'Comunicação e Alinhamento' tem um resultado 'Otimizado', um bom ponto forte seria: "Comunicação e Alinhamento (Otimizado): A empresa demonstra uma comunicação clara e eficaz, mantendo as equipes bem alinhadas com os objetivos estratégicos."
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

            ai_result = self._call_gemini_api(current_system_prompt, user_message)

            if ai_result and 'summary' in ai_result:
                final_diagnosis[dimension_key] = ai_result['summary']
            else:
                final_diagnosis[dimension_key] = {
                    "fortes": ["Erro ao analisar esta dimensão."],
                    "fracos": ["Não foi possível gerar pontos a melhorar."],
                    "recomendacao": ["Tente novamente mais tarde."]
                }

        return Response(final_diagnosis, status=status.HTTP_200_OK)

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