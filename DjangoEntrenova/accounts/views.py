from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db import IntegrityError, transaction
import re

from .models import Posts, Comentarios, Usuario, Empresa, Plans
from .serializers import PostSerializer, ComentarioSerializer, UserSerializer, MyTokenObtainPairSerializer
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa

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
        try:
            post = Posts.objects.get(id=post_id)
            serializer.save(usuario=self.request.user, post=post)
        except Posts.DoesNotExist:
            pass

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
