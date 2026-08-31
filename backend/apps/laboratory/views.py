from rest_framework import viewsets

from apps.accounts.permissions import IsAdmin
from .models import Laboratory
from .serializers import LaboratorySerializer


class LaboratoryViewSet(viewsets.ModelViewSet):
    queryset = Laboratory.objects.active()
    serializer_class = LaboratorySerializer
    permission_classes = [IsAdmin]
    search_fields = ['name', 'lab_code', 'accreditation_number']
