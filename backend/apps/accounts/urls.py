from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import UserViewSet


class AuthRateThrottle(AnonRateThrottle):
    scope = 'auth'


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [AuthRateThrottle]


class ThrottledTokenRefreshView(TokenRefreshView):
    throttle_classes = [AuthRateThrottle]


router = DefaultRouter()
router.register('users', UserViewSet, basename='user')

urlpatterns = [
    path('login/', ThrottledTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', ThrottledTokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
