import logging

# Configura um logger simples
logger = logging.getLogger(__name__)

class SimpleLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Loga o método e o path ANTES de processar a requisição
        print(f"[DJANGO_LOG] Método: {request.method}, Path: {request.path}")
        
        response = self.get_response(request)
        
        # Opcional: logar o status da resposta
        # print(f"[DJANGO_LOG] Resposta Status: {response.status_code}")
        
        return response