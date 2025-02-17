from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import RoomViewSet, FloorTypeViewSet, WallTypeViewSet, CeilingTypeViewSet

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='room')
#router.register(r'floor-types', FloorTypeViewSet, basename='floor-type')
#router.register(r'wall-types', WallTypeViewSet, basename='wall-type')
#router.register(r'ceiling-types', CeilingTypeViewSet, basename='ceiling-type')

urlpatterns = router.urls