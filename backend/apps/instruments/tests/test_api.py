from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.instruments.models import Instrument
from apps.laboratory.models import Laboratory

User = get_user_model()


class TestInstrumentAPI(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.lab = Laboratory.objects.create(
            name='Test Lab', address='Addr', accreditation_number='A1', lab_code='TL',
        )
        self.engineer = User.objects.create_user(
            username='eng', password='pass1234', role='engineer', laboratory=self.lab,
        )
        self.viewer = User.objects.create_user(
            username='viewer', password='pass1234', role='viewer',
        )
        self.instrument_data = {
            'manufacturer': 'Mettler Toledo',
            'model_name': 'XPR205',
            'serial_number': 'MT-001',
            'accuracy_class': 'III',
            'max_capacity': '15000.000000',
            'min_capacity': '100.000000',
            'verification_scale_interval_e': '5.000000',
            'actual_scale_interval_d': '5.000000',
            'num_scale_intervals_n': 3000,
            'unit': 'g',
        }

    def test_create_instrument(self) -> None:
        self.client.force_authenticate(user=self.engineer)
        resp = self.client.post('/api/instruments/', self.instrument_data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['serial_number'], 'MT-001')

    def test_viewer_cannot_create(self) -> None:
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.post('/api/instruments/', self.instrument_data)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_can_read(self) -> None:
        self.client.force_authenticate(user=self.engineer)
        self.client.post('/api/instruments/', self.instrument_data)
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.get('/api/instruments/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unique_serial_per_manufacturer(self) -> None:
        self.client.force_authenticate(user=self.engineer)
        self.client.post('/api/instruments/', self.instrument_data)
        resp = self.client.post('/api/instruments/', self.instrument_data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_accuracy_class(self) -> None:
        self.client.force_authenticate(user=self.engineer)
        self.client.post('/api/instruments/', self.instrument_data)
        resp = self.client.get('/api/instruments/?accuracy_class=III')
        self.assertEqual(resp.data['count'], 1)
        resp = self.client.get('/api/instruments/?accuracy_class=I')
        self.assertEqual(resp.data['count'], 0)

    def test_d_greater_than_e_rejected(self) -> None:
        self.client.force_authenticate(user=self.engineer)
        data = self.instrument_data.copy()
        data['actual_scale_interval_d'] = '10.000000'
        data['verification_scale_interval_e'] = '5.000000'
        resp = self.client.post('/api/instruments/', data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
