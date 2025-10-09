# Django/Django/urls.py
from django.contrib import admin
from django.urls import path, include
from api.views import ChatbotView 
from api.views import DiagnosticAIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/chatbot/', ChatbotView.as_view(), name='chatbot'),
    path('api/diagnostico/avaliar', DiagnosticAIView.as_view(), name='avaliar-diagnostico')
]