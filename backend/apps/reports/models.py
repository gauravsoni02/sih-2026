import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.engine.constants import ComplianceStatus, ReportStatus
from common.models import TimeStampedModel


def _make_verification_code() -> str:
    return secrets.token_hex(8)


class Report(TimeStampedModel):
    report_number = models.CharField(max_length=50, unique=True)
    verification_code = models.CharField(
        max_length=32, unique=True, default=_make_verification_code,
        editable=False,
    )
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
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='checked_reports',
    )
    checked_at = models.DateTimeField(null=True, blank=True)
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

        from apps.laboratory.models import OrgSettings
        year = datetime.date.today().year
        org_prefix = OrgSettings.load().report_prefix or 'NAWI'
        prefix = f"{org_prefix}/{lab_code}/{year}/"
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

    # Fields that may still change once a report is approved (file paths on
    # re-sign, soft-delete flag, workflow bookkeeping). Anything else on an
    # approved report is immutable.
    APPROVED_MUTABLE_FIELDS = frozenset({
        'is_deleted', 'updated_at', 'pdf_path', 'docx_path', 'status',
        'approved_by', 'approved_at', 'checked_by', 'checked_at',
    })

    def save(self, *args, **kwargs) -> None:
        if self.pk:
            try:
                old = Report.objects.get(pk=self.pk)
                if old.status == ReportStatus.APPROVED and self.status == ReportStatus.APPROVED:
                    update_fields = kwargs.get('update_fields') or []
                    disallowed = set(update_fields) - self.APPROVED_MUTABLE_FIELDS
                    if not update_fields or disallowed:
                        raise ValidationError(
                            "Cannot modify an approved report "
                            f"(disallowed fields: {sorted(disallowed) or 'all'})."
                        )
            except Report.DoesNotExist:
                pass
        super().save(*args, **kwargs)
