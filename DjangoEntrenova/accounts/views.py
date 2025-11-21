from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import NotFound
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, F, Q
import re
from .models import Posts, Comentarios, Usuario, Empresa, Plans, DiagnosticoChat
from .serializers import PostSerializer, ComentarioSerializer, UserSerializer, MyTokenObtainPairSerializer

from .models import Posts, Comentarios, Usuario, Empresa, Plans
from .serializers import PostSerializer, ComentarioSerializer, UserSerializer, EmpresaSerializer, MyTokenObtainPairSerializer
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from api.serializers import TicketMensagemSerializer, TicketSerializer,TicketMensagem, Ticket

class RegisterView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

class PrimeiroLoginView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        user.primeiro_login = False
        user.save(update_fields=['primeiro_login'])
        return Response({"message": "Primeiro login concluído."})

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class MeuViewSet(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"mensagem": f"Olá {request.user.email}"})

class PostListCreateView(generics.ListCreateAPIView):
    queryset = Posts.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class PostDetailView(generics.RetrieveAPIView):
    queryset = Posts.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

class ComentarioListCreateView(generics.ListCreateAPIView):
    serializer_class = ComentarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comentarios.objects.filter(post_id=post_id).order_by('data_criacao')

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id')
        resposta_a_id = self.request.data.get('resposta_a')

        try:
            post = Posts.objects.get(id=post_id)
        except Posts.DoesNotExist:
            raise NotFound("Post não encontrado.")

        resposta_a = None
        if resposta_a_id:
            resposta_a = Comentarios.objects.filter(id=resposta_a_id).first()

        serializer.save(
            usuario=self.request.user,
            post=post,
            resposta_a=resposta_a
        )

