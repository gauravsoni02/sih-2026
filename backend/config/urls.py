from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from apps.engine.config_loader import get_config, get_r76_2_config


def standard_config_view(request):
    return JsonResponse({
        'r76_1': get_config(),
        'r76_2': get_r76_2_config(),
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/instruments/', include('apps.instruments.urls')),
    path('api/laboratories/', include('apps.laboratory.urls')),
    path('api/sessions/', include('apps.testing.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/standard-config/', standard_config_view),
]
