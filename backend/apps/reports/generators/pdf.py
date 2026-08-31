import logging
import os
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings
from django.template.loader import render_to_string

from apps.engine.constants import ComplianceStatus, TestType
from apps.reports.generators import _build_report_context

logger = logging.getLogger(__name__)

TEMPLATE_NAME = 'report_base.html'


def _format_decimal(val: Decimal | None) -> str:
    if val is None:
        return '—'
    normalized = val.normalize()
    if normalized == normalized.to_integral_value():
        return str(int(normalized))
    return str(normalized)


TEST_TYPE_TITLES: dict[str, str] = {
    TestType.WEIGHING_PERFORMANCE: 'Weighing Performance Test',
    TestType.ECCENTRICITY: 'Eccentricity Test',
    TestType.REPEATABILITY: 'Repeatability Test',
    TestType.DISCRIMINATION: 'Discrimination Test',
    TestType.SENSITIVITY: 'Sensitivity Test',
    TestType.TARE: 'Tare Device Test',
    TestType.CREEP: 'Creep / Time Dependence Test',
    TestType.ZERO_RETURN: 'Zero Return Test',
    TestType.TEMPERATURE: 'Temperature Test',
    TestType.TILT: 'Tilt Test',
    TestType.POWER_SUPPLY: 'Power Supply Variation Test',
    TestType.DURABILITY: 'Durability Test',
    TestType.SPAN_STABILITY: 'Span Stability Test',
    TestType.ZERO_TRACKING: 'Zero Tracking Test',
}


def _cell(value: str, numeric: bool = False, status: str = '') -> dict[str, Any]:
    return {'value': value, 'numeric': numeric, 'status': status}


def _status_label(s: str) -> str:
    if s == ComplianceStatus.PASS:
        return 'Pass'
    if s == ComplianceStatus.FAIL:
        return 'Fail'
    return 'N/A'


def _build_weighing_rows(results: list) -> tuple[list[str], list[list[dict]]]:
    columns = ['Test Load', 'Indicated', 'Error', 'MPE', 'Status']
    rows = []
    for r in results:
        rows.append([
            _cell(_format_decimal(r.test_point_load), numeric=True),
            _cell(_format_decimal(r.observation.indicated_value if r.observation else None), numeric=True),
            _cell(_format_decimal(r.computed_error), numeric=True),
            _cell(f'±{_format_decimal(r.mpe_applicable)}', numeric=True),
            _cell(_status_label(r.compliance_status), status=r.compliance_status),
        ])
    return columns, rows


def _build_eccentricity_rows(results: list) -> tuple[list[str], list[list[dict]]]:
    columns = ['Position', 'Test Load', 'Indicated', 'Error', 'MPE', 'Status']
    rows = []
    for r in results:
        pos = (r.position or '').replace('_', ' ').title()
        rows.append([
            _cell(pos),
            _cell(_format_decimal(r.test_point_load), numeric=True),
            _cell(_format_decimal(r.observation.indicated_value if r.observation else None), numeric=True),
            _cell(_format_decimal(r.computed_error), numeric=True),
            _cell(f'±{_format_decimal(r.mpe_applicable)}', numeric=True),
            _cell(_status_label(r.compliance_status), status=r.compliance_status),
        ])
    return columns, rows


def _build_repeatability_rows(results: list) -> tuple[list[str], list[list[dict]]]:
    columns = ['Trial', 'Test Load', 'Indicated', 'Error', 'MPE', 'Status']
    rows = []
    for r in results:
        rows.append([
            _cell(str(r.trial_number)),
            _cell(_format_decimal(r.test_point_load), numeric=True),
            _cell(_format_decimal(r.observation.indicated_value if r.observation else None), numeric=True),
            _cell(_format_decimal(r.computed_error), numeric=True),
            _cell(f'±{_format_decimal(r.mpe_applicable)}', numeric=True),
            _cell(_status_label(r.compliance_status), status=r.compliance_status),
        ])
    return columns, rows


def _build_generic_rows(results: list) -> tuple[list[str], list[list[dict]]]:
    columns = ['Test Load', 'Error', 'MPE', 'Status']
    rows = []
    for r in results:
        rows.append([
            _cell(_format_decimal(r.test_point_load), numeric=True),
            _cell(_format_decimal(r.computed_error), numeric=True),
            _cell(f'±{_format_decimal(r.mpe_applicable)}' if r.mpe_applicable else '—', numeric=True),
            _cell(_status_label(r.compliance_status), status=r.compliance_status),
        ])
    return columns, rows


