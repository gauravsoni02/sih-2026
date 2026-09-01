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


class OrgSettings(TimeStampedModel):
    """Singleton holding organisation-wide report branding and defaults.

    Always accessed via OrgSettings.load(); pk is forced to 1.
    """

    jurisdiction = models.CharField(
        max_length=255,
        default='MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION',
    )
    report_prefix = models.CharField(max_length=20, default='NAWI')
    doc_control_number = models.CharField(max_length=50, default='LM-FMT-NAWI-01')
    doc_issue_number = models.CharField(max_length=10, default='01')
    doc_rev_number = models.CharField(max_length=10, default='00')
    # One remark per list entry; empty list means "use built-in defaults"
    default_remarks = models.JSONField(default=list, blank=True)
    # data: URI (e.g. data:image/png;base64,...) so no media storage is needed
    logo_data_uri = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Organisation settings'
        verbose_name_plural = 'Organisation settings'

    def save(self, *args, **kwargs) -> None:
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> 'OrgSettings':
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self) -> str:
        return 'Organisation settings'
