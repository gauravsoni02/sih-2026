from django.contrib import admin

from .models import Laboratory


@admin.register(Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'lab_code', 'accreditation_number', 'contact_person')
    search_fields = ('name', 'lab_code', 'accreditation_number')
