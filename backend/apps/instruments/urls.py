from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InstrumentViewSet

router = DefaultRouter()
router.register('', InstrumentViewSet, basename='instrument')

urlpatterns = [
    path('', include(router.urls)),
]
