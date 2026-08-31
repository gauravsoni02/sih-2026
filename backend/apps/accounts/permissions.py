from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdmin(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_authenticated and request.user.role == 'admin'


class IsLabManager(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_authenticated and request.user.role in ('admin', 'lab_manager')


class IsEngineer(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_authenticated and request.user.role in (
            'admin', 'lab_manager', 'engineer'
        )


class IsViewer(BasePermission):
    """Any authenticated user can view."""
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_authenticated


class CanWrite(BasePermission):
    """Viewers cannot create/update/delete."""
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.role != 'viewer'


class CanApprove(BasePermission):
    """Only admin and lab_manager can approve reports."""
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user.is_authenticated and request.user.role in ('admin', 'lab_manager')
