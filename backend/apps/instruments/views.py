from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.accounts.permissions import CanWrite
from .models import Instrument
from .serializers import InstrumentListSerializer, InstrumentSerializer


class InstrumentViewSet(viewsets.ModelViewSet):
    queryset = Instrument.objects.active()
    permission_classes = [CanWrite]
    filterset_fields = ['accuracy_class', 'manufacturer', 'status', 'unit']
    search_fields = ['serial_number', 'manufacturer', 'model_name']
    ordering_fields = ['created_at', 'manufacturer', 'serial_number', 'accuracy_class']

    def get_serializer_class(self):
        if self.action == 'list':
            return InstrumentListSerializer
        return InstrumentSerializer

    def perform_destroy(self, instance: Instrument) -> None:
        instance.soft_delete()
