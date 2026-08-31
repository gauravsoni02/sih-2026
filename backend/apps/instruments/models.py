from django.db import models

from apps.engine.constants import AccuracyClass, Unit
from common.models import TimeStampedModel


class Instrument(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        UNDER_TEST = 'under_test', 'Under Test'

    class TareDeviceType(models.TextChoices):
        NONE = 'none', 'None'
        NON_ADDITIVE = 'non_additive', 'Non-Additive (Subtractive)'
        ADDITIVE = 'additive', 'Additive'
        BOTH = 'both', 'Both'

    manufacturer = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=100)
    accuracy_class = models.CharField(max_length=4, choices=AccuracyClass.choices)
    max_capacity = models.DecimalField(max_digits=15, decimal_places=6)
    min_capacity = models.DecimalField(max_digits=15, decimal_places=6)
    verification_scale_interval_e = models.DecimalField(max_digits=15, decimal_places=6)
    actual_scale_interval_d = models.DecimalField(max_digits=15, decimal_places=6)
    num_scale_intervals_n = models.PositiveIntegerField()
    unit = models.CharField(max_length=5, choices=Unit.choices, default=Unit.KG)
    tare_device_type = models.CharField(
        max_length=20, choices=TareDeviceType.choices, default=TareDeviceType.NONE
    )
    max_additive_tare = models.DecimalField(
        max_digits=15, decimal_places=6, default=0
    )
    max_safe_load = models.DecimalField(
        max_digits=15, decimal_places=6, null=True, blank=True
    )
    is_multi_interval = models.BooleanField(default=False)
    multi_interval_config = models.JSONField(
        null=True, blank=True,
        help_text='[{"max": 2000, "e": 1}, {"max": 5000, "e": 2}]'
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['manufacturer', 'serial_number'],
                name='unique_serial_per_manufacturer',
            ),
        ]
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.manufacturer} {self.model_name} ({self.serial_number})"
