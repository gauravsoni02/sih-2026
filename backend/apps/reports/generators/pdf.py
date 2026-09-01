import logging
import os
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.conf import settings

from apps.engine.constants import ComplianceStatus, TestType
from apps.reports.generators import _build_report_context, build_uncertainty_budget

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

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

TEST_TYPE_ORDER: list[str] = [v for v, _ in TestType.choices]


def _status_label(s: str) -> str:
    if s == ComplianceStatus.PASS:
        return 'Pass'
    if s == ComplianceStatus.FAIL:
        return 'Fail'
    return 'N/A'


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_pdf(report) -> str:
    """Generate a NABL-style calibration certificate PDF for *report*.

    Returns the absolute file path of the generated PDF.
    """
    context = _build_report_context(report)

    results_qs = report.session.results.all()
    context['test_sections'] = _build_test_sections(results_qs)
    context['compliance_summary'] = _build_compliance_summary(results_qs)
    context['uncertainty_budget'] = build_uncertainty_budget(report.session)

    storage_dir = Path(settings.REPORT_STORAGE_PATH)
    storage_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{report.report_number.replace('/', '_')}_v{report.version}.pdf"
    filepath = storage_dir / filename

    _generate_pdf_reportlab(context=context, filepath=str(filepath))

    logger.info("PDF generated: %s", filepath)
    return str(filepath)


# ---------------------------------------------------------------------------
# Data builders (test sections & compliance summary)
# ---------------------------------------------------------------------------

def _build_test_sections(results_qs) -> list[dict[str, Any]]:
    results_by_type: dict[str, list] = {}
    for r in results_qs.select_related('observation').order_by(
        'test_type', 'trial_number', 'test_point_load'
    ):
        results_by_type.setdefault(r.test_type, []).append(r)

    sections = []
    for test_type_value, label in TestType.choices:
        title = TEST_TYPE_TITLES.get(test_type_value, label)
        results = results_by_type.get(test_type_value, [])
        if not results:
            sections.append({
                'title': title,
                'test_type': test_type_value,
                'results': [],
            })
            continue
        sections.append({
            'title': title,
            'test_type': test_type_value,
            'results': results,
        })
    return sections


def _build_compliance_summary(results_qs) -> list[dict[str, str]]:
    status_map: dict[str, str] = {}
    for tt, cs in results_qs.values_list('test_type', 'compliance_status'):
        if tt not in status_map or cs == ComplianceStatus.FAIL:
            status_map[tt] = cs

    summary = []
    for test_type_value, label in TestType.choices:
        s = status_map.get(test_type_value)
        if s is None:
            continue
        summary.append({
            'test_name': TEST_TYPE_TITLES.get(test_type_value, label),
            'test_type': test_type_value,
            'status': s,
            'status_label': _status_label(s),
        })
    return summary


# ===================================================================
# ReportLab PDF implementation -- NABL-style calibration certificate
# ===================================================================

