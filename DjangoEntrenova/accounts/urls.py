# accounts/urls.py

from django.urls import path
from .views import RegisterView, MeuViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, PostListCreateView,
    PostDetailView, ComentarioListCreateView,
    EmpresaListCreateView, EmpresaDetailView,
    PlanListCreateView, PlanDetailView,
    SubscriptionListCreateView, SubscriptionDetailView,
    UsuarioListView, CurrentSubscriptionView
)

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('login', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('meu-endpoint', MeuViewSet.as_view(), name='meu_endpoint'),

    path('posts', PostListCreateView.as_view(), name='post-list-create'),
    path('posts/<uuid:pk>', PostDetailView.as_view(), name='post-detail'),
    path('posts/<uuid:post_id>/comentarios', ComentarioListCreateView.as_view(), name='comentario-list-create'),

    path('empresas', EmpresaListCreateView.as_view(), name='empresa-list-create'),
    path('empresas/<uuid:pk>', EmpresaDetailView.as_view(), name='empresa-detail'),

    path('plans', PlanListCreateView.as_view(), name='plan-list-create'),
    path('plans/<uuid:pk>', PlanDetailView.as_view(), name='plan-detail'),

    path('subscriptions', SubscriptionListCreateView.as_view(), name='subscription-list-create'),
    path('subscriptions/<uuid:pk>', SubscriptionDetailView.as_view(), name='subscription-detail'),

    path('usuarios', UsuarioListView.as_view(), name='usuario-list'),
    path('subscription/current', CurrentSubscriptionView.as_view(), name='current-subscription'),
]
