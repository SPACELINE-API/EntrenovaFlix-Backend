# accounts/models.py
from django.db import models
import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
# A importação de 'User' foi removida daqui


class Empresa(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    class Meta:
        db_table = 'empresas'


class Plan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=100, unique=True)
    limite_usuarios = models.PositiveIntegerField(default=10)  # Limite padrão
    preco = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} (limite: {self.limite_usuarios})"

    class Meta:
        db_table = 'plans'


class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    ativo = models.BooleanField(default=True)
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_fim = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.empresa.nome} - {self.plan.nome}"

    def usuarios_ativos(self):
        return self.empresa.usuarios.filter(is_active=True).count()

    def pode_adicionar_usuario(self):
        return self.usuarios_ativos() < self.plan.limite_usuarios

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'subscriptions'

class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O campo de Email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)

        # Verificar limite antes de salvar
        if user.empresa:
            try:
                subscription = Subscription.objects.get(empresa=user.empresa, ativo=True)
                usuarios_ativos = subscription.usuarios_ativos()
                if usuarios_ativos + 1 > subscription.plan.limite_usuarios:
                    raise ValueError(f"Limite de usuários atingido para o plano {subscription.plan.nome}. Máximo: {subscription.plan.limite_usuarios} usuários.")
            except Subscription.DoesNotExist:
                pass

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    ROLE_ADMIN = 'admin'
    ROLE_RH = 'rh'
    ROLE_CLIENTE = 'user'
    
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_RH, 'Rh'),
        (ROLE_CLIENTE, 'User'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    password = models.CharField(max_length=128, db_column='senha')
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    email = models.EmailField(unique=True) 
    nome = models.TextField()
    
    cpf = models.CharField(unique=True, max_length=14, null=True, blank=True)
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios'  # Boa prática adicionar related_name
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_CLIENTE
    )

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    def save(self, *args, **kwargs):
        # 1. A validação só roda na criação de um novo usuário (quando ele ainda não tem PK)
        if self.pk is None and self.empresa:
            try:
                subscription = Subscription.objects.get(empresa=self.empresa, ativo=True)
                plan = subscription.plan

                # 2. Verifica se o plano realmente tem um limite
                if plan.limite_usuarios > 0:
                    # Usamos 'self.empresa.usuarios' graças ao related_name
                    usuarios_ativos = self.empresa.usuarios.filter(is_active=True).count()

                    # 3. Se o número de usuários ativos já atingiu o limite, levanta o erro
                    if usuarios_ativos >= plan.limite_usuarios:
                        raise ValueError(
                            f"Limite de {plan.limite_usuarios} usuários atingido para o plano '{plan.nome}'."
                        )

            # 4. Trata o caso de uma empresa sem assinatura ativa (importante!)
            except Subscription.DoesNotExist:
                raise ValueError(f"Não é possível criar usuário. A empresa '{self.empresa.nome}' não possui uma assinatura ativa.")

        # 5. Chama o método save() original para salvar o usuário no banco
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    class Meta:
        managed = True  # Esta linha é opcional, pois True é o padrão
        db_table = 'usuarios'


class Posts(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='usuario_id', blank=True, null=True)
    pergunta = models.TextField(blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'posts'


class Comentarios(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Posts, on_delete=models.CASCADE)  # aqui é o problema
    conteudo = models.TextField()
    data_criacao = models.DateTimeField(blank=True, null=True)
    resposta_a = models.ForeignKey('self', on_delete=models.CASCADE, db_column='resposta_a', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'comentarios'


class Respostas(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, blank=True, null=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, db_column='usuario_id', blank=True, null=True)
    
    conteudo = models.TextField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'respostas'


class Estatisticas(models.Model):
    id = models.BigAutoField(primary_key=True)
    dias_ativos = models.SmallIntegerField(db_column='dias ativos')
    tempo_gasto = models.SmallIntegerField(db_column='tempo gasto', blank=True, null=True)
    comentarios_publicados = models.SmallIntegerField(blank=True, null=True)
    comentarios_respondidos = models.SmallIntegerField(blank=True, null=True)
    interacoes_no_forum = models.SmallIntegerField(blank=True, null=True)
    acessos_semanais = models.SmallIntegerField(blank=True, null=True)
    
    class Meta:
        db_table = 'estatisticas'

class Formulario1(models.Model):
    id_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resposta_ia = models.CharField(max_length=100)
    ticket = models.TextField()
    data = models.DateTimeField(blank=True, null=True)
    chamada = models.TextField()
    telefone = models.TextField()
    regiao = models.TextField(db_column='regio', blank=True, null=True)
    
    class Meta:
        db_table = 'formulario1'