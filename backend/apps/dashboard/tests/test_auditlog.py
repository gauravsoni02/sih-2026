from decimal import Decimal

from auditlog.models import LogEntry
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.engine.constants import AccuracyClass, Unit
from apps.instruments.models import Instrument
from apps.laboratory.models import Laboratory

User = get_user_model()


class TestAuditLog(TestCase):
    def setUp(self) -> None:
        self.lab = Laboratory.objects.create(
            name='Audit Lab', address='Addr',
            accreditation_number='ACC-AL-001', lab_code='ALT',
        )
        self.user = User.objects.create_user(
            username='auditor', password='pass1234',
            role='engineer', laboratory=self.lab,
        )

    def test_instrument_create_logged(self) -> None:
        instrument = Instrument.objects.create(
            manufacturer='TestCo', model_name='M1', serial_number='SN-AL-001',
            accuracy_class=AccuracyClass.CLASS_III, max_capacity=Decimal('10'),
            min_capacity=Decimal('0.2'), verification_scale_interval_e=Decimal('0.01'),
            actual_scale_interval_d=Decimal('0.01'), num_scale_intervals_n=1000,
            unit=Unit.KG,
        )
        logs = LogEntry.objects.get_for_object(instrument)
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().action, LogEntry.Action.CREATE)

    def test_instrument_update_logged(self) -> None:
        instrument = Instrument.objects.create(
            manufacturer='TestCo', model_name='M1', serial_number='SN-AL-002',
            accuracy_class=AccuracyClass.CLASS_III, max_capacity=Decimal('10'),
            min_capacity=Decimal('0.2'), verification_scale_interval_e=Decimal('0.01'),
            actual_scale_interval_d=Decimal('0.01'), num_scale_intervals_n=1000,
            unit=Unit.KG,
        )
        instrument.manufacturer = 'UpdatedCo'
        instrument.save()

        logs = LogEntry.objects.get_for_object(instrument)
        self.assertEqual(logs.count(), 2)
        update_log = logs.filter(action=LogEntry.Action.UPDATE).first()
        self.assertIsNotNone(update_log)
        self.assertIn('manufacturer', update_log.changes)

    def test_laboratory_create_logged(self) -> None:
        lab = Laboratory.objects.create(
            name='New Lab', address='New Addr',
            accreditation_number='ACC-AL-002', lab_code='NLB',
        )
        logs = LogEntry.objects.get_for_object(lab)
        self.assertEqual(logs.count(), 1)

    def test_soft_delete_logged(self) -> None:
        instrument = Instrument.objects.create(
            manufacturer='TestCo', model_name='M1', serial_number='SN-AL-003',
            accuracy_class=AccuracyClass.CLASS_III, max_capacity=Decimal('10'),
            min_capacity=Decimal('0.2'), verification_scale_interval_e=Decimal('0.01'),
            actual_scale_interval_d=Decimal('0.01'), num_scale_intervals_n=1000,
            unit=Unit.KG,
        )
        instrument.soft_delete()

        logs = LogEntry.objects.get_for_object(instrument)
        self.assertEqual(logs.count(), 2)
        update_log = logs.filter(action=LogEntry.Action.UPDATE).first()
        self.assertIsNotNone(update_log)
        self.assertIn('is_deleted', update_log.changes)

    def test_user_create_logged(self) -> None:
        user = User.objects.create_user(
            username='newuser', password='pass1234', role='viewer',
        )
        logs = LogEntry.objects.get_for_object(user)
        self.assertEqual(logs.count(), 1)