SECTION_BUILDERS: dict[str, Any] = {
    TestType.WEIGHING_PERFORMANCE: _build_weighing_rows,
    TestType.ECCENTRICITY: _build_eccentricity_rows,
    TestType.REPEATABILITY: _build_repeatability_rows,
}


def _build_test_sections(results_qs) -> list[dict[str, Any]]:
    results_by_type: dict[str, list] = {}
    for r in results_qs.select_related('observation').order_by('test_type', 'trial_number', 'test_point_load'):
        results_by_type.setdefault(r.test_type, []).append(r)

    sections = []
    for test_type_value, label in TestType.choices:
        title = TEST_TYPE_TITLES.get(test_type_value, label)
        results = results_by_type.get(test_type_value, [])
        if not results:
            sections.append({'title': title, 'columns': [], 'results': []})
            continue

        builder = SECTION_BUILDERS.get(test_type_value, _build_generic_rows)
        columns, rows = builder(results)
        sections.append({'title': title, 'columns': columns, 'results': rows})

    return sections


def _build_compliance_summary(results_qs) -> list[dict[str, str]]:
    from django.db.models import Case, Value, When, CharField

    worst_by_type = (
        results_qs
        .values('test_type')
        .annotate(
            worst=Case(
                When(compliance_status=ComplianceStatus.FAIL, then=Value(ComplianceStatus.FAIL)),
                When(compliance_status=ComplianceStatus.PASS, then=Value(ComplianceStatus.PASS)),
                default=Value(ComplianceStatus.NOT_APPLICABLE),
                output_field=CharField(),
            )
        )
    )

    status_map: dict[str, str] = {}
    for r in results_qs.values_list('test_type', 'compliance_status'):
        tt, cs = r
        if tt not in status_map or cs == ComplianceStatus.FAIL:
            status_map[tt] = cs

    summary = []
    for test_type_value, label in TestType.choices:
        s = status_map.get(test_type_value)
        if s is None:
            continue
        summary.append({
            'test_name': TEST_TYPE_TITLES.get(test_type_value, label),
            'status': s,
            'status_label': _status_label(s),
        })
    return summary


def generate_pdf(report) -> str:
    context = _build_report_context(report)

    results_qs = report.session.results.all()
    context['test_sections'] = _build_test_sections(results_qs)
    context['compliance_summary'] = _build_compliance_summary(results_qs)

    html_string = render_to_string(TEMPLATE_NAME, context)

    storage_dir = Path(settings.REPORT_STORAGE_PATH)
    storage_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{report.report_number.replace('/', '_')}_v{report.version}.pdf"
    filepath = storage_dir / filename

    try:
        from weasyprint import HTML
        HTML(string=html_string).write_pdf(str(filepath))
    except (ImportError, OSError):
        logger.warning("WeasyPrint unavailable — falling back to ReportLab")
        _generate_pdf_reportlab(html_content=html_string, filepath=str(filepath))

    logger.info("PDF generated: %s", filepath)
    return str(filepath)


def _generate_pdf_reportlab(html_content: str, filepath: str) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    import re

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=20*mm, bottomMargin=25*mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("NAWI Test Report", styles['Title']),
        Spacer(1, 12),
        Paragraph("Non-Automatic Weighing Instrument — OIML R 76-1:2006", styles['Normal']),
        Spacer(1, 24),
    ]

    title_match = re.search(r'<title>([^<]+)</title>', html_content)
    if title_match:
        story.append(Paragraph(title_match.group(1), styles['Normal']))
        story.append(Spacer(1, 12))

    verdict_match = re.search(r'(CONFORMS|DOES NOT CONFORM)', html_content)
    if verdict_match:
        verdict_style = styles['Heading2']
        story.append(Paragraph(f"Overall: {verdict_match.group(1)} to OIML R 76-1:2006", verdict_style))
        story.append(Spacer(1, 12))

    story.append(Paragraph(
        "Note: Install WeasyPrint with GTK dependencies for fully formatted reports.",
        styles['Italic']
    ))

    doc.build(story)
