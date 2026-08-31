import datetime
import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.engine.constants import (
    AccuracyClass,
    ComplianceStatus,
    EvaluationType,
    SessionStatus,
    TestType,
    Unit,
)
from apps.instruments.models import Instrument
from apps.laboratory.models import Laboratory
from apps.testing.models import TestObservation, TestResult, TestSession

User = get_user_model()

MANUFACTURERS = [
    ('Mettler Toledo', 'ICS465'),
    ('Sartorius', 'Cubis II'),
    ('Shimadzu', 'UW Series'),
    ('A&D', 'GX-A Series'),
    ('Ohaus', 'Explorer'),
    ('Kern', 'ABJ-NM'),
    ('Precisa', 'ES Series'),
    ('Radwag', 'AS-R2'),
    ('Adam Equipment', 'Solis'),
    ('CAS', 'CI-200A'),
    ('Ishida', 'UNI-9'),
    ('Digi', 'DI-166'),
    ('Essae', 'DS-252'),
    ('Contech', 'CBN Series'),
    ('Wensar', 'MAB Series'),
    ('Eagle', 'Silver Series'),
    ('Swastik', 'SW-50'),
    ('Phoenix', 'PH-Series'),
    ('Goldfield', 'GF-200'),
    ('BEL Engineering', 'Mark-M'),
]

INSTRUMENT_CONFIGS = [
    {
        'accuracy_class': AccuracyClass.CLASS_III,
        'max_capacity': Decimal('30000'),
        'min_capacity': Decimal('400'),
        'e': Decimal('20'),
        'd': Decimal('20'),
        'n': 1500,
        'unit': Unit.G,
    },
    {
        'accuracy_class': AccuracyClass.CLASS_III,
        'max_capacity': Decimal('150'),
        'min_capacity': Decimal('2'),
        'e': Decimal('0.05'),
        'd': Decimal('0.05'),
        'n': 3000,
        'unit': Unit.KG,
    },
    {
        'accuracy_class': AccuracyClass.CLASS_II,
        'max_capacity': Decimal('6100'),
        'min_capacity': Decimal('500'),
        'e': Decimal('0.1'),
        'd': Decimal('0.01'),
        'n': 61000,
        'unit': Unit.G,
    },
    {
        'accuracy_class': AccuracyClass.CLASS_III,
        'max_capacity': Decimal('60'),
        'min_capacity': Decimal('0.4'),
        'e': Decimal('0.02'),
        'd': Decimal('0.02'),
        'n': 3000,
        'unit': Unit.KG,
    },
    {
        'accuracy_class': AccuracyClass.CLASS_IIII,
        'max_capacity': Decimal('500'),
        'min_capacity': Decimal('5'),
        'e': Decimal('0.5'),
        'd': Decimal('0.5'),
        'n': 1000,
        'unit': Unit.KG,
    },
]


