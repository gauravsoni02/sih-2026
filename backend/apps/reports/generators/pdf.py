import logging
from decimal import Decimal
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as _xml_escape

from django.conf import settings

from apps.engine.constants import ComplianceStatus, TestType
from apps.reports.generators import _build_report_context, build_uncertainty_budget

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Palette -- mirrors the certificate preview in
# frontend/src/pages/reports/ReportDetail.tsx (the visual source of truth)
# ---------------------------------------------------------------------------
COLOR_TEXT = '#1a1a1a'         # body text and strong rules
COLOR_MUTED = '#333333'        # secondary text (labels, addresses)
COLOR_FAINT = '#666666'        # footer / signature designations
COLOR_NA = '#888888'           # "N/A" grey
COLOR_BORDER = '#999999'       # all table borders
COLOR_SECTION_BG = '#E8E8E8'   # section title bars + table header rows
COLOR_KV_LABEL_BG = '#F0F0F0'  # key-value label cells
COLOR_ALT_ROW = '#FAFAFA'      # alternating table rows
COLOR_PASS = '#006400'         # Pass / CONFORMS
COLOR_FAIL = '#8B0000'         # Fail / DOES NOT CONFORM
COLOR_PASS_BG = '#f0fff0'      # verdict box tint (pass)
COLOR_FAIL_BG = '#fff5f5'      # verdict box tint (fail)

# Typography -- the preview renders in Times New Roman with Courier numerics
FONT_SERIF = 'Times-Roman'
FONT_SERIF_BOLD = 'Times-Bold'
FONT_SERIF_ITALIC = 'Times-Italic'
FONT_MONO = 'Courier'


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


def _esc(val) -> str:
    """XML-escape a value for safe interpolation into Paragraph markup."""
    if val is None:
        return ''
    return _xml_escape(str(val))


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
# ReportLab PDF implementation -- styled to match the in-browser
# certificate preview (ReportDetail.tsx) as closely as possible
# ===================================================================

