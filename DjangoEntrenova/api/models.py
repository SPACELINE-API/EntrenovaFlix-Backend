import uuid
from django.db import models
from django.conf import settings

class categoriaConteudo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nome
    
    class Meta:
        db_table = 'categoria_conteudo'
    
class conteudoTrilha(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    categoria = models.ForeignKey(categoriaConteudo, on_delete=models.SET_NULL, null=True, blank=True, related_name='conteudos')
    
    titulo = models.CharField(max_length=255)
    url_video = models.URLField(max_length=500)
    descricao = models.TextField(help_text="Resumo sobre o que o vídeo ensina.")
    
    tags_problema = models.JSONField(
        default=list, 
        help_text="Lista de 'dores' que este vídeo resolve. Ex: ['conflito', 'procrastinação']"
    )
    dica_rapida = models.TextField(
        blank=True, 
        help_text="1-2 frases acionáveis que a IA pode usar como 'mini-dica'."
    )

    def __str__(self):
        return self.titulo
    
    class Meta:
        db_table = 'conteudo_trilha'

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('Aberto', 'Aberto'),
        ('Fechado', 'Fechado'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assunto = models.CharField(max_length=255)
    
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tickets_criados'
    )
    empresa = models.ForeignKey(
        'accounts.Empresa',
        on_delete=models.SET_NULL,
        null=True,
        related_name='tickets'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Aberto')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Tickets de Suporte RH Admin"
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket {self.id} ({self.assunto})"

    def fechar_ticket(self):
        self.status = 'Fechado'
        self.save()

class TicketMensagem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='mensagens')
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    texto = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Mensagens de Ticket RH Admin"
        ordering = ['created_at']

    def __str__(self):
        return f"Mensagem {self.id} no Ticket {self.ticket_id}"
    

class aprimoramentoPessoal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resultado = models.CharField(max_length=255)
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    empresa = models.ForeignKey(
        'accounts.Empresa',
        on_delete=models.SET_NULL,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Aprimoramento pessoal usuario"
        ordering = ['-created_at']
        db_table = 'aprimoramentoPessoal'

    def __str__(self):
        return f"Aprimoramento {self.id} - {self.autor}"




