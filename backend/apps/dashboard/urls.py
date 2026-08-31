from django.urls import path

from .views import (
    audit_log,
    clear_demo_samples,
    dashboard_stats,
    error_profile,
    list_demo_samples,
    load_demo_samples,
    monthly_tests,
    pass_fail_summary,
    recent_sessions,
)

urlpatterns = [
    path('stats/', dashboard_stats, name='dashboard-stats'),
    path('monthly-tests/', monthly_tests, name='dashboard-monthly-tests'),
    path('recent-sessions/', recent_sessions, name='dashboard-recent-sessions'),
    path('pass-fail-summary/', pass_fail_summary, name='dashboard-pass-fail-summary'),
    path('error-profile/', error_profile, name='dashboard-error-profile'),
    path('audit-log/', audit_log, name='dashboard-audit-log'),
    path('demo-samples/', list_demo_samples, name='demo-samples-list'),
    path('demo-samples/load/', load_demo_samples, name='demo-samples-load'),
    path('demo-samples/clear/', clear_demo_samples, name='demo-samples-clear'),
]