def _generate_pdf_reportlab(*, context: dict[str, Any], filepath: str) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
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
    MARGIN_LEFT = 16 * mm
    MARGIN_RIGHT = 16 * mm
    MARGIN_TOP = 21 * mm
    MARGIN_BOTTOM = 16 * mm

    FRAME_W = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT

    # -------------------------------------------------------------------
    # Colours (from the module-level preview palette)
    # -------------------------------------------------------------------
    CLR_TEXT = colors.HexColor(COLOR_TEXT)
    CLR_MUTED = colors.HexColor(COLOR_MUTED)
    CLR_FAINT = colors.HexColor(COLOR_FAINT)
    CLR_NA = colors.HexColor(COLOR_NA)
    CLR_BORDER = colors.HexColor(COLOR_BORDER)
    CLR_SECTION_BG = colors.HexColor(COLOR_SECTION_BG)
    CLR_KV_LABEL_BG = colors.HexColor(COLOR_KV_LABEL_BG)
    CLR_ALT_ROW = colors.HexColor(COLOR_ALT_ROW)
    CLR_PASS = colors.HexColor(COLOR_PASS)
    CLR_FAIL = colors.HexColor(COLOR_FAIL)
    CLR_PASS_BG = colors.HexColor(COLOR_PASS_BG)
    CLR_FAIL_BG = colors.HexColor(COLOR_FAIL_BG)
    CLR_WHITE = colors.white

    # -------------------------------------------------------------------
    # Paragraph styles (px sizes in the preview map 1:1 to points)
    # -------------------------------------------------------------------
    base_styles = getSampleStyleSheet()

    def _ps(name, **kw):
        defaults = dict(parent=base_styles['Normal'], fontName=FONT_SERIF,
                        textColor=CLR_TEXT)
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    # Government letterhead block (all centred, as in the preview)
    sty_govt_main = _ps('GovtMain', fontName=FONT_SERIF_BOLD, fontSize=14,
                        leading=17, alignment=TA_CENTER)
    sty_govt_sub = _ps('GovtSub', fontName=FONT_SERIF_BOLD, fontSize=11,
                       leading=14, alignment=TA_CENTER, spaceBefore=2)
    sty_govt_dept = _ps('GovtDept', fontName=FONT_SERIF_BOLD, fontSize=10,
                        leading=13, alignment=TA_CENTER, spaceBefore=1)
    sty_lab_title = _ps('LabTitle', fontName=FONT_SERIF_BOLD, fontSize=15,
                        leading=18, alignment=TA_CENTER, spaceBefore=10)
    sty_lab_addr = _ps('LabAddr', fontSize=10, leading=13,
                       alignment=TA_CENTER, textColor=CLR_MUTED, spaceBefore=3)
    sty_cert_title = _ps('CertTitle', fontName=FONT_SERIF_BOLD, fontSize=12,
                         leading=15, alignment=TA_CENTER, spaceBefore=4)
    sty_subtitle = _ps('CertSubtitle', fontSize=10, leading=13,
                       alignment=TA_CENTER, textColor=CLR_MUTED, spaceBefore=4)

    # Certificate info row (borderless, label muted / value bold)
    sty_ci_label = _ps('CiLabel', fontName=FONT_SERIF_BOLD, fontSize=10,
                       leading=13, textColor=CLR_MUTED)
    sty_ci_value = _ps('CiValue', fontName=FONT_SERIF_BOLD, fontSize=10,
                       leading=13)
    sty_ci_label_r = _ps('CiLabelR', fontName=FONT_SERIF_BOLD, fontSize=10,
                         leading=13, textColor=CLR_MUTED, alignment=TA_RIGHT)
    sty_ci_value_r = _ps('CiValueR', fontName=FONT_SERIF_BOLD, fontSize=10,
                         leading=13, alignment=TA_RIGHT)

    # Section bar / subsection heading
    sty_section_bar = _ps('SectionBar', fontName=FONT_SERIF_BOLD, fontSize=11,
                          leading=14)
    sty_subhead = _ps('SubHead', fontName=FONT_SERIF_BOLD, fontSize=10,
                      leading=13, spaceBefore=6)

    # Table cells
    sty_cell = _ps('Cell', fontSize=9, leading=11.5)
    sty_cell_c = _ps('CellC', fontSize=9, leading=11.5, alignment=TA_CENTER)
    sty_cell_b = _ps('CellB', fontName=FONT_SERIF_BOLD, fontSize=9,
                     leading=11.5)
    sty_num = _ps('CellNum', fontName=FONT_MONO, fontSize=9, leading=11.5,
                  alignment=TA_RIGHT)
    sty_hdr_l = _ps('HdrL', fontName=FONT_SERIF_BOLD, fontSize=9, leading=11.5)
    sty_hdr_c = _ps('HdrC', fontName=FONT_SERIF_BOLD, fontSize=9,
                    leading=11.5, alignment=TA_CENTER)
    sty_hdr_r = _ps('HdrR', fontName=FONT_SERIF_BOLD, fontSize=9,
                    leading=11.5, alignment=TA_RIGHT)

    # Key-value grid cells (label grey / value mono, as in the preview)
    sty_kv_label = _ps('KvLabel', fontName=FONT_SERIF_BOLD, fontSize=9.5,
                       leading=12, textColor=CLR_MUTED)
    sty_kv_value = _ps('KvValue', fontName=FONT_MONO, fontSize=9.5, leading=12)

    # Misc body styles
    sty_na = _ps('NaText', fontName=FONT_SERIF_ITALIC, fontSize=9,
                 leading=12, textColor=CLR_NA)
    sty_remark = _ps('Remark', fontSize=9, leading=13.5)
    sty_conclusion = _ps('Conclusion', fontSize=10, leading=15,
                         alignment=TA_JUSTIFY, spaceBefore=4, spaceAfter=4)
    sty_verdict_pass = _ps('VerdictPass', fontName=FONT_SERIF_BOLD,
                           fontSize=14, leading=18, alignment=TA_CENTER,
                           textColor=CLR_PASS)
    sty_verdict_fail = _ps('VerdictFail', fontName=FONT_SERIF_BOLD,
                           fontSize=14, leading=18, alignment=TA_CENTER,
                           textColor=CLR_FAIL)
    sty_normal_center = _ps('BodyCenter', fontSize=9, leading=12,
                            alignment=TA_CENTER)

    # Signature block styles
    sty_sig_role = _ps('SigRole', fontName=FONT_SERIF_BOLD, fontSize=10,
                       leading=13, alignment=TA_CENTER)
    sty_sig_name = _ps('SigName', fontSize=9, leading=12,
                       alignment=TA_CENTER, spaceBefore=2)
    sty_sig_meta = _ps('SigMeta', fontSize=8, leading=10,
                       alignment=TA_CENTER, textColor=CLR_FAINT, spaceBefore=1)

    # -------------------------------------------------------------------
    # Shared table styling (preview: 1px #999 borders, #E8E8E8 header,
    # #FAFAFA alternating rows, 3-4px vertical / 6px horizontal padding)
    # -------------------------------------------------------------------
    BORDER_W = 0.75
    CELL_PAD_V = 4
    CELL_PAD_H = 6

    def _base_table_style(n_rows: int, has_header: bool = True) -> list:
        """TableStyle commands common to all bordered data tables."""
        cmds: list = [
            ('GRID', (0, 0), (-1, -1), BORDER_W, CLR_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), CELL_PAD_V),
            ('BOTTOMPADDING', (0, 0), (-1, -1), CELL_PAD_V),
            ('LEFTPADDING', (0, 0), (-1, -1), CELL_PAD_H),
            ('RIGHTPADDING', (0, 0), (-1, -1), CELL_PAD_H),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        if has_header:
            cmds.append(('BACKGROUND', (0, 0), (-1, 0), CLR_SECTION_BG))
        # alternating rows (skip header)
        start = 1 if has_header else 0
        for i in range(start, n_rows):
            if (i - start) % 2 == 1:
                cmds.append(('BACKGROUND', (0, i), (-1, i), CLR_ALT_ROW))
        return cmds

    def _kv_table_style(label_cols: tuple[int, ...] = (0, 2)) -> list:
        """Key-value grid: grey label cells, bordered, no header row."""
        cmds: list = [
            ('GRID', (0, 0), (-1, -1), BORDER_W, CLR_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), CELL_PAD_V),
            ('BOTTOMPADDING', (0, 0), (-1, -1), CELL_PAD_V),
            ('LEFTPADDING', (0, 0), (-1, -1), CELL_PAD_H),
            ('RIGHTPADDING', (0, 0), (-1, -1), CELL_PAD_H),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        for c in label_cols:
            cmds.append(('BACKGROUND', (c, 0), (c, -1), CLR_KV_LABEL_BG))
        return cmds

    def _section_bar(text: str) -> list:
        """Grey, bordered, uppercase section title bar (preview style)."""
        bar = Table(
            [[Paragraph(text.upper(), sty_section_bar)]],
            colWidths=[FRAME_W],
        )
        bar.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), CLR_SECTION_BG),
            ('BOX', (0, 0), (-1, -1), BORDER_W, CLR_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        return [Spacer(1, 10), bar, Spacer(1, 5)]

    def _subhead(text: str) -> list:
        """Numbered test subsection heading with an underline rule."""
        return [
            Paragraph(text, sty_subhead),
            HRFlowable(width='100%', thickness=0.5, color=CLR_BORDER,
                       spaceBefore=2, spaceAfter=4),
        ]

    # -------------------------------------------------------------------
    # Status-coloured paragraph (preview: bold green / bold dark red /
    # italic grey)
    # -------------------------------------------------------------------
    def _status_para(status: str, label: str | None = None) -> Paragraph:
        text = label or _status_label(status)
        if status == ComplianceStatus.PASS:
            return Paragraph(
                f'<b><font color="{COLOR_PASS}">{text}</font></b>',
                sty_cell_c,
            )
        if status == ComplianceStatus.FAIL:
            return Paragraph(
                f'<b><font color="{COLOR_FAIL}">{text}</font></b>',
                sty_cell_c,
            )
        return Paragraph(
            f'<i><font color="{COLOR_NA}">{text}</font></i>',
            sty_cell_c,
        )

    # Styles bundle handed to the per-test-type table builders
    S = {
        'hdr_l': sty_hdr_l,
        'hdr_c': sty_hdr_c,
        'hdr_r': sty_hdr_r,
        'cell': sty_cell,
        'cell_c': sty_cell_c,
        'cell_b': sty_cell_b,
        'num': sty_num,
    }

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
    checked_at = context.get('checked_at', '')
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
    doc_issue_date = context.get('doc_issue_date', '01.01.2026')
    logo_data_uri = context.get('logo_data_uri', '')
    report_version = context.get('version', 1)
    customer_name = context.get('customer_name', '')
    customer_address = context.get('customer_address', '')
    customer_contact = context.get('customer_contact', '')
    request_date = context.get('request_date', '')

    def _fmt_date(raw) -> str:
        """Render an ISO date (str or date) as '01 Jan 2026'."""
        try:
            from datetime import date as _date, datetime as _dt
            if isinstance(raw, str) and raw:
                return _dt.strptime(raw, '%Y-%m-%d').date().strftime('%d %b %Y')
            if isinstance(raw, _date):
                return raw.strftime('%d %b %Y')
        except Exception:
            pass
        return str(raw)

    session_date_fmt = _fmt_date(session_date)
    issue_date_fmt = _fmt_date(
        context.get('certificate_issue_date') or session_date)
    request_date_fmt = _fmt_date(request_date) if request_date else '—'
    checked_at_fmt = _fmt_date(checked_at) if checked_at else ''
    approved_at_fmt = _fmt_date(approved_at) if approved_at else ''

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
    # Page-level callbacks (repeating header / document-control footer)
    # -------------------------------------------------------------------
    logo = _load_logo_reader(logo_data_uri) if logo_data_uri else None

    repeat_line = (
        f'LEGAL METROLOGY LABORATORY — {lab_name}   ·   '
        f'Certificate No: {report_number}   ·   Date: {session_date_fmt}'
    )

    def _draw_header_footer(canvas, doc):
        canvas.saveState()
        # -- repeating header (the centred 'Page X of Y' is drawn by
        #    _NumberedCanvas once the total page count is known) --
        y_top = PAGE_H - 12 * mm
        canvas.setFont(FONT_SERIF, 8)
        canvas.setFillColor(CLR_TEXT)
        canvas.drawString(MARGIN_LEFT, y_top,
                          f'Certificate No: {report_number}')
        canvas.drawRightString(PAGE_W - MARGIN_RIGHT, y_top,
                               f'ULR No: {accreditation_number}')
        if canvas.getPageNumber() > 1:
            # continuation pages repeat the laboratory identity, as the
            # preview does at the top of its results / summary pages
            canvas.setFont(FONT_SERIF, 7.5)
            canvas.setFillColor(CLR_MUTED)
            canvas.drawCentredString(PAGE_W / 2, y_top - 11, repeat_line)
            rule_y = y_top - 15
        else:
            rule_y = y_top - 4
        canvas.setStrokeColor(CLR_TEXT)
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN_LEFT, rule_y, PAGE_W - MARGIN_RIGHT, rule_y)

        # -- first-page logo, top-left of the letterhead (as in preview) --
        if logo is not None and canvas.getPageNumber() == 1:
            reader, w, h = logo
            try:
                canvas.drawImage(
                    reader, MARGIN_LEFT, PAGE_H - MARGIN_TOP - h,
                    width=w, height=h, mask='auto',
                    preserveAspectRatio=True,
                )
            except Exception:
                pass

        # -- repeating document-control footer (preview footer strip) --
        y_bot = MARGIN_BOTTOM - 4 * mm
        canvas.setStrokeColor(CLR_TEXT)
        canvas.setLineWidth(0.75)
        canvas.line(MARGIN_LEFT, y_bot + 9, PAGE_W - MARGIN_RIGHT, y_bot + 9)
        canvas.setFont(FONT_SERIF, 7)
        canvas.setFillColor(CLR_FAINT)
        canvas.drawString(MARGIN_LEFT, y_bot, f'Doc No: {doc_control_number}')
        canvas.drawCentredString(
            PAGE_W / 2, y_bot,
            f'Issue No: {doc_issue_number}   ·   '
            f'Issue Date: {doc_issue_date}   ·   '
            f'Rev No: {doc_rev_number}',
        )
        canvas.drawRightString(
            PAGE_W - MARGIN_RIGHT, y_bot,
            f'76 Labs Test Report Generator · Software v{software_version}',
        )
        canvas.restoreState()

    def _draw_first_page(canvas, doc):
        _draw_header_footer(canvas, doc)

    def _draw_later_page(canvas, doc):
        _draw_header_footer(canvas, doc)

    # -------------------------------------------------------------------
    # Canvas with deferred page numbering: pages are buffered in showPage
    # and stamped 'Page i of N' once the total is known at save time.
    # -------------------------------------------------------------------
    from reportlab.pdfgen.canvas import Canvas as _RLCanvas

    class _NumberedCanvas(_RLCanvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states: list[dict] = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.saveState()
                self.setFont(FONT_SERIF, 8)
                self.setFillColor(CLR_TEXT)
                self.drawCentredString(
                    PAGE_W / 2, PAGE_H - 12 * mm,
                    f'Page {self._pageNumber} of {total}',
                )
                self.restoreState()
                super().showPage()
            super().save()

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
    # PAGE 1 -- Government letterhead (centred, logo drawn top-left on
    # the canvas so the text block stays exactly centred like the preview)
    # ===================================================================
    story.append(Paragraph('GOVERNMENT OF INDIA', sty_govt_main))
    story.append(Paragraph(_esc(jurisdiction).upper(), sty_govt_sub))
    story.append(Paragraph('DEPARTMENT OF CONSUMER AFFAIRS', sty_govt_dept))
    story.append(Paragraph('LEGAL METROLOGY LABORATORY', sty_lab_title))
    lab_line = _esc(lab_name) + (f', {_esc(lab_address)}' if lab_address else '')
    story.append(Paragraph(lab_line, sty_lab_addr))
    story.append(HRFlowable(
        width='100%', thickness=2, color=CLR_TEXT,
        spaceBefore=8, spaceAfter=4,
    ))
    story.append(Paragraph(
        'TEST REPORT FOR NON-AUTOMATIC WEIGHING INSTRUMENT', sty_cert_title))
    story.append(Paragraph(
        f'As per OIML R 76-1:2006 &middot; {_esc(evaluation_type_label)}',
        sty_subtitle,
    ))
    story.append(Spacer(1, 8))

    # Certificate info rows (label muted / value bold, right column
    # right-aligned -- exactly the preview's certificate info table)
    cert_rows = [
        [
            Paragraph('Certificate No:', sty_ci_label),
            Paragraph(_esc(report_number), sty_ci_value),
            Paragraph('ULR No:', sty_ci_label_r),
            Paragraph(_esc(accreditation_number) or '—', sty_ci_value_r),
        ],
        [
            Paragraph('Certificate Issue Date:', sty_ci_label),
            Paragraph(issue_date_fmt, sty_ci_value),
            Paragraph('Verification Type:', sty_ci_label_r),
            Paragraph(_esc(verification_type_label) or '—', sty_ci_value_r),
        ],
        [
            Paragraph('Report Version:', sty_ci_label),
            Paragraph(str(report_version), sty_ci_value),
            Paragraph('', sty_ci_label_r),
            Paragraph('', sty_ci_value_r),
        ],
    ]
    cert_tbl = Table(cert_rows, colWidths=[
        FRAME_W * 0.22, FRAME_W * 0.32, FRAME_W * 0.24, FRAME_W * 0.22,
    ])
    cert_tbl.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(cert_tbl)

    # ===================================================================
    # 1. Instrument Under Test -- preview's 4-column key-value grid,
    # extended with the extra fields the PDF has always carried
    # ===================================================================
    story.extend(_section_bar('1. Instrument Under Test'))

    def _kvl(text):
        return Paragraph(text, sty_kv_label)

    def _kvv(text):
        return Paragraph(text, sty_kv_value)

    max_safe_load = (
        f'{_inst("max_safe_load")} {unit_str}'
        if instrument is not None and instrument.max_safe_load else '—'
    )
    inst_rows = [
        [_kvl('Instrument Detail'),
         _kvv('Non-Automatic Weighing Instrument'), '', ''],
        [_kvl('Make / Manufacturer'), _kvv(_esc(_inst('manufacturer'))),
         _kvl('Model'), _kvv(_esc(_inst('model_name')))],
        [_kvl('Serial Number'), _kvv(_esc(_inst('serial_number'))),
         _kvl('Accuracy Class'), _kvv(_esc(_accuracy_label()))],
        [_kvl('Max Capacity (Max)'),
         _kvv(f'{_inst("max_capacity")} {unit_str}'),
         _kvl('Min Capacity (Min)'),
         _kvv(f'{_inst("min_capacity")} {unit_str}')],
        [_kvl('Verification Scale Interval (e)'),
         _kvv(f'{_inst("verification_scale_interval_e")} {unit_str}'),
         _kvl('Actual Scale Interval (d)'),
         _kvv(f'{_inst("actual_scale_interval_d")} {unit_str}')],
        [_kvl('Number of Scale Intervals (n)'),
         _kvv(_inst('num_scale_intervals_n')),
         _kvl('Tare Device'), _kvv(_esc(_tare_label()))],
        [_kvl('Maximum Additive Tare'),
         _kvv(f'{_inst("max_additive_tare")} {unit_str}'),
         _kvl('Maximum Safe Load'), _kvv(max_safe_load)],
        [_kvl('Multi-Interval'),
         _kvv('Yes' if instrument is not None and instrument.is_multi_interval
              else 'No'),
         _kvl(''), _kvv('')],
    ]
    inst_tbl = Table(inst_rows, colWidths=[
        FRAME_W * 0.26, FRAME_W * 0.24, FRAME_W * 0.26, FRAME_W * 0.24,
    ])
    inst_style = _kv_table_style()
    inst_style.append(('SPAN', (1, 0), (3, 0)))
    inst_style.append(('BACKGROUND', (1, 0), (3, 0), CLR_WHITE))
    inst_tbl.setStyle(TableStyle(inst_style))
    story.append(inst_tbl)

    # ===================================================================
    # 2. Customer / Applicant Details (PDF-only data, styled as a grid)
    # ===================================================================
    story.extend(_section_bar('2. Customer / Applicant Details'))

    cust_rows = [
        [_kvl('Customer / Applicant Name'),
         _kvv(_esc(customer_name) or '—'), '', ''],
        [_kvl('Address'), _kvv(_esc(customer_address) or '—'), '', ''],
        [_kvl('Contact'), _kvv(_esc(customer_contact) or '—'),
         _kvl('Test Request Date'), _kvv(request_date_fmt)],
        [_kvl('Date of Testing'), _kvv(session_date_fmt),
         _kvl(''), _kvv('')],
    ]
    cust_tbl = Table(cust_rows, colWidths=[
        FRAME_W * 0.26, FRAME_W * 0.24, FRAME_W * 0.26, FRAME_W * 0.24,
    ])
    cust_style = _kv_table_style()
    for r_idx in (0, 1):
        cust_style.append(('SPAN', (1, r_idx), (3, r_idx)))
        cust_style.append(('BACKGROUND', (1, r_idx), (3, r_idx), CLR_WHITE))
    cust_tbl.setStyle(TableStyle(cust_style))
    story.append(cust_tbl)

    # ===================================================================
    # 3. Environmental Conditions During Test (preview's combined grid)
    # ===================================================================
    story.extend(_section_bar('3. Environmental Conditions During Test'))

    temp_start_s = _format_decimal(temperature_start) if temperature_start else ''
    temp_end_s = _format_decimal(temperature_end) if temperature_end else ''
    if temp_start_s:
        temp_range_s = (
            f'{temp_start_s} – {temp_end_s} °C' if temp_end_s
            else f'{temp_start_s} °C'
        )
    else:
        temp_range_s = '—'
    humidity_s = (
        f'{_format_decimal(humidity)} %' if humidity else '—')
    pressure_s = (
        f'{_format_decimal(barometric_pressure)} hPa'
        if barometric_pressure else '—')

    env_rows = [
        [_kvl('Average Temperature'), _kvv(temp_range_s),
         _kvl('Average Relative Humidity'), _kvv(humidity_s)],
        [_kvl('Average Barometric Pressure'), _kvv(pressure_s),
         _kvl(''), _kvv('')],
    ]
    env_tbl = Table(env_rows, colWidths=[
        FRAME_W * 0.26, FRAME_W * 0.24, FRAME_W * 0.26, FRAME_W * 0.24,
    ])
    env_tbl.setStyle(TableStyle(_kv_table_style()))
    story.append(env_tbl)

    # ===================================================================
    # 4. Important Remarks -- bordered box with a numbered list
    # ===================================================================
    story.extend(_section_bar('4. Important Remarks'))

    from apps.reports.generators import DEFAULT_REMARKS
    remarks = context.get('remarks') or DEFAULT_REMARKS

    remark_data = []
    for idx, remark in enumerate(remarks, 1):
        remark_data.append([
            Paragraph(f'{idx}.', sty_remark),
            Paragraph(_esc(remark), sty_remark),
        ])

    remark_tbl = Table(remark_data,
                       colWidths=[FRAME_W * 0.05, FRAME_W * 0.95])
    remark_tbl.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), BORDER_W, CLR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(remark_tbl)

    # Switch to Later page template for remaining pages
    story.append(NextPageTemplate('Later'))
    story.append(PageBreak())

    # ===================================================================
    # PAGE 2+ -- 5. Test Results (subsections 5.1, 5.2, ... with the
    # preview's underlined subsection headings)
    # ===================================================================
    section_num = 5
    story.extend(_section_bar(f'{section_num}. Test Results'))

    for sub_idx, sec in enumerate(test_sections, 1):
        title = sec['title']
        test_type = sec['test_type']
        results = sec['results']

        section_flowables: list = []
        section_flowables.extend(
            _subhead(f'{section_num}.{sub_idx} {title}'))

        if not results:
            section_flowables.append(Paragraph(
                'Not Applicable — Test was not performed for this instrument.',
                sty_na,
            ))
            section_flowables.append(Spacer(1, 8))
            story.extend(section_flowables)
            continue

        # Build table based on test type
        if test_type == TestType.WEIGHING_PERFORMANCE:
            _add_weighing_table(
                section_flowables, results, FRAME_W, unit_str,
                S, _base_table_style, _status_para,
            )
        elif test_type == TestType.ECCENTRICITY:
            _add_eccentricity_table(
                section_flowables, results, FRAME_W, unit_str,
                S, _base_table_style, _status_para,
            )
        elif test_type == TestType.REPEATABILITY:
            _add_repeatability_table(
                section_flowables, results, FRAME_W, unit_str,
                S, _base_table_style, _status_para,
            )
        elif test_type == TestType.DISCRIMINATION:
            _add_discrimination_table(
                section_flowables, results, FRAME_W, unit_str,
                S, _base_table_style, _status_para,
            )
        else:
            _add_generic_table(
                section_flowables, results, FRAME_W, unit_str,
                S, _base_table_style, _status_para,
            )

        section_flowables.append(Spacer(1, 10))

        # Use KeepTogether only for small tables; otherwise just append
        if len(results) <= 6:
            story.append(KeepTogether(section_flowables))
        else:
            story.extend(section_flowables)

    section_num += 1

    # ===================================================================
    # 6. Measurement Uncertainty budget
    # ===================================================================
    budget = context.get('uncertainty_budget')
    if budget:
        budget_flowables: list = []
        budget_flowables.extend(
            _section_bar(f'{section_num}. Measurement Uncertainty'))
        budget_flowables.append(Paragraph(
            f'Uncertainty budget evaluated at the highest tested load '
            f'({_format_decimal(budget["load"])} {budget["unit"]}), '
            f'in accordance with EURAMET cg-18 principles:',
            sty_cell,
        ))
        budget_flowables.append(Spacer(1, 4))

        # Round budget figures to the instrument resolution d, matching the
        # rounding used in the result tables (never rounded down).
        from apps.engine.uncertainty import round_uncertainty

        def _fmt_u(value) -> str:
            d_val = getattr(instrument, 'actual_scale_interval_d', None)
            if d_val:
                try:
                    return str(round_uncertainty(Decimal(str(value)), d_val))
                except Exception:
                    pass
            return f'{value:.6f}'

        budget_rows = [[
            Paragraph('<b>Uncertainty Component</b>', sty_hdr_l),
            Paragraph(f'<b>Standard Uncertainty ({budget["unit"]})</b>',
                      sty_hdr_r),
        ]]
        for name, value in budget['components']:
            budget_rows.append([
                Paragraph(_esc(name), sty_cell),
                Paragraph(_fmt_u(value), sty_num),
            ])
        budget_rows.append([
            Paragraph('<b>Combined standard uncertainty u<sub>c</sub></b>',
                      sty_cell),
            Paragraph(f'<b>{_fmt_u(budget["u_combined"])}</b>', sty_num),
        ])
        budget_rows.append([
            Paragraph(f'<b>Expanded uncertainty U (k={budget["k"]}, ~95%)</b>',
                      sty_cell),
            Paragraph(f'<b>&plusmn;{_fmt_u(budget["expanded"])}</b>', sty_num),
        ])
        budget_tbl = Table(
            budget_rows, colWidths=[FRAME_W * 0.62, FRAME_W * 0.38])
        budget_tbl.setStyle(TableStyle(_base_table_style(len(budget_rows))))
        budget_flowables.append(budget_tbl)
        story.append(KeepTogether(budget_flowables))
        section_num += 1

    # ===================================================================
    # LAST PAGE -- Overall summary, verdict box, conclusion, signatures
    # ===================================================================
    story.append(PageBreak())

    story.extend(_section_bar(f'{section_num}. Overall Test Summary'))

    summary_header = [
        Paragraph('<b>Sr No.</b>', sty_hdr_c),
        Paragraph('<b>Test Performed</b>', sty_hdr_l),
        Paragraph('<b>Result</b>', sty_hdr_c),
    ]
    summary_rows = [summary_header]
    for idx, item in enumerate(compliance_summary, 1):
        summary_rows.append([
            Paragraph(str(idx), sty_cell_c),
            Paragraph(_esc(item['test_name']), sty_cell),
            _status_para(item['status'], item['status_label']),
        ])

    col_w_summary = [FRAME_W * 0.10, FRAME_W * 0.66, FRAME_W * 0.24]
    summary_tbl = Table(summary_rows, colWidths=col_w_summary)
    summary_tbl.setStyle(TableStyle(
        _base_table_style(len(summary_rows))))
    story.append(summary_tbl)

    # Overall verdict box (preview: thick coloured border, tinted
    # background, large bold uppercase verdict)
    is_pass = overall_verdict == ComplianceStatus.PASS
    verdict_label = (
        'CONFORMS TO OIML R 76-1:2006' if is_pass
        else 'DOES NOT CONFORM TO OIML R 76-1:2006'
    )
    verdict_tbl = Table(
        [[Paragraph(verdict_label,
                    sty_verdict_pass if is_pass else sty_verdict_fail)]],
        colWidths=[FRAME_W],
    )
    verdict_tbl.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2, CLR_PASS if is_pass else CLR_FAIL),
        ('BACKGROUND', (0, 0), (-1, -1),
         CLR_PASS_BG if is_pass else CLR_FAIL_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 16),
        ('RIGHTPADDING', (0, 0), (-1, -1), 16),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(Spacer(1, 14))
    story.append(verdict_tbl)
    story.append(Spacer(1, 10))

    # Conclusion narrative (preview wording, justified)
    verdict_word = (
        f'<b><font color="{COLOR_PASS}">CONFORMS</font></b>' if is_pass
        else f'<b><font color="{COLOR_FAIL}">DOES NOT CONFORM</font></b>'
    )
    evaluation_detail = evaluation_type_label or ''
    if (verification_type_label
            and verification_type_label.lower()
            not in evaluation_detail.lower()):
        evaluation_detail += (
            f' — {verification_type_label} Verification')
    conclusion_text = (
        f'Based on the test results obtained in accordance with OIML '
        f'Recommendation R 76-1:2006 (Non-automatic weighing instruments '
        f'&mdash; Part 1: Metrological and technical requirements &mdash; '
        f'Tests), the above-described instrument bearing Serial Number '
        f'<b>{_esc(_inst("serial_number"))}</b>, manufactured by '
        f'<b>{_esc(_inst("manufacturer"))}</b>, Model '
        f'<b>{_esc(_inst("model_name"))}</b>, with maximum capacity '
        f'<b>{_inst("max_capacity")} {unit_str}</b> and accuracy class '
        f'<b>{_esc(_inst("accuracy_class"))}</b>, {verdict_word} to the '
        f'requirements specified for its declared accuracy class '
        f'({_esc(evaluation_detail)}) as per the said recommendation.'
    )
    story.append(Paragraph(conclusion_text, sty_conclusion))

    # Three-column signature block (preview: rule above each signatory,
    # bold role, name, designation and date in faint grey)
    sig_gap = 6 * mm
    sig_col_w = (FRAME_W - 2 * sig_gap) / 3

    def _sig_cell(role: str, name: str, designation: str,
                  date_str: str) -> list:
        return [
            Paragraph(f'<b>{_esc(role)}</b>', sty_sig_role),
            Paragraph(_esc(name) if name else '________________',
                      sty_sig_name),
            Paragraph(_esc(designation), sty_sig_meta),
            Paragraph(
                f'Date: {date_str}' if date_str else 'Date: ________________',
                sty_sig_meta),
        ]

    sig_row = [
        _sig_cell('Tested By', engineer_name, 'Testing Officer',
                  session_date_fmt),
        '',
        _sig_cell('Checked By', checked_by_name, 'Senior Technical Officer',
                  checked_at_fmt),
        '',
        _sig_cell('Approved By', approved_by_name, 'Laboratory In-Charge',
                  approved_at_fmt),
    ]
    sig_tbl = Table(
        [sig_row],
        colWidths=[sig_col_w, sig_gap, sig_col_w, sig_gap, sig_col_w],
    )
    sig_style = [
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]
    for col in (0, 2, 4):
        sig_style.append(
            ('LINEABOVE', (col, 0), (col, 0), 0.75, CLR_TEXT))
    sig_tbl.setStyle(TableStyle(sig_style))
    story.append(Spacer(1, 56))  # room for physical signatures
    story.append(sig_tbl)

    # QR code for public certificate verification
    verify_url = context.get('verify_url')
    if verify_url:
        qr_flowable = _build_qr_block(verify_url, sty_normal_center)
        if qr_flowable is not None:
            story.append(Spacer(1, 18))
            story.append(qr_flowable)

    # End-of-report marker (before the repeating document-control footer)
    story.append(Spacer(1, 14))
    story.append(Paragraph('--- End of Test Report ---', sty_normal_center))

    # -------------------------------------------------------------------
    # Build (with deferred 'Page X of Y' numbering)
    # -------------------------------------------------------------------
    doc.build(story, canvasmaker=_NumberedCanvas)


