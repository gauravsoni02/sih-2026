from django.db import models

from common.models import TimeStampedModel


class Laboratory(TimeStampedModel):
    name = models.CharField(max_length=255)
    address = models.TextField()
    accreditation_number = models.CharField(max_length=100, unique=True)
    lab_code = models.CharField(max_length=20, unique=True)
    contact_person = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name_plural = 'Laboratories'
        ordering = ['name']

    def __str__(self) -> str:
        return f"{self.name} ({self.lab_code})"
