# accounts/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import Usuario, Posts, Comentarios, Empresa
from rest_framework.validators import UniqueValidator
from rest_framework.generics import ListCreateAPIView
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated

class UsuarioSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nome', 'email']

class ComentarioSerializer(serializers.ModelSerializer):
    usuario = UsuarioSimplesSerializer(read_only=True)

    class Meta:
        model = Comentarios
        fields = ['id', 'conteudo', 'data_criacao', 'usuario', 'post', 'resposta_a']
        read_only_fields = ['usuario', 'post', 'data_criacao']

    def create(self, validated_data):
        validated_data['data_criacao'] = timezone.now()
        return super().create(validated_data)
    
    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id')
        try:
            post = Posts.objects.get(id=post_id)
        except Posts.DoesNotExist:
            raise NotFound("Post não encontrado.")
    
        serializer.save(usuario=self.request.user, post=post)

class PostSerializer(serializers.ModelSerializer):
    usuario = UsuarioSimplesSerializer(read_only=True)
    class Meta:
        model = Posts
        fields = ['id', 'pergunta', 'descricao', 'created_at', 'usuario']

class PostListCreateView(ListCreateAPIView):
    queryset = Posts.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]  

    def perform_create(self, serializer):
        print("Usuário logado:", self.request.user)
        serializer.save(usuario=self.request.user)

class UserSerializer(serializers.ModelSerializer):
    cpf = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=Usuario.objects.all())]
    )

    empresa = serializers.CharField(source='empresa.nome', required=False, allow_blank=True)
    
    class Meta:
        model = Usuario
        fields = ('id', 'email', 'password', 'nome', 'sobrenome', 'cpf', 'telefone', 'data_nascimento', 'empresa', 'role')
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'required': False}, 
        }
        read_only_fields = ['id']



    def create(self, validated_data):

        empresa_data = validated_data.pop('empresa', None)
        empresa_obj = None

        if empresa_data and empresa_data.get('nome'):
            empresa_nome = empresa_data.get('nome')
            empresa_obj, created = Empresa.objects.get_or_create(nome=empresa_nome)
        user = Usuario.objects.create_user(
            email=validated_data['email'],
            nome=validated_data['nome'],
            sobrenome=validated_data['sobrenome'],
            password=validated_data['password'],
            cpf=validated_data['cpf'],
            telefone=validated_data.get('telefone'), 
            data_nascimento=validated_data.get('data_nascimento'),
            empresa=empresa_obj,
            role=validated_data.get('role', Usuario.ROLE_CLIENTE)
        )
        return user

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['nome'] = user.nome
        token['email'] = user.email
        token['sobrenome'] = user.sobrenome
        token['role'] = user.role
        token['primeiro_login'] = user.primeiro_login

        return token
    
    def validate(self, attrs):
        # Pega a resposta padrão (que contém 'access' e 'refresh')
        data = super().validate(attrs)

        # Adiciona seus campos customizados à resposta JSON principal
        # 'self.user' é o usuário que está sendo autenticado
        data['role'] = self.user.role
        data['primeiro_login'] = self.user.primeiro_login # <-- ADICIONADO
        data['email'] = self.user.email
        data['nome'] = self.user.nome
        
        return data