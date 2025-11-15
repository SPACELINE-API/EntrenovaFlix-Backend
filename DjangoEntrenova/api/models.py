import uuid
from django.db import models

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
