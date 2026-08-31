import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.instruments.models import Instrument
from apps.laboratory.models import Laboratory

User = get_user_model()


class TestSessionAPI(TestCase):
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
        self.instrument = Instrument.objects.create(
            manufacturer='Mettler', model_name='XPR', serial_number='S1',
            accuracy_class='III', max_capacity=Decimal('15000'),
            min_capacity=Decimal('100'),
            verification_scale_interval_e=Decimal('5'),
            actual_scale_interval_d=Decimal('5'),
            num_scale_intervals_n=3000, unit='g',
        )

    def test_create_session(self) -> None:
        self.client.force_authenticate(user=self.engineer)
        resp = self.client.post('/api/sessions/', {
            'instrument': self.instrument.pk,
            'laboratory': self.lab.pk,
            'engineer': self.engineer.pk,
            'session_date': '2026-08-31',
            'temperature_start': '22.5',
            'humidity': '45.0',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['status'], 'draft')

    def test_viewer_cannot_create(self) -> None:
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.post('/api/sessions/', {
            'instrument': self.instrument.pk,
            'laboratory': self.lab.pk,
            'engineer': self.viewer.pk,
            'session_date': '2026-08-31',
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_bulk_observations(self) -> None:
        self.client.force_authenticate(user=self.engineer)
        session_resp = self.client.post('/api/sessions/', {
            'instrument': self.instrument.pk,
            'laboratory': self.lab.pk,
            'engineer': self.engineer.pk,
            'session_date': '2026-08-31',
        })
        session_id = session_resp.data['id']

        observations = [
            {
                'test_type': 'weighing_performance',
                'test_point_load': '500.000000',
                'indicated_value': '500.500000',
                'correction': '0.000000',
                'trial_number': 1,
                'direction': 'increasing',
            },
            {
                'test_type': 'weighing_performance',
                'test_point_load': '2500.000000',
                'indicated_value': '2502.000000',
                'correction': '0.000000',
                'trial_number': 1,
                'direction': 'increasing',
            },
        ]
        resp = self.client.post(
            f'/api/sessions/{session_id}/observations/',
            observations, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(resp.data), 2)

    def test_calculate(self) -> None:
        self.client.force_authenticate(user=self.engineer)
        session_resp = self.client.post('/api/sessions/', {
            'instrument': self.instrument.pk,
            'laboratory': self.lab.pk,
            'engineer': self.engineer.pk,
            'session_date': '2026-08-31',
        })
        session_id = session_resp.data['id']

        self.client.post(
            f'/api/sessions/{session_id}/observations/',
            [
                {
                    'test_type': 'weighing_performance',
                    'test_point_load': '500.000000',
                    'indicated_value': '501.000000',
                    'correction': '0.000000',
                    'trial_number': 1,
                },
                {
                    'test_type': 'weighing_performance',
                    'test_point_load': '5000.000000',
                    'indicated_value': '5003.000000',
                    'correction': '0.000000',
                    'trial_number': 1,
                },
            ],
            format='json',
        )

        calc_resp = self.client.post(f'/api/sessions/{session_id}/calculate/')
        self.assertEqual(calc_resp.status_code, status.HTTP_200_OK)
        results = calc_resp.data['results']
        self.assertEqual(len(results), 2)

        # load=500, e=5, m=100 -> MPE=0.5*5=2.5, error=1 -> PASS
        self.assertEqual(results[0]['compliance_status'], 'pass')
        # load=5000, e=5, m=1000 -> MPE=1.0*5=5, error=3 -> PASS
        self.assertEqual(results[1]['compliance_status'], 'pass')

        self.assertIn('r76_2_warnings', calc_resp.data)

        session_resp = self.client.get(f'/api/sessions/{session_id}/')
        self.assertEqual(session_resp.data['overall_verdict'], 'pass')
        self.assertEqual(session_resp.data['status'], 'completed')

    def test_get_results(self) -> None:
        self.client.force_authenticate(user=self.engineer)
        session_resp = self.client.post('/api/sessions/', {
            'instrument': self.instrument.pk,
            'laboratory': self.lab.pk,
            'engineer': self.engineer.pk,
            'session_date': '2026-08-31',
        })
        session_id = session_resp.data['id']
        resp = self.client.get(f'/api/sessions/{session_id}/results/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)


class TestReportPermissions(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.lab = Laboratory.objects.create(
            name='Lab', address='A', accreditation_number='A2', lab_code='L2',
        )
        self.engineer = User.objects.create_user(
            username='eng', password='pass1234', role='engineer', laboratory=self.lab,
        )
        self.manager = User.objects.create_user(
            username='mgr', password='pass1234', role='lab_manager', laboratory=self.lab,
        )
        self.instrument = Instrument.objects.create(
            manufacturer='M', model_name='X', serial_number='S2',
            accuracy_class='III', max_capacity=Decimal('15000'),
            min_capacity=Decimal('100'),
            verification_scale_interval_e=Decimal('5'),
            actual_scale_interval_d=Decimal('5'),
            num_scale_intervals_n=3000, unit='g',
        )

    def test_engineer_cannot_approve(self) -> None:
        from apps.testing.models import TestSession
        from apps.reports.models import Report

        session = TestSession.objects.create(
            instrument=self.instrument, laboratory=self.lab,
            engineer=self.engineer, session_date='2026-08-31',
            status='completed', overall_verdict='pass',
        )
        report = Report.objects.create(
            report_number='NAWI/L2/2026/0001',
            session=session, generated_by=self.engineer,
            overall_verdict='pass',
        )

        self.client.force_authenticate(user=self.engineer)
        resp = self.client.post(f'/api/reports/{report.pk}/approve/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_approve(self) -> None:
        from apps.testing.models import TestSession
        from apps.reports.models import Report

        session = TestSession.objects.create(
            instrument=self.instrument, laboratory=self.lab,
            engineer=self.engineer, session_date='2026-08-31',
            status='completed', overall_verdict='pass',
        )
        report = Report.objects.create(
            report_number='NAWI/L2/2026/0001',
            session=session, generated_by=self.engineer,
            overall_verdict='pass',
        )

        self.client.force_authenticate(user=self.manager)
        resp = self.client.post(f'/api/reports/{report.pk}/approve/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'approved')
