# URLs de API da locadora de carros (quando está implementada e autenticada).

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework import permissions
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import APIRootView, DefaultRouter

from . import views


class RaizPublicaView(APIRootView):
    """Ponto de entrada da API (/api/), com os links dos recursos. Aberto a todos."""

    permission_classes = [permissions.AllowAny]


router = DefaultRouter()
router.APIRootView = RaizPublicaView
router.register('users', views.UserViewSet, basename='user')
router.register('perfis-clientes', views.PerfilClienteViewSet, basename='perfil-cliente')
router.register('carros', views.CarroViewSet, basename='carro')
router.register('alugueis', views.AluguelViewSet, basename='aluguel')
router.register('funcionarios', views.FuncionarioViewSet, basename='funcionario')
router.register('multas', views.MultaViewSet, basename='multa')

urlpatterns = [
    path('', include(router.urls)),
    path('me/', views.MeuPerfilView.as_view(), name='me'),
    path('me/alugueis/', views.MeusAlugueisView.as_view(), name='me-alugueis'),
    path('me/carros/', views.MeusCarrosView.as_view(), name='me-carros'),
    path('me/multas/', views.MinhasMultasView.as_view(), name='me-multas'),
    path('auth/token/', obtain_auth_token, name='token'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    path('docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]