def _generate_pdf_reportlab(*, context: dict[str, Any], filepath: str) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        NextPageTemplate,
        PageBreak,
        PageTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        KeepTogether,
    )
    from reportlab.platypus.flowables import HRFlowable

    PAGE_W, PAGE_H = A4
    MARGIN_LEFT = 15 * mm
    MARGIN_RIGHT = 15 * mm
    MARGIN_TOP = 20 * mm
    MARGIN_BOTTOM = 15 * mm

    FRAME_W = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT

    # -------------------------------------------------------------------
    # Colours
    # -------------------------------------------------------------------
    CLR_HEADER_BG = colors.HexColor('#E8E8E8')
    CLR_ALT_ROW = colors.HexColor('#FAFAFA')
    CLR_PASS = colors.HexColor('#006400')
    CLR_FAIL = colors.HexColor('#8B0000')
    CLR_GRAY = colors.HexColor('#888888')
    CLR_RULE = colors.HexColor('#333333')
    CLR_BORDER = colors.HexColor('#999999')
    CLR_BLACK = colors.black
    CLR_WHITE = colors.white

    # -------------------------------------------------------------------
    # Paragraph styles
    # -------------------------------------------------------------------
    base_styles = getSampleStyleSheet()

    sty_govt = ParagraphStyle(
        'GovtHeader', parent=base_styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12, leading=15,
        alignment=TA_CENTER, spaceAfter=0, spaceBefore=0,
        textTransform='uppercase',
    )
    sty_lab = ParagraphStyle(
        'LabHeader', parent=base_styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12, leading=15,
        alignment=TA_CENTER, spaceAfter=0, spaceBefore=2,
    )
    sty_lab_addr = ParagraphStyle(
        'LabAddr', parent=base_styles['Normal'],
        fontName='Helvetica-Bold', fontSize=11, leading=14,
        alignment=TA_CENTER, spaceAfter=0, spaceBefore=1,
    )
    sty_title = ParagraphStyle(
        'CertTitle', parent=base_styles['Normal'],
        fontName='Helvetica-Bold', fontSize=14, leading=17,
        alignment=TA_CENTER, spaceAfter=2, spaceBefore=6,
    )
    sty_subtitle = ParagraphStyle(
        'CertSubtitle', parent=base_styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=13,
        alignment=TA_CENTER, spaceAfter=2, spaceBefore=1,
    )
    sty_cert_line = ParagraphStyle(
        'CertLine', parent=base_styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=12,
        alignment=TA_CENTER, spaceAfter=1, spaceBefore=1,
    )
    sty_section = ParagraphStyle(
        'SectionHead', parent=base_styles['Normal'],
        fontName='Helvetica-Bold', fontSize=11, leading=14,
        alignment=TA_LEFT, spaceAfter=2, spaceBefore=6,
    )
    sty_cell = ParagraphStyle(
        'Cell', parent=base_styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=11,
        alignment=TA_LEFT,
    )
    sty_cell_bold = ParagraphStyle(
        'CellBold', parent=base_styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9, leading=11,
        alignment=TA_LEFT,
    )
    sty_cell_center = ParagraphStyle(
        'CellCenter', parent=base_styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=11,
        alignment=TA_CENTER,
    )
    sty_cell_center_bold = ParagraphStyle(
        'CellCenterBold', parent=base_styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9, leading=11,
        alignment=TA_CENTER,
    )
    sty_cell_right = ParagraphStyle(
        'CellRight', parent=base_styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=11,
        alignment=TA_RIGHT,
    )
    sty_normal = ParagraphStyle(
        'BodyNormal', parent=base_styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=12,
        alignment=TA_LEFT,
    )
    sty_normal_center = ParagraphStyle(
        'BodyCenter', parent=base_styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=12,
        alignment=TA_CENTER,
    )
    sty_italic_gray = ParagraphStyle(
        'ItalicGray', parent=base_styles['Normal'],
        fontName='Helvetica-Oblique', fontSize=9, leading=12,
        alignment=TA_LEFT, textColor=CLR_GRAY,
    )
    sty_remark = ParagraphStyle(
        'Remark', parent=base_styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=10,
        alignment=TA_LEFT, leftIndent=12,
    )
    sty_conclusion = ParagraphStyle(
        'Conclusion', parent=base_styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=13,
        alignment=TA_LEFT, spaceBefore=4, spaceAfter=4,
    )

    # -------------------------------------------------------------------
    # Shared cell-padding for tables
    # -------------------------------------------------------------------
    CELL_PAD_V = 6
    CELL_PAD_H = 8

    def _base_table_style(n_rows: int, has_header: bool = True) -> list:
        """Return a list of TableStyle commands common to all bordered tables."""
        cmds: list = [
            ('GRID', (0, 0), (-1, -1), 0.5, CLR_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), CELL_PAD_V),
            ('BOTTOMPADDING', (0, 0), (-1, -1), CELL_PAD_V),
            ('LEFTPADDING', (0, 0), (-1, -1), CELL_PAD_H),
            ('RIGHTPADDING', (0, 0), (-1, -1), CELL_PAD_H),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        if has_header:
            cmds.append(('BACKGROUND', (0, 0), (-1, 0), CLR_HEADER_BG))
        # alternating rows (skip header)
        start = 1 if has_header else 0
        for i in range(start, n_rows):
            if (i - start) % 2 == 1:
                cmds.append(('BACKGROUND', (0, i), (-1, i), CLR_ALT_ROW))
        return cmds

    # -------------------------------------------------------------------
    # Status-coloured paragraph helper
    # -------------------------------------------------------------------
    def _status_para(status: str, label: str | None = None) -> Paragraph:
        text = label or _status_label(status)
        if status == ComplianceStatus.PASS:
            return Paragraph(
                f'<font color="#{CLR_PASS.hexval()[2:]}">{text}</font>',
                sty_cell_center,
            )
        if status == ComplianceStatus.FAIL:
            return Paragraph(
                f'<font color="#{CLR_FAIL.hexval()[2:]}">{text}</font>',
                sty_cell_center,
            )
        return Paragraph(
            f'<i><font color="#{CLR_GRAY.hexval()[2:]}">{text}</font></i>',
            sty_cell_center,
        )

    # -------------------------------------------------------------------
    # Extract context values
    # -------------------------------------------------------------------
    report_number = context['report_number']
    accreditation_number = context.get('accreditation_number', '')
    lab_name = context.get('lab_name', '')
    lab_address = context.get('lab_address', '')
    evaluation_type_label = context.get('evaluation_type_label', '')
    verification_type_label = context.get('verification_type_label', '')
    session_date = context.get('session_date', '')
    overall_verdict = context.get('overall_verdict', '')
    instrument = context.get('instrument')
    temperature_start = context.get('temperature_start')
    temperature_end = context.get('temperature_end')
    humidity = context.get('humidity')
    barometric_pressure = context.get('barometric_pressure')
    engineer_name = context.get('engineer_name', '')
    checked_by_name = context.get('checked_by_name', '')
    approved_by_name = context.get('approved_by_name', '')
    approved_at = context.get('approved_at', '')
    software_version = context.get('software_version', '1.0')
    test_sections = context.get('test_sections', [])
    compliance_summary = context.get('compliance_summary', [])
    jurisdiction = context.get(
        'jurisdiction', 'MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION')
    doc_control_number = context.get('doc_control_number', 'LM-FMT-NAWI-01')
    doc_issue_number = context.get('doc_issue_number', '01')
    doc_rev_number = context.get('doc_rev_number', '00')
    logo_data_uri = context.get('logo_data_uri', '')

    # Format session date nicely
    try:
        from datetime import date as _date, datetime as _dt
        if isinstance(session_date, str) and session_date:
            _d = _dt.strptime(session_date, '%Y-%m-%d').date()
            session_date_fmt = _d.strftime('%d %b %Y')
        elif isinstance(session_date, _date):
            session_date_fmt = session_date.strftime('%d %b %Y')
        else:
            session_date_fmt = str(session_date)
    except Exception:
        session_date_fmt = str(session_date)

    # -------------------------------------------------------------------
    # Instrument details helper
    # -------------------------------------------------------------------
    unit_str = instrument.unit if instrument else 'kg'

    def _inst(attr: str, fallback: str = '—') -> str:
        if instrument is None:
            return fallback
        val = getattr(instrument, attr, None)
        if val is None:
            return fallback
        if isinstance(val, Decimal):
            return _format_decimal(val)
        return str(val)

    def _tare_label() -> str:
        if instrument is None:
            return '—'
        raw = instrument.tare_device_type
        return {
            'none': 'None',
            'non_additive': 'Non-Additive (Subtractive)',
            'additive': 'Additive',
            'both': 'Both (Additive & Non-Additive)',
        }.get(raw, raw)

    def _accuracy_label() -> str:
        if instrument is None:
            return '—'
        return {
            'I': 'Class I (Special)',
            'II': 'Class II (High)',
            'III': 'Class III (Medium)',
            'IIII': 'Class IIII (Ordinary)',
        }.get(instrument.accuracy_class, instrument.accuracy_class)

    # -------------------------------------------------------------------
    # Page-level callbacks (header / footer)
    # -------------------------------------------------------------------
    _page_count_holder: dict[str, int] = {'total': 0}

    DOC_CONTROL = (
        f'Doc No: {doc_control_number}  |  Issue No: {doc_issue_number}  |  '
        f'Rev No: {doc_rev_number}  |  Software v{software_version}'
    )

    def _draw_header_footer(canvas, doc):
        canvas.saveState()
        page_num = doc.page
        # -- repeating header --
        y_top = PAGE_H - 12 * mm
        canvas.setFont('Helvetica', 8)
        canvas.drawString(MARGIN_LEFT, y_top,
                          f'Certificate No: {report_number}')
        canvas.drawRightString(PAGE_W - MARGIN_RIGHT, y_top,
                               f'ULR No: {accreditation_number}')
        canvas.drawCentredString(PAGE_W / 2, y_top,
                                 f'Page {page_num}')
        canvas.setStrokeColor(CLR_RULE)
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN_LEFT, y_top - 3, PAGE_W - MARGIN_RIGHT, y_top - 3)

        # -- repeating footer --
        y_bot = MARGIN_BOTTOM - 4 * mm
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(CLR_GRAY)
        canvas.drawCentredString(PAGE_W / 2, y_bot, DOC_CONTROL)
        canvas.restoreState()

    def _draw_first_page(canvas, doc):
        _draw_header_footer(canvas, doc)

    def _draw_later_page(canvas, doc):
        _draw_header_footer(canvas, doc)

    # -------------------------------------------------------------------
    # Build the document
    # -------------------------------------------------------------------
    frame_first = Frame(
        MARGIN_LEFT, MARGIN_BOTTOM,
        FRAME_W, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM,
        id='first',
    )
    frame_later = Frame(
        MARGIN_LEFT, MARGIN_BOTTOM,
        FRAME_W, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM,
        id='later',
    )

    doc = BaseDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )
    doc.addPageTemplates([
        PageTemplate(id='First', frames=[frame_first],
                     onPage=_draw_first_page),
        PageTemplate(id='Later', frames=[frame_later],
                     onPage=_draw_later_page),
    ])

    story: list = []

    # ===================================================================
    # PAGE 1 -- Title / header block
    # ===================================================================
    jurisdiction_escaped = jurisdiction.replace('&', '&amp;')
    header_flowables = [
        Paragraph('GOVERNMENT OF INDIA', sty_govt),
        Paragraph(jurisdiction_escaped, sty_govt),
        Paragraph('DEPARTMENT OF CONSUMER AFFAIRS', sty_govt),
        Spacer(1, 6),
        Paragraph('LEGAL METROLOGY LABORATORY', sty_lab),
        Paragraph(f'{lab_name}, {lab_address}', sty_lab_addr),
    ]
    logo_img = _load_logo_image(logo_data_uri) if logo_data_uri else None
    if logo_img is not None:
        # Logo top-left (max 60x60px ~ 16mm), header text block beside it
        hdr_tbl = Table(
            [[logo_img, header_flowables]],
            colWidths=[20 * mm, FRAME_W - 20 * mm],
        )
        hdr_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(hdr_tbl)
    else:
        story.extend(header_flowables)
    story.append(Spacer(1, 2))
    story.append(HRFlowable(
        width='100%', thickness=1, color=CLR_RULE,
        spaceAfter=4, spaceBefore=2,
    ))
    story.append(Paragraph(
        'TEST REPORT FOR NON-AUTOMATIC WEIGHING INSTRUMENT', sty_title))
    story.append(Paragraph(
        f'As per OIML R 76-1:2006 &middot; {evaluation_type_label}',
        sty_subtitle,
    ))
    story.append(Spacer(1, 2))

    # Certificate / ULR / Date line
    cert_data = [
        [
            Paragraph(f'<b>Certificate No:</b> {report_number}', sty_cell),
            Paragraph(f'<b>ULR No:</b> {accreditation_number}', sty_cell_right),
        ],
        [
            Paragraph(
                f'<b>Certificate Issue Date:</b> {session_date_fmt}', sty_cell),
            Paragraph('', sty_cell_right),
        ],
    ]
    cert_tbl = Table(cert_data, colWidths=[FRAME_W * 0.5, FRAME_W * 0.5])
    cert_tbl.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(cert_tbl)
    story.append(Spacer(1, 8))

    # ===================================================================
    # Customer / Applicant details table
    # ===================================================================
    story.append(Paragraph('1. Customer / Applicant Details', sty_section))
    story.append(HRFlowable(
        width='100%', thickness=0.5, color=CLR_RULE,
        spaceAfter=4, spaceBefore=0,
    ))

    contact = ''
    if instrument:
        try:
            lab_obj = context.get('_laboratory')
        except Exception:
            lab_obj = None
    # Use lab contact_person if available from the original session
    contact_person = ''
    try:
        session_obj = context.get('_session')
        if session_obj and hasattr(session_obj, 'laboratory'):
            contact_person = session_obj.laboratory.contact_person or ''
    except Exception:
        pass
    if not contact_person:
        contact_person = 'As submitted'

    cust_rows = [
        [Paragraph('<b>Parameter</b>', sty_cell_bold),
         Paragraph('<b>Details</b>', sty_cell_bold)],
        [Paragraph('Customer / Applicant Name', sty_cell),
         Paragraph(contact_person, sty_cell)],
        [Paragraph('Address', sty_cell),
         Paragraph(lab_address, sty_cell)],
        [Paragraph('Date of Testing', sty_cell),
         Paragraph(session_date_fmt, sty_cell)],
    ]
    cust_tbl = Table(cust_rows, colWidths=[FRAME_W * 0.35, FRAME_W * 0.65])
    cust_tbl.setStyle(TableStyle(_base_table_style(len(cust_rows))))
    story.append(cust_tbl)
    story.append(Spacer(1, 8))

    # ===================================================================
    # Instrument details table
    # ===================================================================
    story.append(Paragraph('2. Instrument Under Test', sty_section))
    story.append(HRFlowable(
        width='100%', thickness=0.5, color=CLR_RULE,
        spaceAfter=4, spaceBefore=0,
    ))

    inst_rows = [
        [Paragraph('<b>Parameter</b>', sty_cell_bold),
         Paragraph('<b>Details</b>', sty_cell_bold)],
        [Paragraph('Manufacturer', sty_cell),
         Paragraph(_inst('manufacturer'), sty_cell)],
        [Paragraph('Model', sty_cell),
         Paragraph(_inst('model_name'), sty_cell)],
        [Paragraph('Serial Number', sty_cell),
         Paragraph(_inst('serial_number'), sty_cell)],
        [Paragraph('Accuracy Class', sty_cell),
         Paragraph(_accuracy_label(), sty_cell)],
        [Paragraph(f'Maximum Capacity (Max)', sty_cell),
         Paragraph(f'{_inst("max_capacity")} {unit_str}', sty_cell)],
        [Paragraph(f'Minimum Capacity (Min)', sty_cell),
         Paragraph(f'{_inst("min_capacity")} {unit_str}', sty_cell)],
        [Paragraph(f'Verification Scale Interval (e)', sty_cell),
         Paragraph(f'{_inst("verification_scale_interval_e")} {unit_str}',
                   sty_cell)],
        [Paragraph(f'Actual Scale Interval (d)', sty_cell),
         Paragraph(f'{_inst("actual_scale_interval_d")} {unit_str}',
                   sty_cell)],
        [Paragraph('Number of Scale Intervals (n)', sty_cell),
         Paragraph(_inst('num_scale_intervals_n'), sty_cell)],
        [Paragraph('Tare Device', sty_cell),
         Paragraph(_tare_label(), sty_cell)],
        [Paragraph(f'Maximum Additive Tare', sty_cell),
         Paragraph(f'{_inst("max_additive_tare")} {unit_str}', sty_cell)],
        [Paragraph(f'Maximum Safe Load', sty_cell),
         Paragraph(
             f'{_inst("max_safe_load")} {unit_str}'
             if instrument and instrument.max_safe_load else '—',
             sty_cell)],
        [Paragraph('Multi-Interval', sty_cell),
         Paragraph('Yes' if instrument and instrument.is_multi_interval
                   else 'No', sty_cell)],
    ]
    inst_tbl = Table(inst_rows, colWidths=[FRAME_W * 0.35, FRAME_W * 0.65])
    inst_tbl.setStyle(TableStyle(_base_table_style(len(inst_rows))))
    story.append(inst_tbl)
    story.append(Spacer(1, 8))

    # ===================================================================
    # Environmental conditions
    # ===================================================================
    story.append(Paragraph('3. Environmental Conditions', sty_section))
    story.append(HRFlowable(
        width='100%', thickness=0.5, color=CLR_RULE,
        spaceAfter=4, spaceBefore=0,
    ))

    temp_start_s = _format_decimal(temperature_start) if temperature_start else '—'
    temp_end_s = _format_decimal(temperature_end) if temperature_end else '—'
    humidity_s = _format_decimal(humidity) if humidity else '—'
    pressure_s = _format_decimal(barometric_pressure) if barometric_pressure else '—'

    env_rows = [
        [Paragraph('<b>Parameter</b>', sty_cell_bold),
         Paragraph('<b>Value</b>', sty_cell_bold)],
        [Paragraph('Temperature at Start', sty_cell),
         Paragraph(f'{temp_start_s} °C', sty_cell)],
        [Paragraph('Temperature at End', sty_cell),
         Paragraph(f'{temp_end_s} °C', sty_cell)],
        [Paragraph('Relative Humidity', sty_cell),
         Paragraph(f'{humidity_s} %', sty_cell)],
        [Paragraph('Barometric Pressure', sty_cell),
         Paragraph(f'{pressure_s} hPa', sty_cell)],
    ]
    env_tbl = Table(env_rows, colWidths=[FRAME_W * 0.35, FRAME_W * 0.65])
    env_tbl.setStyle(TableStyle(_base_table_style(len(env_rows))))
    story.append(env_tbl)
    story.append(Spacer(1, 8))

    # ===================================================================
    # Important remarks
    # ===================================================================
    story.append(Paragraph('4. Important Remarks', sty_section))
    story.append(HRFlowable(
        width='100%', thickness=0.5, color=CLR_RULE,
        spaceAfter=4, spaceBefore=0,
    ))

    from apps.reports.generators import DEFAULT_REMARKS
    remarks = context.get('remarks') or DEFAULT_REMARKS

    remark_data = []
    for idx, remark in enumerate(remarks, 1):
        remark_data.append([
            Paragraph(f'{idx}.', sty_remark),
            Paragraph(remark, sty_remark),
        ])

    remark_tbl = Table(remark_data,
                       colWidths=[FRAME_W * 0.05, FRAME_W * 0.95])
    remark_tbl.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, CLR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(remark_tbl)
    story.append(Spacer(1, 10))

    # Approval signature on page 1 (right-aligned)
    if approved_by_name:
        sig_data = [
            [Paragraph('', sty_cell),
             Paragraph(f'<b>Approved By:</b> {approved_by_name}',
                       sty_cell_right)],
        ]
        if approved_at:
            sig_data.append([
                Paragraph('', sty_cell),
                Paragraph(f'Date: {approved_at}', sty_cell_right),
            ])
        sig_tbl = Table(sig_data,
                        colWidths=[FRAME_W * 0.5, FRAME_W * 0.5])
        sig_tbl.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        story.append(sig_tbl)

    # Switch to Later page template for remaining pages
    story.append(NextPageTemplate('Later'))
    story.append(PageBreak())

    # ===================================================================
    # PAGE 2+ -- Test Results
    # ===================================================================
    section_num = 5

    for sec in test_sections:
        title = sec['title']
        test_type = sec['test_type']
        results = sec['results']

        section_flowables: list = []

        section_flowables.append(
            Paragraph(f'{section_num}. {title}', sty_section))
        section_flowables.append(HRFlowable(
            width='100%', thickness=0.5, color=CLR_RULE,
            spaceAfter=4, spaceBefore=0,
        ))

        if not results:
            section_flowables.append(
                Paragraph('Not Applicable', sty_italic_gray))
            section_flowables.append(Spacer(1, 8))
            story.extend(section_flowables)
            section_num += 1
            continue

        # Build table based on test type
        if test_type == TestType.WEIGHING_PERFORMANCE:
            _add_weighing_table(
                section_flowables, results, FRAME_W,
                sty_cell_center_bold, sty_cell_center, sty_cell,
                _base_table_style, _status_para, CLR_PASS, CLR_FAIL,
            )
        elif test_type == TestType.ECCENTRICITY:
            _add_eccentricity_table(
                section_flowables, results, FRAME_W,
                sty_cell_center_bold, sty_cell_center, sty_cell,
                _base_table_style, _status_para,
            )
        elif test_type == TestType.REPEATABILITY:
            _add_repeatability_table(
                section_flowables, results, FRAME_W,
                sty_cell_center_bold, sty_cell_center, sty_cell,
                _base_table_style, _status_para,
            )
        elif test_type == TestType.DISCRIMINATION:
            _add_discrimination_table(
                section_flowables, results, FRAME_W,
                sty_cell_center_bold, sty_cell_center, sty_cell,
                _base_table_style, _status_para,
            )
        else:
            _add_generic_table(
                section_flowables, results, FRAME_W,
                sty_cell_center_bold, sty_cell_center, sty_cell,
                _base_table_style, _status_para,
            )

        section_flowables.append(Spacer(1, 10))

        # Use KeepTogether only for small tables; otherwise just append
        if len(results) <= 6:
            story.append(KeepTogether(section_flowables))
        else:
            story.extend(section_flowables)

        section_num += 1

    # ===================================================================
    # Measurement Uncertainty Budget
    # ===================================================================
    budget = context.get('uncertainty_budget')
    if budget:
        budget_flowables: list = []
        budget_flowables.append(Paragraph(
            f'{section_num}. Measurement Uncertainty', sty_section))
        budget_flowables.append(HRFlowable(
            width='100%', thickness=0.5, color=CLR_RULE,
            spaceAfter=4, spaceBefore=0,
        ))
        budget_flowables.append(Paragraph(
            f'Uncertainty budget evaluated at the highest tested load '
            f'({_format_decimal(budget["load"])} {budget["unit"]}), '
            f'in accordance with EURAMET cg-18 principles:',
            sty_cell,
        ))
        budget_flowables.append(Spacer(1, 4))

        budget_rows = [[
            Paragraph('<b>Uncertainty Component</b>', sty_cell_center_bold),
            Paragraph(f'<b>Standard Uncertainty ({budget["unit"]})</b>',
                      sty_cell_center_bold),
        ]]
        for name, value in budget['components']:
            budget_rows.append([
                Paragraph(name, sty_cell),
                Paragraph(f'{value:.6f}', sty_cell_center),
            ])
        budget_rows.append([
            Paragraph('<b>Combined standard uncertainty u<sub>c</sub></b>', sty_cell),
            Paragraph(f'<b>{budget["u_combined"]:.6f}</b>', sty_cell_center),
        ])
        budget_rows.append([
            Paragraph(f'<b>Expanded uncertainty U (k={budget["k"]}, ~95%)</b>',
                      sty_cell),
            Paragraph(f'<b>&plusmn;{budget["expanded"]:.6f}</b>', sty_cell_center),
        ])
        budget_tbl = Table(
            budget_rows, colWidths=[FRAME_W * 0.62, FRAME_W * 0.38])
        budget_tbl.setStyle(TableStyle(_base_table_style(len(budget_rows))))
        budget_flowables.append(budget_tbl)
        budget_flowables.append(Spacer(1, 10))
        story.append(KeepTogether(budget_flowables))
        section_num += 1

    # ===================================================================
    # LAST PAGE -- Conclusion + Signatures
    # ===================================================================
    story.append(PageBreak())

    # Overall test summary table
    story.append(
        Paragraph(f'{section_num}. Overall Test Summary', sty_section))
    story.append(HRFlowable(
        width='100%', thickness=0.5, color=CLR_RULE,
        spaceAfter=4, spaceBefore=0,
    ))

    summary_header = [
        Paragraph('<b>Sr No</b>', sty_cell_center_bold),
        Paragraph('<b>Test Performed</b>', sty_cell_center_bold),
        Paragraph('<b>Result</b>', sty_cell_center_bold),
    ]
    summary_rows = [summary_header]
    for idx, item in enumerate(compliance_summary, 1):
        summary_rows.append([
            Paragraph(str(idx), sty_cell_center),
            Paragraph(item['test_name'], sty_cell),
            _status_para(item['status'], item['status_label']),
        ])

    col_w_summary = [FRAME_W * 0.10, FRAME_W * 0.60, FRAME_W * 0.30]
    summary_tbl = Table(summary_rows, colWidths=col_w_summary)
    summary_tbl.setStyle(TableStyle(
        _base_table_style(len(summary_rows))))
    story.append(summary_tbl)
    story.append(Spacer(1, 12))

    # Conclusion
    section_num += 1
    story.append(
        Paragraph(f'{section_num}. Conclusion', sty_section))
    story.append(HRFlowable(
        width='100%', thickness=0.5, color=CLR_RULE,
        spaceAfter=4, spaceBefore=0,
    ))

    if overall_verdict == ComplianceStatus.PASS:
        verdict_text = (
            f'Based on the tests performed in accordance with OIML R 76-1:2006, '
            f'the non-automatic weighing instrument described above '
            f'<b><font color="#{CLR_PASS.hexval()[2:]}">CONFORMS</font></b> '
            f'to the requirements for {evaluation_type_label} '
            f'({verification_type_label} Verification).'
        )
    else:
        verdict_text = (
            f'Based on the tests performed in accordance with OIML R 76-1:2006, '
            f'the non-automatic weighing instrument described above '
            f'<b><font color="#{CLR_FAIL.hexval()[2:]}">DOES NOT CONFORM</font></b> '
            f'to the requirements for {evaluation_type_label} '
            f'({verification_type_label} Verification). '
            f'Please refer to the individual test results above for details.'
        )
    story.append(Paragraph(verdict_text, sty_conclusion))
    story.append(Spacer(1, 20))

    # Three-column signature block
    sig_block = [
        [
            Paragraph('', sty_cell_center),
            Paragraph('', sty_cell_center),
            Paragraph('', sty_cell_center),
        ],
        [
            Paragraph('_' * 22, sty_cell_center),
            Paragraph('_' * 22, sty_cell_center),
            Paragraph('_' * 22, sty_cell_center),
        ],
        [
            Paragraph(f'<b>Tested By</b>', sty_cell_center_bold),
            Paragraph(f'<b>Checked By</b>', sty_cell_center_bold),
            Paragraph(f'<b>Approved By</b>', sty_cell_center_bold),
        ],
        [
            Paragraph(engineer_name or '—', sty_cell_center),
            Paragraph(checked_by_name or '—', sty_cell_center),
            Paragraph(approved_by_name or '—', sty_cell_center),
        ],
    ]
    sig_col_w = FRAME_W / 3
    sig_tbl = Table(sig_block,
                    colWidths=[sig_col_w, sig_col_w, sig_col_w])
    sig_tbl.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
    ]))
    story.append(sig_tbl)

    # QR code for public certificate verification
    verify_url = context.get('verify_url')
    if verify_url:
        qr_flowable = _build_qr_block(verify_url, sty_cell_center)
        if qr_flowable is not None:
            story.append(Spacer(1, 18))
            story.append(qr_flowable)

    # -------------------------------------------------------------------
    # Build
    # -------------------------------------------------------------------
    doc.build(story)


