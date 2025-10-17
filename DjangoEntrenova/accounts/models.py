# accounts/models.py
from django.db import models
import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O campo de Email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
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
    
    # --- CORREÇÃO APLICADA AQUI ---
    # Informa ao Django que o campo 'empresa' corresponde à coluna 'empresa_id' no banco de dados.
    empresa = models.TextField(blank=True, null=True, db_column='empresa_id')
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_CLIENTE
    )
    
    objects = UsuarioManager()

    USERNAME_FIELD = 'email' 
    REQUIRED_FIELDS = ['nome'] 

    def __str__(self):
        return self.email

    class Meta:
        managed = True
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
    post = models.ForeignKey(Posts, on_delete=models.CASCADE)
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

class PendenteAprovado(models.Model):
    cnpj_empresa = models.CharField(max_length=20, unique=True)
    plano = models.CharField(max_length=50)
    status_pagamento = models.CharField(
        max_length=20,
        choices=[('pendente', 'Pendente'), ('aprovado', 'Aprovado')],
        default='pendente'
    )

    class Meta:
        db_table = 'pendenteAprovado'

    def aprovar_pagamento(self):
        self.status_pagamento = 'aprovado'
        self.save()
