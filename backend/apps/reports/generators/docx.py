import logging
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings

from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from apps.engine.constants import ComplianceStatus, TestType
from apps.reports.generators import _build_report_context

logger = logging.getLogger(__name__)

PASS_COLOR = RGBColor(0x38, 0x9E, 0x0D)
FAIL_COLOR = RGBColor(0xCF, 0x13, 0x22)
GRAY_COLOR = RGBColor(0x66, 0x66, 0x66)

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


def _format_decimal(val: Decimal | None) -> str:
    if val is None:
        return '—'
    normalized = val.normalize()
    if normalized == normalized.to_integral_value():
        return str(int(normalized))
    return str(normalized)


def _status_label(s: str) -> str:
    if s == ComplianceStatus.PASS:
        return 'Pass'
    if s == ComplianceStatus.FAIL:
        return 'Fail'
    return 'N/A'


def _add_kv_row(table, label: str, value: str) -> None:
    row = table.add_row()
    cell_label = row.cells[0]
    cell_value = row.cells[1]
    run_label = cell_label.paragraphs[0].add_run(label)
    run_label.font.size = Pt(10)
    run_label.font.color.rgb = GRAY_COLOR
    run_value = cell_value.paragraphs[0].add_run(str(value) if value else '—')
    run_value.font.size = Pt(10)


def _set_cell_shading(cell, color_hex: str) -> None:
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color_hex)
    shading.set(qn('w:val'), 'clear')
    cell._tc.get_or_add_tcPr().append(shading)


def _style_header_row(row) -> None:
    for cell in row.cells:
        _set_cell_shading(cell, 'F5F5F5')
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(9)


