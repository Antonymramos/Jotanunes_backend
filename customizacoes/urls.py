from rest_framework.routers import DefaultRouter
from .views import CustomizacaoViewSet, DependenciaViewSet, AlteracaoViewSet, NotificacaoViewSet

router = DefaultRouter()
router.register(r'customizacoes', CustomizacaoViewSet, basename='customizacoes')
router.register(r'dependencias', DependenciaViewSet, basename='dependencias')
router.register(r'alteracoes', AlteracaoViewSet, basename='alteracoes')
router.register(r'notificacoes', NotificacaoViewSet, basename='notificacoes')

urlpatterns = router.urls
