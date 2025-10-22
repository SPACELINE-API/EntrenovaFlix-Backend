# accounts/urls.py

from django.urls import path
from .serializers import MyTokenObtainPairSerializer
from .views import RegisterView, MeuViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, PostListCreateView, 
    PostDetailView, ComentarioListCreateView
)

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('login', TokenObtainPairView.as_view(serializer_class=MyTokenObtainPairSerializer), name='token_obtain_pair'),
    path('login/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('meu-endpoint', MeuViewSet.as_view(), name='meu_endpoint'),  

    path('posts', PostListCreateView.as_view(), name='post-list-create'),
    path('posts/<uuid:pk>', PostDetailView.as_view(), name='post-detail'),
    path('posts/<uuid:post_id>/comentarios', ComentarioListCreateView.as_view(), name='comentario-list-create'),
]