from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_number', 'overall_verdict', 'status', 'version', 'created_at')
    list_filter = ('status', 'overall_verdict')
    search_fields = ('report_number',)
