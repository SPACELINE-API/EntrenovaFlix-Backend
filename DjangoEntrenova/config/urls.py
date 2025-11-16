# Django/Django/urls.py
from django.contrib import admin
from django.urls import path, include
from django.urls import path
from api.views import (ChatbotView, 
                       LeadScoreView, 
                       DiagnosticAIView,
                       TicketCreateView,
                       AdminTicketDetailView,
                       AdminTicketListView,
                       RHTicketListView
                       )
from accounts.views import AdminRegistrationView
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
    path('api/lead-score/', LeadScoreView.as_view(), name='lead_score'),
    path('api/proximos-passos/', ProximosPassosView.as_view(), name='proximos_passos'),
    path('api/accounts/tickets/rh/create/', TicketCreateView.as_view(), name='ticket-rh-create'),
    path('api/accounts/tickets/admin/list/', AdminTicketListView.as_view(), name='ticket-admin-list'),
    path('api/accounts/tickets/rh/list/', RHTicketListView.as_view(), name='ticket-rh-list'),
    path('api/createAdmin', AdminRegistrationView.as_view(), name="criarAdmin"),
]