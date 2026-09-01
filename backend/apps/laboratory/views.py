from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsAdmin
from .models import Laboratory
from .serializers import LaboratorySerializer


class LaboratoryViewSet(viewsets.ModelViewSet):
    queryset = Laboratory.objects.active()
    serializer_class = LaboratorySerializer
    search_fields = ['name', 'lab_code', 'accreditation_number']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdmin()]
