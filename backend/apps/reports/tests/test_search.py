import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.engine.constants import AccuracyClass, ComplianceStatus, SessionStatus, Unit
from apps.instruments.models import Instrument
from apps.laboratory.models import Laboratory
from apps.reports.models import Report
from apps.testing.models import TestSession

User = get_user_model()


class TestReportSearch(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.lab = Laboratory.objects.create(
            name='Central Metrology Lab', address='New Delhi',
            accreditation_number='NABL-S-001', lab_code='CML',
        )
        self.user = User.objects.create_user(
            username='eng_search', password='pass1234',
            role='engineer', laboratory=self.lab,
        )
        self.client.force_authenticate(self.user)

        self.instrument = Instrument.objects.create(
            manufacturer='Mettler Toledo', model_name='ICS465',
            serial_number='SN-SEARCH-001',
            accuracy_class=AccuracyClass.CLASS_III, max_capacity=Decimal('30'),
            min_capacity=Decimal('0.4'), verification_scale_interval_e=Decimal('0.02'),
            actual_scale_interval_d=Decimal('0.02'), num_scale_intervals_n=1500,
            unit=Unit.KG,
        )
        self.session = TestSession.objects.create(
            instrument=self.instrument, laboratory=self.lab, engineer=self.user,
            session_date=datetime.date(2026, 8, 15),
            status=SessionStatus.COMPLETED, overall_verdict=ComplianceStatus.PASS,
        )
        self.report = Report.objects.create(
            report_number='NAWI/CML/2026/0001', session=self.session,
            generated_by=self.user, overall_verdict=ComplianceStatus.PASS,
        )

    def test_search_by_report_number(self) -> None:
        resp = self.client.get('/api/reports/search/', {'q': 'NAWI/CML'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['report_number'], 'NAWI/CML/2026/0001')

    def test_search_by_manufacturer(self) -> None:
        resp = self.client.get('/api/reports/search/', {'q': 'Mettler'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data['count'], 1)

    def test_filter_by_verdict(self) -> None:
        resp = self.client.get('/api/reports/search/', {'verdict': 'pass'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)

        resp = self.client.get('/api/reports/search/', {'verdict': 'fail'})
        self.assertEqual(resp.data['count'], 0)

    def test_filter_by_accuracy_class(self) -> None:
        resp = self.client.get('/api/reports/search/', {'accuracy_class': 'III'})
        self.assertEqual(resp.data['count'], 1)

        resp = self.client.get('/api/reports/search/', {'accuracy_class': 'I'})
        self.assertEqual(resp.data['count'], 0)

    def test_filter_by_date_range(self) -> None:
        resp = self.client.get('/api/reports/search/', {
            'date_from': '2026-08-01', 'date_to': '2026-08-31',
        })
        self.assertEqual(resp.data['count'], 1)

        resp = self.client.get('/api/reports/search/', {
            'date_from': '2026-09-01',
        })
        self.assertEqual(resp.data['count'], 0)

    def test_filter_by_manufacturer(self) -> None:
        resp = self.client.get('/api/reports/search/', {'manufacturer': 'Mettler'})
        self.assertEqual(resp.data['count'], 1)

    def test_empty_search_returns_all(self) -> None:
        resp = self.client.get('/api/reports/search/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)

    def test_search_result_fields(self) -> None:
        resp = self.client.get('/api/reports/search/')
        result = resp.data['results'][0]
        self.assertIn('id', result)
        self.assertIn('report_number', result)
        self.assertIn('overall_verdict', result)
        self.assertIn('instrument_name', result)
        self.assertIn('serial_number', result)
        self.assertIn('accuracy_class', result)
        self.assertIn('laboratory_name', result)
        self.assertIn('session_date', result)

    def test_unauthenticated_returns_401(self) -> None:
        self.client.force_authenticate(None)
        resp = self.client.get('/api/reports/search/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_combined_filters(self) -> None:
        resp = self.client.get('/api/reports/search/', {
            'q': 'Mettler', 'verdict': 'pass', 'accuracy_class': 'III',
        })
        self.assertEqual(resp.data['count'], 1)
