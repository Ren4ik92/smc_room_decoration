from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Представление для схемы
schema_view = SpectacularAPIView.as_view()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api-auth/', include('rest_framework.urls')),  # Для встроенной аутентификации DRF

    # Эндпоинт для получения схемы в формате JSON или YAML
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema-json'), name='schema-swagger-ui'),

    # Эндпоинт для отображения схемы в формате JSON или YAML (не используйте re_path)
    path('schema/', schema_view, name='schema-json'),  # это будет ваш endpoint для схемы
    path('redoc/', SpectacularRedocView.as_view(url_name='schema-json'), name='schema-redoc'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