def generate_docx(report) -> str:
    context = _build_report_context(report)
    session = report.session
    instrument = session.instrument
    results_qs = session.results.select_related('observation').order_by(
        'test_type', 'trial_number', 'test_point_load'
    )

    doc = Document()

    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(10)

    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)

    # --- COVER PAGE ---
    for _ in range(4):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(context['lab_name'])
    run.font.size = Pt(16)
    run.font.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"Accreditation No: {context['accreditation_number']}")
    run.font.size = Pt(10)
    run.font.color.rgb = GRAY_COLOR

    if context.get('lab_address'):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(context['lab_address'])
        run.font.size = Pt(9)
        run.font.color.rgb = GRAY_COLOR

    doc.add_paragraph()
    doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('Test Report')
    run.font.size = Pt(22)
    run.font.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('Non-Automatic Weighing Instrument\nas per OIML R 76-1:2006')
    run.font.size = Pt(12)
    run.font.color.rgb = GRAY_COLOR

    doc.add_paragraph()

    meta_table = doc.add_table(rows=0, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for label, value in [
        ('Report Number', context['report_number']),
        ('Date of Test', context['session_date']),
        ('Report Version', str(context['version'])),
        ('Evaluation Type', context['evaluation_type_label']),
        ('Verification Type', context['verification_type_label']),
    ]:
        _add_kv_row(meta_table, label, value)

    doc.add_page_break()

    # --- 1. INSTRUMENT DETAILS ---
    doc.add_heading('1. Instrument Under Test', level=2)

    inst_table = doc.add_table(rows=0, cols=2)
    unit = instrument.unit
    for label, value in [
        ('Manufacturer', instrument.manufacturer),
        ('Model', instrument.model_name),
        ('Serial Number', instrument.serial_number),
        ('Accuracy Class', instrument.accuracy_class),
        ('Max Capacity (Max)', f'{_format_decimal(instrument.max_capacity)} {unit}'),
        ('Min Capacity (Min)', f'{_format_decimal(instrument.min_capacity)} {unit}'),
        ('Verification Interval (e)', f'{_format_decimal(instrument.verification_scale_interval_e)} {unit}'),
        ('Actual Scale Interval (d)', f'{_format_decimal(instrument.actual_scale_interval_d)} {unit}'),
        ('Number of Intervals (n)', str(instrument.num_scale_intervals_n)),
        ('Tare Device', instrument.tare_device_type),
    ]:
        _add_kv_row(inst_table, label, value)

    if instrument.max_safe_load:
        _add_kv_row(inst_table, 'Max Safe Load (Lim)', f'{_format_decimal(instrument.max_safe_load)} {unit}')
    if instrument.is_multi_interval:
        _add_kv_row(inst_table, 'Multi-Interval', 'Yes')

    # --- 2. ENVIRONMENTAL CONDITIONS ---
    doc.add_heading('2. Environmental Conditions', level=2)

    env_table = doc.add_table(rows=0, cols=2)
    if context['temperature_start'] is not None:
        _add_kv_row(env_table, 'Temperature (Start)', f"{context['temperature_start']} °C")
    if context['temperature_end'] is not None:
        _add_kv_row(env_table, 'Temperature (End)', f"{context['temperature_end']} °C")
    if context['humidity'] is not None:
        _add_kv_row(env_table, 'Relative Humidity', f"{context['humidity']} %")
    if context['barometric_pressure'] is not None:
        _add_kv_row(env_table, 'Barometric Pressure', f"{context['barometric_pressure']} hPa")

    # --- 3. TEST RESULTS ---
    doc.add_heading('3. Test Results', level=2)

    results_by_type: dict[str, list] = {}
    for r in results_qs:
        results_by_type.setdefault(r.test_type, []).append(r)

    section_num = 1
    for test_type_value, label in TestType.choices:
        title = TEST_TYPE_TITLES.get(test_type_value, label)
        results = results_by_type.get(test_type_value, [])

        doc.add_heading(f'3.{section_num} {title}', level=3)
        section_num += 1

        if not results:
            p = doc.add_paragraph('No observations recorded for this test.')
            p.runs[0].font.color.rgb = GRAY_COLOR
            p.runs[0].font.italic = True
            continue

        if test_type_value == TestType.WEIGHING_PERFORMANCE:
            headers = ['Test Load', 'Indicated', 'Error', 'MPE', 'Status']
        elif test_type_value == TestType.ECCENTRICITY:
            headers = ['Position', 'Test Load', 'Indicated', 'Error', 'MPE', 'Status']
        elif test_type_value == TestType.REPEATABILITY:
            headers = ['Trial', 'Test Load', 'Indicated', 'Error', 'MPE', 'Status']
        else:
            headers = ['Test Load', 'Error', 'MPE', 'Status']

        table = doc.add_table(rows=1, cols=len(headers))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        header_row = table.rows[0]
        for i, h in enumerate(headers):
            header_row.cells[i].text = h
        _style_header_row(header_row)

        for r in results:
            row = table.add_row()
            indicated = _format_decimal(r.observation.indicated_value if r.observation else None)
            mpe_str = f'±{_format_decimal(r.mpe_applicable)}' if r.mpe_applicable else '—'
            status_text = _status_label(r.compliance_status)

            if test_type_value == TestType.ECCENTRICITY:
                pos = (r.position or '').replace('_', ' ').title()
                cells_data = [pos, _format_decimal(r.test_point_load), indicated,
                              _format_decimal(r.computed_error), mpe_str, status_text]
            elif test_type_value == TestType.REPEATABILITY:
                cells_data = [str(r.trial_number), _format_decimal(r.test_point_load), indicated,
                              _format_decimal(r.computed_error), mpe_str, status_text]
            elif test_type_value == TestType.WEIGHING_PERFORMANCE:
                cells_data = [_format_decimal(r.test_point_load), indicated,
                              _format_decimal(r.computed_error), mpe_str, status_text]
            else:
                cells_data = [_format_decimal(r.test_point_load),
                              _format_decimal(r.computed_error), mpe_str, status_text]

            for i, val in enumerate(cells_data):
                cell = row.cells[i]
                cell.text = ''
                run = cell.paragraphs[0].add_run(val)
                run.font.size = Pt(9)
                if val in ('Pass', 'Fail'):
                    run.font.bold = True
                    run.font.color.rgb = PASS_COLOR if val == 'Pass' else FAIL_COLOR

        doc.add_paragraph()

    # --- 4. COMPLIANCE SUMMARY ---
    doc.add_page_break()
    doc.add_heading('4. Compliance Summary', level=2)

    status_map: dict[str, str] = {}
    for r in results_qs:
        tt = r.test_type
        cs = r.compliance_status
        if tt not in status_map or cs == ComplianceStatus.FAIL:
            status_map[tt] = cs

    summary_table = doc.add_table(rows=1, cols=2)
    summary_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = summary_table.rows[0]
    hdr.cells[0].text = 'Test'
    hdr.cells[1].text = 'Result'
    _style_header_row(hdr)

    for test_type_value, label in TestType.choices:
        s = status_map.get(test_type_value)
        if s is None:
            continue
        row = summary_table.add_row()
        row.cells[0].text = TEST_TYPE_TITLES.get(test_type_value, label)
        cell = row.cells[1]
        cell.text = ''
        run = cell.paragraphs[0].add_run(_status_label(s))
        run.font.bold = True
        run.font.color.rgb = PASS_COLOR if s == ComplianceStatus.PASS else FAIL_COLOR

    # --- OVERALL VERDICT ---
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if context['overall_verdict'] == ComplianceStatus.PASS:
        run = p.add_run('CONFORMS to OIML R 76-1:2006')
        run.font.color.rgb = PASS_COLOR
    else:
        run = p.add_run('DOES NOT CONFORM to OIML R 76-1:2006')
        run.font.color.rgb = FAIL_COLOR
    run.font.size = Pt(14)
    run.font.bold = True

    # --- 5. SIGNATORIES ---
    doc.add_paragraph()
    doc.add_heading('5. Signatories', level=2)

    sig_table = doc.add_table(rows=3, cols=3)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (role, name, date) in enumerate([
        ('Tested by', context['engineer_name'], f"Date: {context['session_date']}"),
        ('Checked by', context.get('checked_by_name') or '________________', 'Date: ________________'),
        ('Approved by', context.get('approved_by_name') or '________________',
         f"Date: {context['approved_at']}" if context.get('approved_at') else 'Date: ________________'),
    ]):
        sig_table.rows[0].cells[i].text = role
        sig_table.rows[1].cells[i].text = name
        sig_table.rows[2].cells[i].text = date
        for row_idx in range(3):
            for run in sig_table.rows[row_idx].cells[i].paragraphs[0].runs:
                run.font.size = Pt(9)

    # --- FOOTER ---
    doc.add_paragraph()
    p = doc.add_paragraph()
    run = p.add_run(
        f"This report was generated by the NAWI Test Report Generator v{context.get('software_version', '1.0')}.\n"
        "Standard reference: OIML R 76-1:2006 — Non-automatic weighing instruments, "
        "Part 1: Metrological and technical requirements — Tests."
    )
    run.font.size = Pt(8)
    run.font.color.rgb = GRAY_COLOR

    # --- SAVE ---
    storage_dir = Path(settings.REPORT_STORAGE_PATH)
    storage_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{report.report_number.replace('/', '_')}_v{report.version}.docx"
    filepath = storage_dir / filename
    doc.save(str(filepath))

    logger.info("DOCX generated: %s", filepath)
    return str(filepath)
