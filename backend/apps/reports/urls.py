from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ReportViewSet, generate_report_view, search_reports

router = DefaultRouter()
router.register('', ReportViewSet, basename='report')

urlpatterns = [
    path('generate/<int:session_id>/', generate_report_view, name='report-generate'),
    path('search/', search_reports, name='report-search'),
    path('', include(router.urls)),
]
