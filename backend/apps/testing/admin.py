from django.contrib import admin

from .models import TestObservation, TestResult, TestSession


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'instrument', 'session_date', 'status', 'overall_verdict', 'engineer')
    list_filter = ('status', 'overall_verdict', 'verification_type')


@admin.register(TestObservation)
class TestObservationAdmin(admin.ModelAdmin):
    list_display = ('session', 'test_type', 'test_point_load', 'indicated_value', 'trial_number')
    list_filter = ('test_type',)


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('session', 'test_type', 'test_point_load', 'computed_error', 'mpe_applicable', 'compliance_status')
    list_filter = ('test_type', 'compliance_status')