class EmpresaRegistrationView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        dados = request.data
        dados_cadastro = dados.get('cadastro', {})
        dados_pagamento = dados.get('pagamento', {})

        if not dados_cadastro:
            return Response({"error": "Objeto 'cadastro' não encontrado no payload."}, status=status.HTTP_400_BAD_REQUEST)
        dados_solicitante = dados_cadastro.get('dadosSolicitante', {})
        dados_empresa = dados_cadastro.get('dadosEmpresa', {})
        dados_senha_obj = dados_cadastro.get('dadosSenha', {})
        senha = dados_senha_obj.get('senha')
        plano_nome = dados_pagamento.get('plano') or dados_solicitante.get('plano')

        if not all([dados_solicitante, dados_empresa, senha, plano_nome]):
            return Response({"error": "Dados de cadastro incompletos."}, status=status.HTTP_400_BAD_REQUEST)

        cnpj = re.sub(r'\D', '', dados_empresa.get("cnpj", ""))
        cpf = re.sub(r'\D', '', dados_solicitante.get("cpf", ""))
        telefone = re.sub(r'\D', '', dados_solicitante.get("telefone", ""))

        if len(cnpj) != 14:
            return Response({"error": "CNPJ inválido."}, status=status.HTTP_400_BAD_REQUEST)
        if len(cpf) != 11:
            return Response({"error": "CPF inválido."}, status=status.HTTP_400_BAD_REQUEST)

        status_pagamento = 'aprovado'

        try:
            plano_obj = Plans.objects.get(nome__iexact=plano_nome)
        except Plans.DoesNotExist:
            return Response({"error": f"Plano '{plano_nome}' não encontrado."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            empresa_obj = Empresa.objects.create(
                cnpj=cnpj,
                nome=dados_empresa.get("razaoSocial"),
                plano=plano_obj,
                status_pagamento=status_pagamento
            )
            usuario_rh = Usuario.objects.create_user(
                email=dados_solicitante.get("emailCorporativo"),
                password=senha,
                nome=dados_solicitante.get("nome"),
                sobrenome=dados_solicitante.get("sobrenome"),
                cpf=cpf,
                telefone=telefone,
                empresa=empresa_obj,
                role=Usuario.ROLE_RH,
                is_active=True
            )

        except IntegrityError as e:
            if 'cnpj' in str(e).lower() or 'empresa' in str(e).lower():
                return Response({"error": "Já existe uma empresa com este CNPJ."}, status=status.HTTP_400_BAD_REQUEST)
            if 'email' in str(e).lower():
                return Response({"error": "Este email já está cadastrado."}, status=status.HTTP_400_BAD_REQUEST)
            if 'cpf' in str(e).lower():
                return Response({"error": "Este CPF já está cadastrado."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Erro de dados duplicados."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Erro inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "message": "Empresa e usuário RH cadastrados com sucesso!",
            "empresa": empresa_obj.nome,
            "usuario_email": usuario_rh.email
        }, status=status.HTTP_201_CREATED)


class CnpjView(APIView):
   permission_classes = [AllowAny]
   def post(self, request):
        cnpj_recebido = request.data.get('cnpj', '')
        cnpj_limpo = re.sub(r'\D', '', cnpj_recebido)
        exists = Empresa.objects.filter(cnpj=cnpj_limpo).exists()
        return Response({"exists": exists}, status=status.HTTP_200_OK)

class CpfView(APIView):
   permission_classes = [AllowAny]
   def post(self, request):
        cpf_recebido = request.data.get('cpf', '')
        cpf_limpo = re.sub(r'\D', '', cpf_recebido)
        exists = Usuario.objects.filter(cpf=cpf_limpo).exists()
        return Response({"exists": exists}, status=status.HTTP_200_OK)
    
   
class EmpresaListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresas = Empresa.objects.select_related('plano').all().order_by('nome')
        serializer = EmpresaSerializer(empresas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class EmpresaDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_obj(self, cnpj: str):
        try:
            return Empresa.objects.get(cnpj=cnpj)
        except Empresa.DoesNotExist:
            return None
    
    def get(self, request, cnpj: str):
        empresa = self.get_obj(cnpj)
        if not empresa:
            return Response({"error": "Empresa não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmpresaSerializer(empresa).data, status=status.HTTP_200_OK)
    
    def patch(self, request, cnpj: str):
        empresa = self.get_obj(cnpj)

        if not empresa:
            return Response({"error": "Empresa não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        
        dados = request.data or {}

        obrigatorios = ['nome', 'area', 'lead']
        for campo in obrigatorios:
            if campo in dados and (dados[campo] is None or str(dados[campo]).strip() == ''):
                return Response({"error": "Dados inválidos", "details": {campo: "Campo obrigatório"}}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = EmpresaSerializer(instance=empresa, data=dados, partial=True)

        if not serializer.is_valid():
            return Response({"error": "Dados inválidos", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Erro interno ao atualizar empresa."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, cnpj: str):
        return self.patch(request, cnpj)
    
    def delete(self, request, cnpj: str):
        empresa = self.get_obj(cnpj)

        if not empresa:
            return Response({"error": "Empresa não encontrada"}, status=status.HTTP_404_NOT_FOUND)

        try:
            empresa.delete()
            return Response({"message": "Empresa excluída com sucesso"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Erro interno ao excluir empresa"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FuncionariosView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        empresa = getattr(request.user, "empresa", None)
        if not empresa:
            return Response({"error": "Usuário não está vinculado a nenhuma empresa."}, status=status.HTTP_403_FORBIDDEN)

        funcionarios = Usuario.objects.filter(empresa=empresa).exclude(id=request.user.id).values(
            "id", "nome", "sobrenome", "email", "cpf", "telefone",
            "is_active", "role"
        ).order_by('nome', 'sobrenome')

        return Response(list(funcionarios), status=status.HTTP_200_OK)

    def post(self, request):
        empresa = getattr(request.user, "empresa", None)
        if not empresa:
            return Response({"error": "Usuário RH não está vinculado a nenhuma empresa."}, status=status.HTTP_403_FORBIDDEN)

        try:
            plano = empresa.plano
            if plano and plano.limite_usuarios and Usuario.objects.filter(empresa=empresa).count() >= plano.limite_usuarios:
                return Response({"error": f"Limite de usuários atingido ({plano.limite_usuarios})."}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response({"error": "Erro ao verificar limite de usuários."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        dados = request.data
        required_fields = ['email', 'nome', 'sobrenome', 'password', 'cpf', 'data_nascimento']
        if not all(dados.get(field) for field in required_fields):
            return Response({"error": "Todos os campos obrigatórios devem ser preenchidos."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cpf_limpo = re.sub(r'\D', '', dados.get("cpf", ""))
            telefone_limpo = re.sub(r'\D', '', dados.get("telefone", ""))

            if len(cpf_limpo) != 11:
                return Response({"error": "CPF inválido. Deve conter 11 dígitos."}, status=status.HTTP_400_BAD_REQUEST)
            if telefone_limpo and not (10 <= len(telefone_limpo) <= 11):
                return Response({"error": "Telefone inválido. Deve conter 10 ou 11 dígitos."}, status=status.HTTP_400_BAD_REQUEST)

            user = Usuario.objects.create_user(
                email=dados.get("email"),
                nome=dados.get("nome"),
                sobrenome=dados.get("sobrenome"),
                password=dados.get("password"),
                cpf=cpf_limpo,
                telefone=telefone_limpo if telefone_limpo else None,
                data_nascimento=dados.get("data_nascimento"),
                empresa=empresa,
                role=dados.get("role", Usuario.ROLE_CLIENTE)
            )
            return Response({"message": "Funcionário criado com sucesso!", "id": user.id}, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            if 'email' in str(e).lower():
                return Response({"error": "Este email já está cadastrado."}, status=status.HTTP_400_BAD_REQUEST)
            if 'cpf' in str(e).lower():
                return Response({"error": "Este CPF já está cadastrado."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Erro de integridade ao cadastrar funcionário."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Erro inesperado ao cadastrar funcionário."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        empresa = getattr(request.user, "empresa", None)
        if not empresa:
            return Response({"error": "Usuário RH não está vinculado a nenhuma empresa."}, status=status.HTTP_403_FORBIDDEN)

        funcionario_id = request.data.get("id")
        ativo = request.data.get("ativo")

        if funcionario_id is None or ativo is None or not isinstance(ativo, bool):
            return Response({"error": "Campos 'id' e 'ativo' obrigatórios e 'ativo' deve ser booleano."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            funcionario = Usuario.objects.get(id=funcionario_id, empresa=empresa)
            funcionario.is_active = ativo
            funcionario.save(update_fields=['is_active'])
            status_txt = "ativado" if ativo else "desativado"
            return Response({"message": f"Funcionário {status_txt} com sucesso."}, status=status.HTTP_200_OK)
        except Usuario.DoesNotExist:
            return Response({"error": "Funcionário não encontrado nesta empresa."}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "Erro interno ao atualizar status do funcionário."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        empresa = getattr(request.user, "empresa", None)
        if not empresa:
            return Response({"error": "Usuário RH não está vinculado a nenhuma empresa."}, status=status.HTTP_403_FORBIDDEN)

        funcionario_id = request.data.get("id")
        if funcionario_id is None:
            return Response({"error": "O campo 'id' do funcionário é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            funcionario = Usuario.objects.get(id=funcionario_id, empresa=empresa)
            funcionario.delete()
            return Response({"message": "Funcionário excluído com sucesso."}, status=status.HTTP_200_OK)
        except Usuario.DoesNotExist:
            return Response({"error": "Funcionário não encontrado nesta empresa."}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "Erro interno ao excluir funcionário."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class AdminRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        dados = request.data
        required_fields = ['email', 'nome', 'sobrenome', 'password', 'cpf', 'data_nascimento', 'empresa_id']
        if not all(dados.get(field) for field in required_fields):
            return Response(
                {"error": "Campos obrigatórios: email, nome, sobrenome, password, cpf, data_nascimento, empresa_id."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            empresa = Empresa.objects.get(id=dados.get("empresa_id"))
        except Empresa.DoesNotExist:
            return Response({"error": "Empresa não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        try:
            plano = empresa.plano
            if plano and plano.limite_usuarios and Usuario.objects.filter(empresa=empresa).count() >= plano.limite_usuarios:
                return Response(
                    {"error": f"Limite de usuários atingido ({plano.limite_usuarios}) para esta empresa."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except Exception:
            return Response({"error": "Erro ao verificar limite de usuários da empresa."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            cpf_limpo = re.sub(r'\D', '', dados.get("cpf", ""))
            telefone_limpo = re.sub(r'\D', '', dados.get("telefone", ""))

            if len(cpf_limpo) != 11:
                return Response({"error": "CPF inválido. Deve conter 11 dígitos."}, status=status.HTTP_400_BAD_REQUEST)
            if telefone_limpo and not (10 <= len(telefone_limpo) <= 11):
                return Response({"error": "Telefone inválido. Deve conter 10 ou 11 dígitos."}, status=status.HTTP_400_BAD_REQUEST)

            user = Usuario.objects.create_user(
                email=dados.get("email"),
                nome=dados.get("nome"),
                sobrenome=dados.get("sobrenome"),
                password=dados.get("password"),
                cpf=cpf_limpo,
                telefone=telefone_limpo if telefone_limpo else None,
                data_nascimento=dados.get("data_nascimento"),
                empresa=empresa, 
                role=Usuario.ROLE_ADMIN, 
                is_staff=True 
            )
            return Response({"message": "Admin da empresa criado com sucesso!", "id": user.id}, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
            if 'email' in str(e).lower():
                return Response({"error": "Este email já está cadastrado."}, status=status.HTTP_400_BAD_REQUEST)
            if 'cpf' in str(e).lower():
                return Response({"error": "Este CPF já está cadastrado."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Erro de integridade ao cadastrar admin."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Erro inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class GerarPDFView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        diagnostic_result = request.data.get('diagnosticResult', {})
        form_data = request.data.get('formData', {})

        TOPICO_TITULOS = {
            "pessoasCultura": "Pessoas & Cultura",
            "estruturaOperacoes": "Estrutura & Operações",
            "mercadoClientes": "Mercado & Clientes",
            "direcaoFuturo": "Direção & Futuro",
        }

        for key, cat in diagnostic_result.items():
            cat["titulo"] = TOPICO_TITULOS.get(key, key)

        context = {
            "diagnosticResult": diagnostic_result,
            "formData": form_data,
        }

        html = render_to_string('diagnostico_template.html', context)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Diagnóstico Aprofundado.pdf"'

        pisa_status = pisa.CreatePDF(html, dest=response)

        if pisa_status.err:
            return HttpResponse("Erro ao gerar o PDF")
        
        return response

class SalvarDiagnosticoView(APIView):
    permission_classes = [IsAuthenticated] 
    def post(self, request):
        try:
            conversa_array = request.data.get('conversa')
            tipo_trilha = request.data.get('tipo_trilha')

            if not conversa_array or not tipo_trilha:
                return Response({'status': 'erro', 'message': 'Dados incompletos.'}, status=status.HTTP_400_BAD_REQUEST)
            DiagnosticoChat.objects.create(
                user=request.user,
                tipo_trilha=tipo_trilha,
                conversa_completa=conversa_array
            )
            return Response({'status': 'sucesso', 'message': 'Diagnóstico salvo!'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'status': 'erro', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ListarDiagnosticosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        diagnosticos = DiagnosticoChat.objects.filter(user=request.user)
        lista_para_frontend = list(diagnosticos.values(
            'id', 
            'created_at', 
            'tipo_trilha'
        ))
        
        return Response({'diagnosticos': lista_para_frontend}, status=status.HTTP_200_OK)

class VerDiagnosticoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, diagnostico_id):
        try:
            diagnostico = DiagnosticoChat.objects.get(id=diagnostico_id, user=request.user)
            return Response({
                'tipo_trilha': diagnostico.tipo_trilha,
                'created_at': diagnostico.created_at,
                'conversa_completa': diagnostico.conversa_completa
            }, status=status.HTTP_200_OK)
            
        except DiagnosticoChat.DoesNotExist:
            return Response({'status': 'erro', 'message': 'Diagnóstico não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'status': 'erro', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GerarChatPDFView(APIView):
    permission_classes = [IsAuthenticated] 

    def get(self, request, diagnostico_id):
        try:
            diagnostico = DiagnosticoChat.objects.get(id=diagnostico_id, user=request.user)     
        except DiagnosticoChat.DoesNotExist:
            return Response({'status': 'erro', 'message': 'Diagnóstico não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        context = {
            'chat': diagnostico
        }
        html = render_to_string('chat_template.html', context)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="diagnostico_{diagnostico_id}.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)

        if pisa_status.err:
            return HttpResponse("Erro ao gerar o PDF")
        
        return response
    
def get_mock_engagement_finance_data():
    return {

        "totalTrilhasCriadas": 85,
        "trilhasMaisAcessadas": [
            {"nome": "Liderança 101", "acessos": 1200},
            {"nome": "Comunicação Efetiva", "acessos": 950},
            {"nome": "Gestão de Tempo", "acessos": 700},
        ],
        "topHobbies": [
            {"nome": "Leitura", "usuarios": 300},
            {"nome": "Esportes", "usuarios": 250},
            {"nome": "Música", "usuarios": 150},
            {"nome": "Gastronomia", "usuarios": 100},
        ],
        "engajamentoVsCrescimento": [
            ["Jan", 60, 100],
            ["Fev", 65, 120],
            ["Mar", 70, 150],
            ["Abr", 75, 200],
        ],

        "topDimensoes": [
            {"nome": "Comunicação", "trabalhadas": 500},
            {"nome": "Autoconhecimento", "trabalhadas": 450},
            {"nome": "Liderança", "trabalhadas": 400},
        ],
        
        "revenueTotal": 120500.75,
        "historicoTransacoes": [
            {"id": "t1", "empresa": "Empresa A", "valor": 500, "data": "2025-11-14", "plano": "Premium", "metodo": "Cartão"},
            {"id": "t2", "empresa": "Empresa B", "valor": 750, "data": "2025-11-13", "plano": "Basic", "metodo": "Boleto"},
            {"id": "t3", "empresa": "Empresa C", "valor": 500, "data": "2025-11-12", "plano": "Standard", "metodo": "Pix"},
        ]
    }
def get_mock_engagement_finance_data():
    return {

        "totalTrilhasCriadas": 85,
        "trilhasMaisAcessadas": [
            {"nome": "Liderança 101", "acessos": 1200},
            {"nome": "Comunicação Efetiva", "acessos": 950},
            {"nome": "Gestão de Tempo", "acessos": 700},
        ],
        "topHobbies": [
            {"nome": "Leitura", "usuarios": 300},
            {"nome": "Esportes", "usuarios": 250},
            {"nome": "Música", "usuarios": 150},
            {"nome": "Gastronomia", "usuarios": 100},
        ],
        "engajamentoVsCrescimento": [
            ["Jan", 60, 100],
            ["Fev", 65, 120],
            ["Mar", 70, 150],
            ["Abr", 75, 200],
        ],

        "topDimensoes": [
            {"nome": "Comunicação", "trabalhadas": 500},
            {"nome": "Autoconhecimento", "trabalhadas": 450},
            {"nome": "Liderança", "trabalhadas": 400},
        ],
        
        "revenueTotal": 12500.,
        "historicoTransacoes": [
            {"id": "t1", "empresa": "Empresa A", "valor": 1390.90, "data": "2025-11-14", "plano": "Diamante", "metodo": "Cartão"},
            {"id": "t2", "empresa": "Empresa B", "valor": 990.90, "data": "2025-11-13", "plano": "Premium", "metodo": "Boleto"},
            {"id": "t3", "empresa": "Empresa C", "valor": 590.90, "data": "2025-11-12", "plano": "Essencial", "metodo": "Pix"},
        ]
    }

    
class Dashwidgets(APIView):


    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
             return Response({"error": "Acesso não autorizado."}, status=status.HTTP_403_FORBIDDEN)
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        one_day_ago = timezone.now() - timedelta(days=1)

        user_metrics = Usuario.objects.aggregate(

            totalUsuarios=Count('id'),
            
            usuariosAtivos=Count('id', filter=Q(last_login__gte=seven_days_ago)),
            
            novosInscritos=Count('id', filter=Q(date_joined__gte=one_day_ago))
        )
        business_metrics = Empresa.objects.filter(status_pagamento='aprovado').aggregate(
            totalEmpresas=Count('id')
        )
        
        planos_mais_assinados = Empresa.objects.filter(status_pagamento='aprovado') \
                                    .values(plano_nome=F('plano__nome')) \
                                    .annotate(assinantes=Count('id')) \
                                    .order_by('-assinantes')
        
        mock_data = get_mock_engagement_finance_data()

        response_data = {
            "totalUsuarios": user_metrics['totalUsuarios'],
            "usuariosAtivos": user_metrics['usuariosAtivos'],
            "novosInscritos": user_metrics['novosInscritos'],
            "totalEmpresas": business_metrics['totalEmpresas'],
            "planosMaisAssinados": list(planos_mais_assinados),
            **mock_data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
class AdminTicketDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated] 

    def get_object(self, request, pk):
        is_admin_role = False
        try:
            if request.user.role == Usuario.ROLE_ADMIN:
                is_admin_role = True
        except AttributeError:
            pass

        if request.user.is_superuser or is_admin_role:
            return get_object_or_404(Ticket, id=pk)
        else:
            return get_object_or_404(Ticket, id=pk, empresa=request.user.empresa)

    def get(self, request, pk):
        ticket = self.get_object(request, pk)
        serializer = TicketSerializer(ticket)
        return Response(serializer.data)

    def post(self, request, pk):
        ticket = self.get_object(request, pk)
        texto_resposta = request.data.get('texto')

        if not texto_resposta:
            return Response({"error": "O texto da resposta é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        if ticket.status == 'Fechado':
            return Response({"error": "Este ticket já está fechado."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                nova_mensagem = TicketMensagem.objects.create(
                    ticket=ticket,
                    autor=request.user, 
                    texto=texto_resposta
                )
                
                ticket.status = 'Fechado'
                ticket.save(update_fields=['status'])
            
            serializer = TicketMensagemSerializer(nova_mensagem)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                "error": "Erro ao salvar a resposta. A operação foi revertida.",
                "detalhe": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, pk):
        ticket = self.get_object(request, pk)
        
        try:
            ticket.delete()
            return Response(
                {"message": "Ticket excluído com sucesso."}, 
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": "Erro ao excluir ticket.", "detalhe": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class colaboradoresView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        ticket = self.get_object(request, pk)
        serializer = TicketSerializer(ticket)
        return Response("Sem implementação de código")
