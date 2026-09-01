from django.conf import settings
from django.db import models

from apps.engine.constants import ComplianceStatus, EvaluationType, SessionStatus, TestType
from common.models import TimeStampedModel


class TestSession(TimeStampedModel):
    instrument = models.ForeignKey(
        'instruments.Instrument',
        on_delete=models.PROTECT,
        related_name='test_sessions',
    )
    laboratory = models.ForeignKey(
        'laboratory.Laboratory',
        on_delete=models.PROTECT,
        related_name='test_sessions',
    )
    engineer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='test_sessions',
    )
    session_date = models.DateField()
    temperature_start = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    temperature_end = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    humidity = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    barometric_pressure = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    evaluation_type = models.CharField(
        max_length=30,
        choices=EvaluationType.choices,
        default=EvaluationType.INITIAL_VERIFICATION,
    )
    verification_type = models.CharField(
        max_length=20, default='initial',
        choices=[('initial', 'Initial'), ('subsequent', 'Subsequent')],
    )
    customer_name = models.CharField(max_length=255, blank=True)
    customer_address = models.TextField(blank=True)
    customer_contact = models.CharField(max_length=255, blank=True)
    request_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=SessionStatus.choices, default=SessionStatus.DRAFT
    )
    overall_verdict = models.CharField(
        max_length=20, choices=ComplianceStatus.choices, null=True, blank=True
    )

    class Meta:
        ordering = ['-session_date', '-created_at']

    def __str__(self) -> str:
        return f"Session {self.id} - {self.instrument} ({self.session_date})"


class TestObservation(TimeStampedModel):
    session = models.ForeignKey(
        TestSession,
        on_delete=models.CASCADE,
        related_name='observations',
    )
    test_type = models.CharField(max_length=30, choices=TestType.choices)
    test_point_load = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    indicated_value = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    reference_value = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    correction = models.DecimalField(
        max_digits=15, decimal_places=6, default=0
    )
    position = models.CharField(max_length=20, blank=True)
    trial_number = models.PositiveIntegerField(default=1)
    direction = models.CharField(
        max_length=20, blank=True,
        choices=[('increasing', 'Increasing'), ('decreasing', 'Decreasing')],
    )
    timestamp_minutes = models.DecimalField(
        max_digits=6, decimal_places=1, null=True, blank=True,
        help_text='Minutes elapsed, for creep tests (0, 15, 30)',
    )
    delta_load = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True,
        help_text=(
            'Additional load ΔL at which the indication changed over to '
            'I + d (changeover-point / half-division method, R 76-2 A.4.4.3). '
            'When set, the error is computed as E = I + 0.5d − ΔL − L.'
        ),
    )
    temperature_c = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Ambient temperature (°C) at which this observation was taken',
    )

    class Meta:
        ordering = ['test_type', 'trial_number', 'test_point_load']

    def __str__(self) -> str:
        return f"{self.test_type} @ {self.test_point_load} (trial {self.trial_number})"


class TestResult(TimeStampedModel):
    session = models.ForeignKey(
        TestSession,
        on_delete=models.CASCADE,
        related_name='results',
    )
    test_type = models.CharField(max_length=30, choices=TestType.choices)
    observation = models.ForeignKey(
        TestObservation,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='results',
    )
    test_point_load = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    computed_error = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    mpe_applicable = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    expanded_uncertainty = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True,
        help_text='Expanded measurement uncertainty U (k=2)',
    )
    compliance_status = models.CharField(
        max_length=20, choices=ComplianceStatus.choices
    )
    position = models.CharField(max_length=20, blank=True)
    trial_number = models.PositiveIntegerField(default=1)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['test_type', 'trial_number', 'test_point_load']
