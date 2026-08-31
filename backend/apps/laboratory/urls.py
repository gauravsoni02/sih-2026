from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LaboratoryViewSet

router = DefaultRouter()
router.register('', LaboratoryViewSet, basename='laboratory')

urlpatterns = [
    path('', include(router.urls)),
]
