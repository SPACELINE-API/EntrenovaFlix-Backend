from django.contrib import admin
from .models import categoriaConteudo, conteudoTrilha

@admin.register(categoriaConteudo)
class CategoriaConteudoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(conteudoTrilha)
class ConteudoTrilhaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria')
    search_fields = ('titulo', 'descricao')
    list_filter = ('categoria',)
    
    fieldsets = (
        (None, {
            'fields': ('titulo', 'categoria', 'url_video', 'descricao')
        }),
        ('Mapeamento da IA (Essencial)', {
            'fields': ('tags_problema', 'dica_rapida')
        }),
    )
