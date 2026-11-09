#URLs da API e do Django Admin para login
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('locadora.urls')),
    # Login e logout pela web (Django Auth), com link na API navegável
    path('api-auth/', include('rest_framework.urls')),
]