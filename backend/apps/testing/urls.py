from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TestSessionViewSet

router = DefaultRouter()
router.register('', TestSessionViewSet, basename='session')

urlpatterns = [
    path('', include(router.urls)),
]
