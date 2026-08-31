from django.conf import settings
from django.db import models

from apps.engine.constants import ComplianceStatus, ReportStatus
from common.models import TimeStampedModel


class Report(TimeStampedModel):
    report_number = models.CharField(max_length=50, unique=True)
    session = models.ForeignKey(
        'testing.TestSession',
        on_delete=models.PROTECT,
        related_name='reports',
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='generated_reports',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_reports',
    )
    overall_verdict = models.CharField(
        max_length=20, choices=ComplianceStatus.choices
    )
    pdf_path = models.CharField(max_length=500, blank=True)
    docx_path = models.CharField(max_length=500, blank=True)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=ReportStatus.choices, default=ReportStatus.DRAFT
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.report_number

    @staticmethod
    def generate_report_number(lab_code: str) -> str:
        import datetime
        year = datetime.date.today().year
        prefix = f"NAWI/{lab_code}/{year}/"
        last = (
            Report.objects
            .filter(report_number__startswith=prefix)
            .order_by('-report_number')
            .first()
        )
        if last:
            last_num = int(last.report_number.split('/')[-1])
            next_num = last_num + 1
        else:
            next_num = 1
        return f"{prefix}{next_num:04d}"

    def save(self, *args, **kwargs) -> None:
        if self.pk:
            try:
                old = Report.objects.get(pk=self.pk)
                if old.status == ReportStatus.APPROVED and self.status == ReportStatus.APPROVED:
                    allowed_fields = kwargs.get('update_fields', [])
                    if not allowed_fields:
                        raise ValueError("Cannot modify an approved report")
            except Report.DoesNotExist:
                pass
        super().save(*args, **kwargs)