def _load_logo_image(logo_data_uri: str):
    """Decode a data: URI into a ReportLab Image capped at ~16mm square.

    Returns None on any failure so the certificate renders without a logo.
    """
    try:
        import base64
        import io

        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
        from reportlab.platypus import Image

        b64 = logo_data_uri.split(',', 1)[1]
        buf = io.BytesIO(base64.b64decode(b64))
        reader = ImageReader(buf)
        w, h = reader.getSize()
        max_side = 16 * mm
        scale = min(max_side / w, max_side / h)
        buf.seek(0)
        return Image(buf, width=w * scale, height=h * scale)
    except Exception:
        logger.exception("Logo decoding failed; certificate continues without it")
        return None


def _build_qr_block(verify_url: str, caption_style):
    """Centered QR code linking to the public verification page.

    Returns None if the qrcode library is unavailable so certificate
    generation never fails because of the QR.
    """
    try:
        import io

        import qrcode
        from reportlab.lib.units import mm
        from reportlab.platypus import Image, Paragraph, Table, TableStyle

        qr = qrcode.QRCode(border=1, box_size=6)
        qr.add_data(verify_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        qr_img = Image(buf, width=22 * mm, height=22 * mm)
        caption = Paragraph(
            'Scan to verify the authenticity of this certificate<br/>'
            f'<font size="6" color="#666666">{verify_url}</font>',
            caption_style,
        )
        tbl = Table([[qr_img], [caption]], colWidths=[None])
        tbl.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        return tbl
    except Exception:
        logger.exception("QR code generation failed; certificate continues without it")
        return None


# ===================================================================
# Table builder functions for each test type
# ===================================================================

def _add_weighing_table(
    flowables: list,
    results: list,
    frame_w: float,
    sty_hdr,
    sty_center,
    sty_cell,
    base_style_fn,
    status_para_fn,
    clr_pass,
    clr_fail,
) -> None:
    """Weighing Performance: Sr No, Test Point, Mass Values, Indicated Value,
    Error, MPE, Result."""
    from reportlab.platypus import Paragraph, Table, TableStyle

    header = [
        Paragraph('<b>Sr No</b>', sty_hdr),
        Paragraph('<b>Test Point</b>', sty_hdr),
        Paragraph('<b>Ref. Mass Value</b>', sty_hdr),
        Paragraph('<b>Indicated Value</b>', sty_hdr),
        Paragraph('<b>Error</b>', sty_hdr),
        Paragraph(u'<b>MPE (±)</b>', sty_hdr),
        Paragraph(u'<b>U (±) k=2</b>', sty_hdr),
        Paragraph('<b>Result</b>', sty_hdr),
    ]
    rows = [header]
    for idx, r in enumerate(results, 1):
        obs = r.observation
        indicated = _format_decimal(obs.indicated_value) if obs else '—'
        ref_val = _format_decimal(obs.reference_value) if obs else \
            _format_decimal(r.test_point_load)
        uncertainty = getattr(r, 'expanded_uncertainty', None)
        rows.append([
            Paragraph(str(idx), sty_center),
            Paragraph(_format_decimal(r.test_point_load), sty_center),
            Paragraph(ref_val, sty_center),
            Paragraph(indicated, sty_center),
            Paragraph(_format_decimal(r.computed_error), sty_center),
            Paragraph(
                f'±{_format_decimal(r.mpe_applicable)}'
                if r.mpe_applicable else '—',
                sty_center),
            Paragraph(
                f'±{_format_decimal(uncertainty)}' if uncertainty else '—',
                sty_center),
            status_para_fn(r.compliance_status),
        ])

    col_widths = [
        frame_w * 0.06,
        frame_w * 0.13,
        frame_w * 0.14,
        frame_w * 0.14,
        frame_w * 0.13,
        frame_w * 0.13,
        frame_w * 0.13,
        frame_w * 0.14,
    ]
    tbl = Table(rows, colWidths=col_widths)
    tbl.setStyle(TableStyle(base_style_fn(len(rows))))
    flowables.append(tbl)


def _add_eccentricity_table(
    flowables: list,
    results: list,
    frame_w: float,
    sty_hdr,
    sty_center,
    sty_cell,
    base_style_fn,
    status_para_fn,
) -> None:
    """Eccentricity: Position-based layout with position labels."""
    from reportlab.platypus import Paragraph, Table, TableStyle

    header = [
        Paragraph('<b>Sr No</b>', sty_hdr),
        Paragraph('<b>Position</b>', sty_hdr),
        Paragraph('<b>Test Load</b>', sty_hdr),
        Paragraph('<b>Indicated Value</b>', sty_hdr),
        Paragraph('<b>Error</b>', sty_hdr),
        Paragraph(u'<b>MPE (±)</b>', sty_hdr),
        Paragraph('<b>Result</b>', sty_hdr),
    ]

    position_labels = {
        'center': 'Centre',
        'front_left': 'Front Left (FL)',
        'front_right': 'Front Right (FR)',
        'rear_left': 'Rear Left (RL)',
        'rear_right': 'Rear Right (RR)',
    }

    rows = [header]
    for idx, r in enumerate(results, 1):
        obs = r.observation
        pos_raw = r.position or (obs.position if obs else '')
        pos_label = position_labels.get(pos_raw,
                                        pos_raw.replace('_', ' ').title())
        indicated = _format_decimal(obs.indicated_value) if obs else '—'
        rows.append([
            Paragraph(str(idx), sty_center),
            Paragraph(pos_label, sty_cell),
            Paragraph(_format_decimal(r.test_point_load), sty_center),
            Paragraph(indicated, sty_center),
            Paragraph(_format_decimal(r.computed_error), sty_center),
            Paragraph(
                f'±{_format_decimal(r.mpe_applicable)}'
                if r.mpe_applicable else '—',
                sty_center),
            status_para_fn(r.compliance_status),
        ])

    col_widths = [
        frame_w * 0.07,
        frame_w * 0.18,
        frame_w * 0.14,
        frame_w * 0.16,
        frame_w * 0.14,
        frame_w * 0.14,
        frame_w * 0.17,
    ]
    tbl = Table(rows, colWidths=col_widths)
    tbl.setStyle(TableStyle(base_style_fn(len(rows))))
    flowables.append(tbl)

    # Max difference from centre note
    centre_results = [r for r in results
                      if (r.position or '') == 'center']
    corner_results = [r for r in results
                      if (r.position or '') != 'center' and r.position]
    if centre_results and corner_results:
        centre_error = centre_results[0].computed_error or Decimal(0)
        max_diff = max(
            abs((r.computed_error or Decimal(0)) - centre_error)
            for r in corner_results
        )
        flowables.append(Paragraph(
            f'Maximum difference from centre load: '
            f'{_format_decimal(max_diff)}',
            sty_cell,
        ))


def _add_repeatability_table(
    flowables: list,
    results: list,
    frame_w: float,
    sty_hdr,
    sty_center,
    sty_cell,
    base_style_fn,
    status_para_fn,
) -> None:
    """Repeatability: Trial-based layout with range calculation."""
    from reportlab.platypus import Paragraph, Table, TableStyle
    from collections import OrderedDict

    # Group by test_point_load
    by_load: dict[str, list] = OrderedDict()
    for r in results:
        key = _format_decimal(r.test_point_load)
        by_load.setdefault(key, []).append(r)

    for load_str, load_results in by_load.items():
        flowables.append(Paragraph(
            f'Test Load: {load_str}', sty_cell))

        header = [
            Paragraph('<b>Trial</b>', sty_hdr),
            Paragraph('<b>Indicated Value</b>', sty_hdr),
            Paragraph('<b>Error</b>', sty_hdr),
            Paragraph(u'<b>MPE (±)</b>', sty_hdr),
            Paragraph('<b>Result</b>', sty_hdr),
        ]

        rows = [header]
        indicated_values = []
        for r in load_results:
            obs = r.observation
            ind_val = obs.indicated_value if obs else None
            if ind_val is not None:
                indicated_values.append(ind_val)
            rows.append([
                Paragraph(str(r.trial_number), sty_center),
                Paragraph(
                    _format_decimal(ind_val) if ind_val is not None
                    else '—', sty_center),
                Paragraph(_format_decimal(r.computed_error), sty_center),
                Paragraph(
                    f'±{_format_decimal(r.mpe_applicable)}'
                    if r.mpe_applicable else '—',
                    sty_center),
                status_para_fn(r.compliance_status),
            ])

        # Range row
        if indicated_values:
            range_val = max(indicated_values) - min(indicated_values)
            rows.append([
                Paragraph('<b>Range</b>', sty_center),
                Paragraph(f'<b>{_format_decimal(range_val)}</b>', sty_center),
                Paragraph('', sty_center),
                Paragraph('', sty_center),
                Paragraph('', sty_center),
            ])

        col_widths = [
            frame_w * 0.10,
            frame_w * 0.22,
            frame_w * 0.22,
            frame_w * 0.22,
            frame_w * 0.24,
        ]
        tbl = Table(rows, colWidths=col_widths)
        style_cmds = base_style_fn(len(rows))
        tbl.setStyle(TableStyle(style_cmds))
        flowables.append(tbl)
        flowables.append(Paragraph('', sty_cell))  # small gap


def _add_discrimination_table(
    flowables: list,
    results: list,
    frame_w: float,
    sty_hdr,
    sty_center,
    sty_cell,
    base_style_fn,
    status_para_fn,
) -> None:
    """Discrimination: Test Load, Indication before, Indication after adding
    1.4d, Change, Result."""
    from reportlab.platypus import Paragraph, Table, TableStyle

    header = [
        Paragraph('<b>Sr No</b>', sty_hdr),
        Paragraph('<b>Test Load</b>', sty_hdr),
        Paragraph('<b>Indication Before</b>', sty_hdr),
        Paragraph('<b>Indication After (+1.4d)</b>', sty_hdr),
        Paragraph('<b>Change</b>', sty_hdr),
        Paragraph('<b>Result</b>', sty_hdr),
    ]

    rows = [header]
    for idx, r in enumerate(results, 1):
        obs = r.observation
        indicated_before = '—'
        indicated_after = '—'
        change = '—'

        if obs:
            indicated_before = _format_decimal(obs.reference_value)
            indicated_after = _format_decimal(obs.indicated_value)
            if obs.reference_value is not None and obs.indicated_value is not None:
                change = _format_decimal(
                    obs.indicated_value - obs.reference_value)

        rows.append([
            Paragraph(str(idx), sty_center),
            Paragraph(_format_decimal(r.test_point_load), sty_center),
            Paragraph(indicated_before, sty_center),
            Paragraph(indicated_after, sty_center),
            Paragraph(change, sty_center),
            status_para_fn(r.compliance_status),
        ])

    col_widths = [
        frame_w * 0.07,
        frame_w * 0.16,
        frame_w * 0.20,
        frame_w * 0.22,
        frame_w * 0.15,
        frame_w * 0.20,
    ]
    tbl = Table(rows, colWidths=col_widths)
    tbl.setStyle(TableStyle(base_style_fn(len(rows))))
    flowables.append(tbl)


def _add_generic_table(
    flowables: list,
    results: list,
    frame_w: float,
    sty_hdr,
    sty_center,
    sty_cell,
    base_style_fn,
    status_para_fn,
) -> None:
    """Generic table for any test type not covered by a specific builder."""
    from reportlab.platypus import Paragraph, Table, TableStyle

    header = [
        Paragraph('<b>Sr No</b>', sty_hdr),
        Paragraph('<b>Test Load</b>', sty_hdr),
        Paragraph('<b>Indicated Value</b>', sty_hdr),
        Paragraph('<b>Error</b>', sty_hdr),
        Paragraph(u'<b>MPE (±)</b>', sty_hdr),
        Paragraph('<b>Result</b>', sty_hdr),
    ]

    rows = [header]
    for idx, r in enumerate(results, 1):
        obs = r.observation
        indicated = _format_decimal(obs.indicated_value) if obs else '—'
        rows.append([
            Paragraph(str(idx), sty_center),
            Paragraph(_format_decimal(r.test_point_load), sty_center),
            Paragraph(indicated, sty_center),
            Paragraph(_format_decimal(r.computed_error), sty_center),
            Paragraph(
                f'±{_format_decimal(r.mpe_applicable)}'
                if r.mpe_applicable else '—',
                sty_center),
            status_para_fn(r.compliance_status),
        ])

    col_widths = [
        frame_w * 0.07,
        frame_w * 0.18,
        frame_w * 0.20,
        frame_w * 0.18,
        frame_w * 0.17,
        frame_w * 0.20,
    ]
    tbl = Table(rows, colWidths=col_widths)
    tbl.setStyle(TableStyle(base_style_fn(len(rows))))
    flowables.append(tbl)