class Command(BaseCommand):
    help = 'Load 20 demo test samples (10 pass, 10 fail) with instruments and sessions'

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear existing demo data before loading',
        )

    def handle(self, *args, **options) -> None:
        if options['clear']:
            self._clear_demo_data()

        lab, user = self._ensure_lab_and_user()

        with transaction.atomic():
            instruments = self._create_instruments()
            self._create_sessions(instruments, lab, user)

        self.stdout.write(self.style.SUCCESS(
            'Successfully loaded 20 demo samples (10 pass, 10 fail)'
        ))

    def _clear_demo_data(self) -> None:
        count, _ = Instrument.objects.filter(
            serial_number__startswith='DEMO-'
        ).delete()
        self.stdout.write(f'Cleared {count} demo records')

    def _ensure_lab_and_user(self) -> tuple:
        lab, _ = Laboratory.objects.get_or_create(
            lab_code='DEM',
            defaults={
                'name': 'Demo Metrology Lab',
                'address': 'New Delhi, India',
                'accreditation_number': 'NABL-DEMO-001',
            },
        )
        user = User.objects.filter(role='engineer').first()
        if not user:
            user = User.objects.create_user(
                username='demo_engineer',
                password='demo1234',
                role='engineer',
                laboratory=lab,
            )
        return lab, user

    def _create_instruments(self) -> list[Instrument]:
        instruments = []
        for i in range(20):
            mfr, model = MANUFACTURERS[i]
            config = INSTRUMENT_CONFIGS[i % len(INSTRUMENT_CONFIGS)]
            serial = f'DEMO-{i + 1:03d}'

            existing = Instrument.objects.filter(
                manufacturer=mfr, serial_number=serial
            ).first()
            if existing:
                instruments.append(existing)
                continue

            inst = Instrument.objects.create(
                manufacturer=mfr,
                model_name=model,
                serial_number=serial,
                accuracy_class=config['accuracy_class'],
                max_capacity=config['max_capacity'],
                min_capacity=config['min_capacity'],
                verification_scale_interval_e=config['e'],
                actual_scale_interval_d=config['d'],
                num_scale_intervals_n=config['n'],
                unit=config['unit'],
            )
            instruments.append(inst)
        return instruments

    def _create_sessions(
        self, instruments: list[Instrument], lab: Laboratory, user
    ) -> None:
        today = datetime.date.today()
        for i, inst in enumerate(instruments):
            should_pass = i < 10

            existing = TestSession.objects.filter(
                instrument=inst, laboratory=lab
            ).first()
            if existing:
                self.stdout.write(f'  Skipping {inst} — session exists')
                continue

            session = TestSession.objects.create(
                instrument=inst,
                laboratory=lab,
                engineer=user,
                session_date=today - datetime.timedelta(days=random.randint(0, 30)),
                temperature_start=Decimal('23.0'),
                temperature_end=Decimal('23.5'),
                humidity=Decimal('48.5'),
                barometric_pressure=Decimal('1013.2'),
                evaluation_type=EvaluationType.INITIAL_VERIFICATION,
                verification_type='initial',
                status=SessionStatus.COMPLETED,
                overall_verdict=(
                    ComplianceStatus.PASS if should_pass else ComplianceStatus.FAIL
                ),
            )

            self._create_observations_and_results(session, inst, should_pass)
            label = 'PASS' if should_pass else 'FAIL'
            self.stdout.write(f'  Created session #{session.id} for {inst} [{label}]')

    def _create_observations_and_results(
        self, session: TestSession, inst: Instrument, should_pass: bool
    ) -> None:
        e = inst.verification_scale_interval_e
        d = inst.actual_scale_interval_d
        max_cap = inst.max_capacity
        min_cap = inst.min_capacity
        half_max = max_cap / 2
        tare_max = inst.max_additive_tare or Decimal('0')
        ecc_load = (max_cap + tare_max) / 3

        observations = []
        results = []

        loads = [min_cap, max_cap * Decimal('0.2'), max_cap * Decimal('0.5'),
                 max_cap * Decimal('0.8'), max_cap]
        for trial, load in enumerate(loads, 1):
            if should_pass:
                error_offset = Decimal('0')
            else:
                error_offset = e * Decimal('3')

            obs_inc = TestObservation(
                session=session, test_type=TestType.WEIGHING_PERFORMANCE,
                test_point_load=load,
                indicated_value=load + error_offset,
                correction=Decimal('0'),
                direction='increasing', trial_number=trial,
            )
            observations.append(obs_inc)

            obs_dec = TestObservation(
                session=session, test_type=TestType.WEIGHING_PERFORMANCE,
                test_point_load=load,
                indicated_value=load + error_offset,
                correction=Decimal('0'),
                direction='decreasing', trial_number=trial + len(loads),
            )
            observations.append(obs_dec)

        positions = ['center', 'front_left', 'front_right', 'rear_left', 'rear_right']
        for trial, pos in enumerate(positions, 1):
            offset = Decimal('0')
            if not should_pass and pos in ('rear_left', 'rear_right'):
                offset = e * Decimal('5')
            elif pos != 'center':
                offset = e * Decimal('0.2')
            obs = TestObservation(
                session=session, test_type=TestType.ECCENTRICITY,
                test_point_load=ecc_load,
                indicated_value=ecc_load + offset,
                correction=Decimal('0'),
                position=pos, trial_number=trial,
            )
            observations.append(obs)

        for trial in range(1, 7):
            if should_pass:
                val = half_max + (e * Decimal('0.1') if trial % 2 == 0 else Decimal('0'))
            else:
                val = half_max + (e * Decimal('3') if trial % 2 == 0 else Decimal('0'))
            obs = TestObservation(
                session=session, test_type=TestType.REPEATABILITY,
                test_point_load=half_max,
                indicated_value=val,
                correction=Decimal('0'),
                trial_number=trial,
            )
            observations.append(obs)

        disc_loads = [min_cap, half_max, max_cap]
        for trial, dl in enumerate(disc_loads, 1):
            obs_before = TestObservation(
                session=session, test_type=TestType.DISCRIMINATION,
                test_point_load=dl, indicated_value=dl,
                correction=Decimal('0'),
                direction='increasing', trial_number=trial,
            )
            after_val = dl + d if should_pass else dl
            obs_after = TestObservation(
                session=session, test_type=TestType.DISCRIMINATION,
                test_point_load=dl, indicated_value=after_val,
                correction=Decimal('0'),
                direction='decreasing', trial_number=trial,
            )
            observations.append(obs_before)
            observations.append(obs_after)

        for trial, (load_str, before, after) in enumerate([
            ('0', '0', str(d)),
            (str(max_cap), str(max_cap), str(max_cap + d)),
        ], 1):
            obs_b = TestObservation(
                session=session, test_type=TestType.SENSITIVITY,
                test_point_load=Decimal(load_str),
                indicated_value=Decimal(before),
                correction=Decimal('0'),
                direction='increasing', trial_number=trial,
            )
            obs_a = TestObservation(
                session=session, test_type=TestType.SENSITIVITY,
                test_point_load=Decimal(load_str),
                indicated_value=Decimal(after),
                correction=Decimal('0'),
                direction='decreasing', trial_number=trial,
            )
            observations.append(obs_b)
            observations.append(obs_a)

        creep_offsets = {
            0: Decimal('0'),
            15: e * Decimal('0.1') if should_pass else e * Decimal('0.3'),
            30: e * Decimal('0.2') if should_pass else e * Decimal('0.8'),
        }
        for trial, (minutes, offset) in enumerate(creep_offsets.items(), 1):
            obs = TestObservation(
                session=session, test_type=TestType.CREEP,
                test_point_load=max_cap,
                indicated_value=max_cap + offset,
                correction=Decimal('0'),
                trial_number=trial,
                timestamp_minutes=Decimal(str(minutes)),
            )
            observations.append(obs)

        TestObservation.objects.bulk_create(observations)

        from apps.testing.views import _calculate_test_type
        saved_obs = session.observations.filter(is_deleted=False)
        all_results = []
        for test_type in TestType.values:
            type_obs = saved_obs.filter(test_type=test_type)
            if not type_obs.exists():
                continue
            type_results = _calculate_test_type(
                test_type, type_obs, inst, session.verification_type
            )
            all_results.extend(type_results)

        TestResult.objects.bulk_create(all_results)
