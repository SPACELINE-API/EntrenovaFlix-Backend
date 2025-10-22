# Django/Django/urls.py
from django.contrib import admin
from django.urls import path, include
from django.urls import path
from api.views import ChatbotView, funcionarios
from api.views import DiagnosticAIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from api.views import ProximosPassosView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/accounts/', include('accounts.urls')),
    path('api/pagamento/',include('api.urls')),
    path('api/chatbot/', ChatbotView.as_view(), name='chatbot'),
    path('api/diagnostico/avaliar', DiagnosticAIView.as_view(), name='avaliar-diagnostico'),
    path('api/proximos-passos/', ProximosPassosView.as_view(), name='proximos_passos'),
    path('api/accounts/funcionario', funcionarios.as_view(), name='funcionarios')
]