# accounts/urls.py

from django.urls import path
from .serializers import MyTokenObtainPairSerializer
from .views import RegisterView, MeuViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, PostListCreateView, PostDetailView, ComentarioListCreateView, FuncionariosView, EmpresaRegistrationView, CnpjView, CpfView, PrimeiroLoginView, GerarPDFView, SalvarDiagnosticoView, VerDiagnosticoView, ListarDiagnosticosView, GerarChatPDFView, Dashwidgets, CnpjView, CpfView,
    SalvarDiagnosticoView, ListarDiagnosticosView, VerDiagnosticoView, EmpresaListView, EmpresaDetailView)
from api.views import (
    AdminTicketListView,
    TicketCreateView,
    RHTicketListView,
)

from accounts.views import AdminTicketDetailView

urlpatterns = [
    path('funcionarios', FuncionariosView.as_view(), name='funcionarios'),
    path('register', RegisterView.as_view(), name='register'),
    path('register-empresa', EmpresaRegistrationView.as_view(), name='register_empresa_rh'),
    path('empresas', EmpresaListView.as_view(), name='empresa-list'),
    path('empresas/<str:cnpj>', EmpresaDetailView.as_view(), name='empresa-detail'),
    path('primeiro-login', PrimeiroLoginView.as_view(), name='primeiro-login'),
    path('login', TokenObtainPairView.as_view(serializer_class=MyTokenObtainPairSerializer), name='token_obtain_pair'),
    path('login/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('meu-endpoint', MeuViewSet.as_view(), name='meu_endpoint'),  
    path('check-cnpj', CnpjView.as_view(), name='check-cnpj'),
    path('check-cpf', CpfView.as_view(), name='check-cpf'),
    path('posts', PostListCreateView.as_view(), name='post-list-create'),
    path('posts/<uuid:pk>', PostDetailView.as_view(), name='post-detail'),
    path('posts/<uuid:post_id>/comentarios', ComentarioListCreateView.as_view(), name='comentario-list-create'),
    path('gerar-pdf', GerarPDFView.as_view(), name='gerar_pdf'),
    path('api/diagnosticos/salvar/', SalvarDiagnosticoView.as_view(), name='api_salvar_diagnostico'),
    path('api/diagnosticos/listar/', ListarDiagnosticosView.as_view(), name='api_listar_diagnosticos'),
    path('api/diagnosticos/<uuid:diagnostico_id>/', VerDiagnosticoView.as_view(), name='api_ver_diagnostico'),
    path('api/diagnosticos/<uuid:diagnostico_id>/pdf/', GerarChatPDFView.as_view(), name='api_gerar_chat_pdf'),
    path('dashwidgets', Dashwidgets.as_view(), name='dashwidgets'),
]