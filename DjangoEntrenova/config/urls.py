# Django/Django/urls.py

from django.contrib import admin
from django.urls import path, include
from django.urls import path


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/pagamento/',include('api.urls')),
]