def _load_logo_reader(logo_data_uri: str):
    """Decode a data: URI into (ImageReader, width_pt, height_pt).

    Sized like the preview's logo (max ~40px high / 80px wide -> capped at
    12mm x 24mm). Returns None on any failure so the certificate renders
    without a logo.
    """
    try:
        import base64
        import io

        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader

        b64 = logo_data_uri.split(',', 1)[1]
        buf = io.BytesIO(base64.b64decode(b64))
        reader = ImageReader(buf)
        w, h = reader.getSize()
        scale = min((24 * mm) / w, (12 * mm) / h, 1.0)
        return reader, w * scale, h * scale
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
            f'<font size="6" color="{COLOR_FAINT}">{verify_url}</font>',
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
#
# All builders share the preview's table treatment: grey bold header
# row, thin #999 grid, alternating #FAFAFA rows, right-aligned mono
# numerics and coloured Pass/Fail cells (applied via _base_table_style
# and the styles bundle S).
# ===================================================================

def _add_weighing_table(
    flowables: list,
    results: list,
    frame_w: float,
    unit: str,
    S: dict,
    base_style_fn,
    status_para_fn,
) -> None:
    """Weighing Performance: Sr No, Test Point, Ref Mass, Indicated,
    Error, MPE, Uncertainty, Result."""
    from reportlab.platypus import Paragraph, Table, TableStyle

    header = [
        Paragraph('<b>Sr No.</b>', S['hdr_c']),
        Paragraph(f'<b>Test Point ({unit})</b>', S['hdr_r']),
        Paragraph(f'<b>Ref. Mass ({unit})</b>', S['hdr_r']),
        Paragraph(f'<b>Indicated ({unit})</b>', S['hdr_r']),
        Paragraph(f'<b>Error ({unit})</b>', S['hdr_r']),
        Paragraph(f'<b>MPE (±{unit})</b>', S['hdr_r']),
        Paragraph(f'<b>U (±{unit}) k=2</b>', S['hdr_r']),
        Paragraph('<b>Result</b>', S['hdr_c']),
    ]
    rows = [header]
    for idx, r in enumerate(results, 1):
        obs = r.observation
        indicated = _format_decimal(obs.indicated_value) if obs else '—'
        ref_val = _format_decimal(obs.reference_value) if obs else \
            _format_decimal(r.test_point_load)
        uncertainty = getattr(r, 'expanded_uncertainty', None)
        rows.append([
            Paragraph(str(idx), S['cell_c']),
            Paragraph(_format_decimal(r.test_point_load), S['num']),
            Paragraph(ref_val, S['num']),
            Paragraph(indicated, S['num']),
            Paragraph(_format_decimal(r.computed_error), S['num']),
            Paragraph(
                f'±{_format_decimal(r.mpe_applicable)}'
                if r.mpe_applicable else '—',
                S['num']),
            Paragraph(
                f'±{_format_decimal(uncertainty)}' if uncertainty else '—',
                S['num']),
            status_para_fn(r.compliance_status),
        ])

    col_widths = [
        frame_w * 0.07,
        frame_w * 0.13,
        frame_w * 0.14,
        frame_w * 0.14,
        frame_w * 0.13,
        frame_w * 0.13,
        frame_w * 0.13,
        frame_w * 0.13,
    ]
    tbl = Table(rows, colWidths=col_widths)
    tbl.setStyle(TableStyle(base_style_fn(len(rows))))
    flowables.append(tbl)


