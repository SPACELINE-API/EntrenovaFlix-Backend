from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Posts, Comentarios, Usuario
from .serializers import PostSerializer, ComentarioSerializer, UserSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa


class RegisterView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

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
        # Ele pega o usuário da requisição (que foi autenticado pelo token JWT)
        # e o passa para o serializer antes de salvar.
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
        post = Posts.objects.get(id=post_id)
        serializer.save(usuario=self.request.user, post=post)

class GerarPDFView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        diagnostic_result = request.data.get('diagnosticResult', {})
        form_data = request.data.get('formData', {})

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