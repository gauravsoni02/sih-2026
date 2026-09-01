from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin
from .models import Laboratory, OrgSettings
from .serializers import LaboratorySerializer, OrgSettingsSerializer


class LaboratoryViewSet(viewsets.ModelViewSet):
    queryset = Laboratory.objects.active()
    serializer_class = LaboratorySerializer
    search_fields = ['name', 'lab_code', 'accreditation_number']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdmin()]


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def org_settings_view(request: Request) -> Response:
    settings_obj = OrgSettings.load()

    if request.method == 'GET':
        return Response(OrgSettingsSerializer(settings_obj).data)

    # PUT — admins and lab managers only
    role = getattr(request.user, 'role', '')
    if role not in ('admin', 'lab_manager'):
        return Response(
            {'detail': 'Only admins and lab managers can change settings.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = OrgSettingsSerializer(settings_obj, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
