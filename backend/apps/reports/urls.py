from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ReportViewSet, generate_report_view, search_reports, verify_report

router = DefaultRouter()
router.register('', ReportViewSet, basename='report')

urlpatterns = [
    path('generate/<int:session_id>/', generate_report_view, name='report-generate'),
    path('search/', search_reports, name='report-search'),
    path('verify/<str:code>/', verify_report, name='report-verify'),
    path('', include(router.urls)),
]
