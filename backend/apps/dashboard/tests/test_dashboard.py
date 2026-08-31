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


class DashboardTestMixin:
    def setUp(self) -> None:
        self.client = APIClient()
        self.lab = Laboratory.objects.create(
            name='Test Lab', address='Addr', accreditation_number='ACC-D-001',
            lab_code='TST',
        )
        self.user = User.objects.create_user(
            username='engineer', password='pass1234',
            role='engineer', laboratory=self.lab,
        )
        self.client.force_authenticate(self.user)
        self.instrument = Instrument.objects.create(
            manufacturer='Acme', model_name='Scale-100', serial_number='SN-D-001',
            accuracy_class=AccuracyClass.CLASS_III, max_capacity=Decimal('30'),
            min_capacity=Decimal('0.4'), verification_scale_interval_e=Decimal('0.02'),
            actual_scale_interval_d=Decimal('0.02'), num_scale_intervals_n=1500,
            unit=Unit.KG,
        )


class TestDashboardStats(DashboardTestMixin, TestCase):
    def test_empty_dashboard(self) -> None:
        resp = self.client.get('/api/dashboard/stats/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['total_instruments'], 1)
        self.assertEqual(resp.data['sessions_this_month'], 0)
        self.assertEqual(resp.data['reports_generated'], 0)
        self.assertEqual(resp.data['pass_rate'], 0)

    def test_stats_with_data(self) -> None:
        today = datetime.date.today()
        s1 = TestSession.objects.create(
            instrument=self.instrument, laboratory=self.lab, engineer=self.user,
            session_date=today, status=SessionStatus.COMPLETED,
            overall_verdict=ComplianceStatus.PASS,
        )
        s2 = TestSession.objects.create(
            instrument=self.instrument, laboratory=self.lab, engineer=self.user,
            session_date=today, status=SessionStatus.COMPLETED,
            overall_verdict=ComplianceStatus.FAIL,
        )
        Report.objects.create(
            report_number='NAWI/TST/2026/0001', session=s1,
            generated_by=self.user, overall_verdict=ComplianceStatus.PASS,
        )

        resp = self.client.get('/api/dashboard/stats/')
        self.assertEqual(resp.data['total_instruments'], 1)
        self.assertEqual(resp.data['sessions_this_month'], 2)
        self.assertEqual(resp.data['reports_generated'], 1)
        self.assertEqual(resp.data['pass_rate'], 50.0)

    def test_unauthenticated_returns_401(self) -> None:
        self.client.force_authenticate(None)
        resp = self.client.get('/api/dashboard/stats/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class TestMonthlyTests(DashboardTestMixin, TestCase):
    def test_returns_months(self) -> None:
        today = datetime.date.today()
        TestSession.objects.create(
            instrument=self.instrument, laboratory=self.lab, engineer=self.user,
            session_date=today,
        )

        resp = self.client.get('/api/dashboard/monthly-tests/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)
        self.assertLessEqual(len(resp.data), 12)
        current_month = today.strftime('%Y-%m')
        month_entry = next((m for m in resp.data if m['month'] == current_month), None)
        self.assertIsNotNone(month_entry)
        self.assertGreaterEqual(month_entry['count'], 1)

    def test_empty_months_show_zero(self) -> None:
        resp = self.client.get('/api/dashboard/monthly-tests/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for entry in resp.data:
            self.assertIn('month', entry)
            self.assertIn('count', entry)


class TestRecentSessions(DashboardTestMixin, TestCase):
    def test_returns_recent(self) -> None:
        today = datetime.date.today()
        TestSession.objects.create(
            instrument=self.instrument, laboratory=self.lab, engineer=self.user,
            session_date=today,
        )

        resp = self.client.get('/api/dashboard/recent-sessions/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['instrument_name'], 'Acme Scale-100')

    def test_max_10_results(self) -> None:
        today = datetime.date.today()
        for i in range(15):
            TestSession.objects.create(
                instrument=self.instrument, laboratory=self.lab, engineer=self.user,
                session_date=today,
            )

        resp = self.client.get('/api/dashboard/recent-sessions/')
        self.assertEqual(len(resp.data), 10)
