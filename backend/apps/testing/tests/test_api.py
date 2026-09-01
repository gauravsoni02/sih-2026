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


class TestDomainCalculations(TestCase):
    """API-level tests for the R 76 evaluation logic in _calculate_test_type."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.lab = Laboratory.objects.create(
            name='Calc Lab', address='Addr', accreditation_number='A3', lab_code='CL',
        )
        self.engineer = User.objects.create_user(
            username='calc_eng', password='pass1234', role='engineer',
            laboratory=self.lab,
        )
        # Class III, Max 15000 g, e = d = 5 g, n = 3000
        # MPE at 5000 g (m=1000): 1.0e = 5 g; at 500 g (m=100): 0.5e = 2.5 g
        self.instrument = Instrument.objects.create(
            manufacturer='Mettler', model_name='XPR', serial_number='CALC-1',
            accuracy_class='III', max_capacity=Decimal('15000'),
            min_capacity=Decimal('100'),
            verification_scale_interval_e=Decimal('5'),
            actual_scale_interval_d=Decimal('5'),
            num_scale_intervals_n=3000, unit='g',
        )
        self.client.force_authenticate(user=self.engineer)
        resp = self.client.post('/api/sessions/', {
            'instrument': self.instrument.pk,
            'laboratory': self.lab.pk,
            'engineer': self.engineer.pk,
            'session_date': '2026-08-31',
        })
        self.session_id = resp.data['id']

    def _calculate(self, observations: list[dict]) -> list[dict]:
        resp = self.client.post(
            f'/api/sessions/{self.session_id}/observations/',
            observations, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        calc = self.client.post(f'/api/sessions/{self.session_id}/calculate/')
        self.assertEqual(calc.status_code, status.HTTP_200_OK)
        return calc.data['results']

    def test_eccentricity_span_bias_fails_all_positions(self) -> None:
        # Every position (center included) reads 6 g high at a 5000 g load.
        # MPE = 5 g, so every position must FAIL: the error is referenced
        # to the applied load, not the center reading.
        positions = ['center', 'front_left', 'front_right', 'rear_left', 'rear_right']
        obs = [
            {
                'test_type': 'eccentricity', 'test_point_load': '5000',
                'indicated_value': '5006', 'correction': '0',
                'position': pos, 'trial_number': i + 1,
            }
            for i, pos in enumerate(positions)
        ]
        results = self._calculate(obs)
        self.assertEqual(len(results), 5)
        for r in results:
            self.assertEqual(r['compliance_status'], 'fail')
            self.assertEqual(Decimal(r['computed_error']), Decimal('6'))

    def test_eccentricity_center_not_hardcoded_pass(self) -> None:
        # Center out of tolerance, corners compliant: only center fails.
        obs = [
            {'test_type': 'eccentricity', 'test_point_load': '5000',
             'indicated_value': '5006', 'correction': '0',
             'position': 'center', 'trial_number': 1},
            {'test_type': 'eccentricity', 'test_point_load': '5000',
             'indicated_value': '5002', 'correction': '0',
             'position': 'front_left', 'trial_number': 2},
            {'test_type': 'eccentricity', 'test_point_load': '5000',
             'indicated_value': '4998', 'correction': '0',
             'position': 'front_right', 'trial_number': 3},
        ]
        results = self._calculate(obs)
        by_pos = {r['position']: r for r in results}
        self.assertEqual(by_pos['center']['compliance_status'], 'fail')
        self.assertEqual(by_pos['front_left']['compliance_status'], 'pass')
        self.assertEqual(by_pos['front_right']['compliance_status'], 'pass')
        # Corner rows carry the informative center comparison
        self.assertIn('center indication', by_pos['front_left']['remarks'])

    def test_sensitivity_requires_04_mpe_change(self) -> None:
        # At zero load MPE = 0.5e = 2.5 g -> required change = 1 g.
        obs = [
            # Trial 1: change of 2.5 g (>= 1 g) -> PASS
            {'test_type': 'sensitivity', 'test_point_load': '0',
             'indicated_value': '0', 'correction': '0',
             'trial_number': 1, 'direction': 'increasing'},
            {'test_type': 'sensitivity', 'test_point_load': '0',
             'indicated_value': '2.5', 'correction': '0',
             'trial_number': 1, 'direction': 'decreasing'},
            # Trial 2: change of 0.5 g (< 1 g) -> FAIL despite being non-zero
            {'test_type': 'sensitivity', 'test_point_load': '0',
             'indicated_value': '0', 'correction': '0',
             'trial_number': 2, 'direction': 'increasing'},
            {'test_type': 'sensitivity', 'test_point_load': '0',
             'indicated_value': '0.5', 'correction': '0',
             'trial_number': 2, 'direction': 'decreasing'},
        ]
        results = self._calculate(obs)
        by_trial = {r['trial_number']: r for r in results}
        self.assertEqual(by_trial[1]['compliance_status'], 'pass')
        self.assertEqual(by_trial[2]['compliance_status'], 'fail')
        self.assertEqual(Decimal(by_trial[1]['mpe_applicable']), Decimal('2.5'))

    def test_hysteresis_pairing_within_mpe(self) -> None:
        obs = [
            {'test_type': 'weighing_performance', 'test_point_load': '5000',
             'indicated_value': '5002', 'correction': '0',
             'trial_number': 1, 'direction': 'increasing'},
            {'test_type': 'weighing_performance', 'test_point_load': '5000',
             'indicated_value': '5004', 'correction': '0',
             'trial_number': 2, 'direction': 'decreasing'},
        ]
        results = self._calculate(obs)
        self.assertEqual(len(results), 3)  # two point errors + one hysteresis
        hyst = [r for r in results if 'Hysteresis' in (r['remarks'] or '')]
        self.assertEqual(len(hyst), 1)
        self.assertEqual(Decimal(hyst[0]['computed_error']), Decimal('2'))
        self.assertEqual(hyst[0]['compliance_status'], 'pass')

    def test_hysteresis_exceeding_mpe_fails(self) -> None:
        # Both directions individually within MPE (+/-4 vs 5) but the
        # increasing/decreasing difference is 8 > 5 -> hysteresis FAIL.
        obs = [
            {'test_type': 'weighing_performance', 'test_point_load': '5000',
             'indicated_value': '5004', 'correction': '0',
             'trial_number': 1, 'direction': 'increasing'},
            {'test_type': 'weighing_performance', 'test_point_load': '5000',
             'indicated_value': '4996', 'correction': '0',
             'trial_number': 2, 'direction': 'decreasing'},
        ]
        results = self._calculate(obs)
        point_results = [r for r in results if 'Hysteresis' not in (r['remarks'] or '')]
        hyst = [r for r in results if 'Hysteresis' in (r['remarks'] or '')]
        for r in point_results:
            self.assertEqual(r['compliance_status'], 'pass')
        self.assertEqual(len(hyst), 1)
        self.assertEqual(Decimal(hyst[0]['computed_error']), Decimal('8'))
        self.assertEqual(hyst[0]['compliance_status'], 'fail')

    def test_half_division_method(self) -> None:
        # Changeover point: I = 5000, d = 5, delta_load = 2
        # E = I + 0.5d - dL - L = 5000 + 2.5 - 2 - 5000 = 0.5
        obs = [{
            'test_type': 'weighing_performance', 'test_point_load': '5000',
            'indicated_value': '5000', 'correction': '0',
            'delta_load': '2', 'trial_number': 1, 'direction': 'increasing',
        }]
        results = self._calculate(obs)
        self.assertEqual(len(results), 1)
        self.assertEqual(Decimal(results[0]['computed_error']), Decimal('0.5'))
        self.assertEqual(results[0]['compliance_status'], 'pass')
        self.assertIn('half-division', results[0]['remarks'])

    def test_temperature_drift_evaluated(self) -> None:
        # Class III default: 1e per 5 C -> over 10 C allowed drift = 2e = 10 g.
        obs = [
            {'test_type': 'temperature', 'test_point_load': '5000',
             'indicated_value': '5000', 'correction': '0',
             'temperature_c': '20.0', 'trial_number': 1},
            {'test_type': 'temperature', 'test_point_load': '5000',
             'indicated_value': '5003', 'correction': '0',
             'temperature_c': '30.0', 'trial_number': 2},
        ]
        results = self._calculate(obs)
        self.assertEqual(len(results), 3)  # two point errors + drift check
        drift = [r for r in results if 'Temperature effect' in (r['remarks'] or '')]
        self.assertEqual(len(drift), 1)
        self.assertEqual(Decimal(drift[0]['computed_error']), Decimal('3'))
        self.assertEqual(drift[0]['compliance_status'], 'pass')
        self.assertIn('20', drift[0]['remarks'])
        self.assertIn('30', drift[0]['remarks'])

    def test_calculate_warns_on_missing_plan_points(self) -> None:
        obs = [
            {'test_type': 'weighing_performance', 'test_point_load': '15000',
             'indicated_value': '15000', 'correction': '0',
             'trial_number': 1, 'direction': 'increasing'},
            {'test_type': 'repeatability', 'test_point_load': '7500',
             'indicated_value': '7500', 'correction': '0', 'trial_number': 1},
            {'test_type': 'repeatability', 'test_point_load': '7500',
             'indicated_value': '7500', 'correction': '0', 'trial_number': 2},
        ]
        self.client.post(
            f'/api/sessions/{self.session_id}/observations/', obs, format='json',
        )
        calc = self.client.post(f'/api/sessions/{self.session_id}/calculate/')
        warnings = calc.data['r76_2_warnings']
        self.assertTrue(
            any('test plan points not recorded' in w for w in warnings),
            warnings,
        )
        self.assertTrue(
            any('repeatability readings' in w for w in warnings),
            warnings,
        )


class TestSessionLocking(TestCase):
    """A session with an approved report must reject all modification."""

    def setUp(self) -> None:
        from apps.testing.models import TestSession
        from apps.reports.models import Report

        self.client = APIClient()
        self.lab = Laboratory.objects.create(
            name='Lock Lab', address='Addr', accreditation_number='A4', lab_code='LK',
        )
        self.engineer = User.objects.create_user(
            username='lock_eng', password='pass1234', role='engineer',
            laboratory=self.lab,
        )
        self.instrument = Instrument.objects.create(
            manufacturer='M', model_name='X', serial_number='LOCK-1',
            accuracy_class='III', max_capacity=Decimal('15000'),
            min_capacity=Decimal('100'),
            verification_scale_interval_e=Decimal('5'),
            actual_scale_interval_d=Decimal('5'),
            num_scale_intervals_n=3000, unit='g',
        )
        self.session = TestSession.objects.create(
            instrument=self.instrument, laboratory=self.lab,
            engineer=self.engineer, session_date='2026-08-31',
            status='completed', overall_verdict='pass',
        )
        Report.objects.create(
            report_number='NAWI/LK/2026/0001',
            session=self.session, generated_by=self.engineer,
            overall_verdict='pass', status='approved',
        )
        self.client.force_authenticate(user=self.engineer)

    def test_observations_rejected(self) -> None:
        resp = self.client.post(
            f'/api/sessions/{self.session.pk}/observations/',
            [{'test_type': 'weighing_performance', 'test_point_load': '500',
              'indicated_value': '500', 'correction': '0', 'trial_number': 1}],
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_calculate_rejected(self) -> None:
        resp = self.client.post(f'/api/sessions/{self.session.pk}/calculate/')
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_update_rejected(self) -> None:
        resp = self.client.patch(
            f'/api/sessions/{self.session.pk}/',
            {'humidity': '55.0'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_delete_rejected(self) -> None:
        resp = self.client.delete(f'/api/sessions/{self.session.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)


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

    def test_manager_can_review_then_approve(self) -> None:
        import tempfile

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

        # Approving an unreviewed draft is rejected
        resp = self.client.post(f'/api/reports/{report.pk}/approve/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        resp = self.client.post(f'/api/reports/{report.pk}/review/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'reviewed')

        with tempfile.TemporaryDirectory() as tmp:
            with self.settings(REPORT_STORAGE_PATH=tmp):
                resp = self.client.post(f'/api/reports/{report.pk}/approve/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'approved')
