from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Posts, Comentarios, Usuario, Empresa, Plan, Subscription
from .serializers import PostSerializer, ComentarioSerializer, UserSerializer, EmpresaSerializer, PlanSerializer, SubscriptionSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication

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

class EmpresaListCreateView(generics.ListCreateAPIView):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [IsAuthenticated]

class EmpresaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [IsAuthenticated]

class PlanListCreateView(generics.ListCreateAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]

class PlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]

class SubscriptionListCreateView(generics.ListCreateAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

class SubscriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

class UsuarioListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filtrar usuários pela empresa do usuário logado
        if self.request.user.empresa:
            return Usuario.objects.filter(empresa=self.request.user.empresa)
        return Usuario.objects.none()

class CurrentSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.empresa:
            return Response({"error": "Usuário não pertence a nenhuma empresa"}, status=400)

        try:
            subscription = Subscription.objects.get(empresa=request.user.empresa, ativo=True)
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            return Response({"error": "Nenhuma assinatura ativa encontrada"}, status=404)