def _add_eccentricity_table(
    flowables: list,
    results: list,
    frame_w: float,
    unit: str,
    S: dict,
    base_style_fn,
    status_para_fn,
) -> None:
    """Eccentricity: Position-based layout with position labels."""
    from reportlab.platypus import Paragraph, Table, TableStyle

    header = [
        Paragraph('<b>Sr No.</b>', S['hdr_c']),
        Paragraph('<b>Position</b>', S['hdr_l']),
        Paragraph(f'<b>Test Load ({unit})</b>', S['hdr_r']),
        Paragraph(f'<b>Indicated ({unit})</b>', S['hdr_r']),
        Paragraph(f'<b>Error ({unit})</b>', S['hdr_r']),
        Paragraph(f'<b>MPE (±{unit})</b>', S['hdr_r']),
        Paragraph('<b>Result</b>', S['hdr_c']),
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
            Paragraph(str(idx), S['cell_c']),
            Paragraph(pos_label, S['cell']),
            Paragraph(_format_decimal(r.test_point_load), S['num']),
            Paragraph(indicated, S['num']),
            Paragraph(_format_decimal(r.computed_error), S['num']),
            Paragraph(
                f'±{_format_decimal(r.mpe_applicable)}'
                if r.mpe_applicable else '—',
                S['num']),
            status_para_fn(r.compliance_status),
        ])

    col_widths = [
        frame_w * 0.07,
        frame_w * 0.19,
        frame_w * 0.14,
        frame_w * 0.16,
        frame_w * 0.14,
        frame_w * 0.14,
        frame_w * 0.16,
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
        from reportlab.platypus import Spacer
        flowables.append(Spacer(1, 3))
        flowables.append(Paragraph(
            f'Maximum difference from centre load: '
            f'{_format_decimal(max_diff)} {unit}',
            S['cell'],
        ))


def _add_repeatability_table(
    flowables: list,
    results: list,
    frame_w: float,
    unit: str,
    S: dict,
    base_style_fn,
    status_para_fn,
) -> None:
    """Repeatability: Trial-based layout with range calculation."""
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from collections import OrderedDict

    # Group by test_point_load
    by_load: dict[str, list] = OrderedDict()
    for r in results:
        key = _format_decimal(r.test_point_load)
        by_load.setdefault(key, []).append(r)

    for load_str, load_results in by_load.items():
        flowables.append(Paragraph(
            f'<b>Test Load: {load_str} {unit}</b>', S['cell_b']))
        flowables.append(Spacer(1, 2))

        header = [
            Paragraph('<b>Trial</b>', S['hdr_c']),
            Paragraph(f'<b>Indicated ({unit})</b>', S['hdr_r']),
            Paragraph(f'<b>Error ({unit})</b>', S['hdr_r']),
            Paragraph(f'<b>MPE (±{unit})</b>', S['hdr_r']),
            Paragraph('<b>Result</b>', S['hdr_c']),
        ]

        rows = [header]
        indicated_values = []
        for r in load_results:
            obs = r.observation
            ind_val = obs.indicated_value if obs else None
            if ind_val is not None:
                indicated_values.append(ind_val)
            rows.append([
                Paragraph(str(r.trial_number), S['cell_c']),
                Paragraph(
                    _format_decimal(ind_val) if ind_val is not None
                    else '—', S['num']),
                Paragraph(_format_decimal(r.computed_error), S['num']),
                Paragraph(
                    f'±{_format_decimal(r.mpe_applicable)}'
                    if r.mpe_applicable else '—',
                    S['num']),
                status_para_fn(r.compliance_status),
            ])

        # Range row
        if indicated_values:
            range_val = max(indicated_values) - min(indicated_values)
            rows.append([
                Paragraph('<b>Range</b>', S['cell_c']),
                Paragraph(f'<b>{_format_decimal(range_val)}</b>', S['num']),
                Paragraph('', S['cell_c']),
                Paragraph('', S['cell_c']),
                Paragraph('', S['cell_c']),
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
        flowables.append(Spacer(1, 6))


def _add_discrimination_table(
    flowables: list,
    results: list,
    frame_w: float,
    unit: str,
    S: dict,
    base_style_fn,
    status_para_fn,
) -> None:
    """Discrimination: Test Load, Indication before, Indication after adding
    1.4d, Change, Result."""
    from reportlab.platypus import Paragraph, Table, TableStyle

    header = [
        Paragraph('<b>Sr No.</b>', S['hdr_c']),
        Paragraph(f'<b>Test Load ({unit})</b>', S['hdr_r']),
        Paragraph(f'<b>Indication Before ({unit})</b>', S['hdr_r']),
        Paragraph(f'<b>Indication After +1.4d ({unit})</b>', S['hdr_r']),
        Paragraph(f'<b>Change ({unit})</b>', S['hdr_r']),
        Paragraph('<b>Result</b>', S['hdr_c']),
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
            Paragraph(str(idx), S['cell_c']),
            Paragraph(_format_decimal(r.test_point_load), S['num']),
            Paragraph(indicated_before, S['num']),
            Paragraph(indicated_after, S['num']),
            Paragraph(change, S['num']),
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
    unit: str,
    S: dict,
    base_style_fn,
    status_para_fn,
) -> None:
    """Generic table for any test type not covered by a specific builder."""
    from reportlab.platypus import Paragraph, Table, TableStyle

    header = [
        Paragraph('<b>Sr No.</b>', S['hdr_c']),
        Paragraph(f'<b>Test Load ({unit})</b>', S['hdr_r']),
        Paragraph(f'<b>Indicated ({unit})</b>', S['hdr_r']),
        Paragraph(f'<b>Error ({unit})</b>', S['hdr_r']),
        Paragraph(f'<b>MPE (±{unit})</b>', S['hdr_r']),
        Paragraph('<b>Result</b>', S['hdr_c']),
    ]

    rows = [header]
    for idx, r in enumerate(results, 1):
        obs = r.observation
        indicated = _format_decimal(obs.indicated_value) if obs else '—'
        rows.append([
            Paragraph(str(idx), S['cell_c']),
            Paragraph(_format_decimal(r.test_point_load), S['num']),
            Paragraph(indicated, S['num']),
            Paragraph(_format_decimal(r.computed_error), S['num']),
            Paragraph(
                f'±{_format_decimal(r.mpe_applicable)}'
                if r.mpe_applicable else '—',
                S['num']),
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
