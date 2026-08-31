import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_report_task(self, report_id: int) -> dict:
    from apps.reports.models import Report
    from apps.reports.generators.pdf import generate_pdf
    from apps.reports.generators.docx import generate_docx

    try:
        report = Report.objects.select_related(
            'session__instrument',
            'session__laboratory',
            'session__engineer',
            'approved_by',
        ).get(pk=report_id)

        pdf_path = generate_pdf(report)
        report.pdf_path = pdf_path
        report.save(update_fields=['pdf_path', 'updated_at'])

        docx_path = generate_docx(report)
        report.docx_path = docx_path
        report.save(update_fields=['docx_path', 'updated_at'])

        logger.info("Report %s generated successfully (PDF + DOCX)", report.report_number)
        return {
            'report_id': report.id,
            'report_number': report.report_number,
            'pdf_path': pdf_path,
            'docx_path': docx_path,
        }
    except Report.DoesNotExist:
        logger.error("Report %s not found", report_id)
        raise
    except Exception as exc:
        logger.exception("Report generation failed for report %s", report_id)
        raise self.retry(exc=exc)
