from django.contrib import admin

from .models import Instrument


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = (
        'serial_number', 'manufacturer', 'model_name',
        'accuracy_class', 'max_capacity', 'unit', 'status',
    )
    list_filter = ('accuracy_class', 'status', 'unit')
    search_fields = ('serial_number', 'manufacturer', 'model_name')
