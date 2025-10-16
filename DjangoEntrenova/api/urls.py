from django.urls import path
from .views import AprovarPagamentoView

urlpatterns = [
    path('aprovar/<str:cnpj>/', AprovarPagamentoView.as_view(), name='aprovar_pagamento'),
]