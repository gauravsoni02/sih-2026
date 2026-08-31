from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.laboratory.models import Laboratory

User = get_user_model()


class TestAuthAPI(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.lab = Laboratory.objects.create(
            name='Test Lab', address='123 Test St',
            accreditation_number='ACC-001', lab_code='TL01',
        )
        self.user = User.objects.create_user(
            username='engineer1', password='testpass123',
            email='eng@test.com', role='engineer', laboratory=self.lab,
        )

    def test_login(self) -> None:
        resp = self.client.post('/api/auth/login/', {
            'username': 'engineer1', 'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_login_invalid(self) -> None:
        resp = self.client.post('/api/auth/login/', {
            'username': 'engineer1', 'password': 'wrong',
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint(self) -> None:
        self.client.force_authenticate(user=self.user)
        resp = self.client.get('/api/auth/users/me/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['username'], 'engineer1')
        self.assertEqual(resp.data['role'], 'engineer')
        self.assertEqual(resp.data['laboratory_name'], 'Test Lab')

    def test_me_unauthenticated(self) -> None:
        resp = self.client.get('/api/auth/users/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self) -> None:
        login_resp = self.client.post('/api/auth/login/', {
            'username': 'engineer1', 'password': 'testpass123',
        })
        refresh_token = login_resp.data['refresh']
        resp = self.client.post('/api/auth/refresh/', {'refresh': refresh_token})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)


class TestPermissions(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.lab = Laboratory.objects.create(
            name='Test Lab', address='123 Test St',
            accreditation_number='ACC-001', lab_code='TL01',
        )
        self.admin = User.objects.create_user(
            username='admin1', password='testpass123', role='admin',
        )
        self.viewer = User.objects.create_user(
            username='viewer1', password='testpass123', role='viewer',
        )
        self.engineer = User.objects.create_user(
            username='engineer1', password='testpass123', role='engineer',
        )

    def test_viewer_cannot_create_user(self) -> None:
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.post('/api/auth/users/', {
            'username': 'new', 'password': 'testpass123', 'role': 'viewer',
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_user(self) -> None:
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post('/api/auth/users/', {
            'username': 'new', 'password': 'testpass123',
            'email': 'new@test.com', 'role': 'viewer',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_engineer_cannot_create_user(self) -> None:
        self.client.force_authenticate(user=self.engineer)
        resp = self.client.post('/api/auth/users/', {
            'username': 'new', 'password': 'testpass123', 'role': 'viewer',
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
