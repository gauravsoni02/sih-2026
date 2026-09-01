import logging
import mimetypes
from pathlib import Path

from django.db.models import Q
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import CanApprove, CanWrite, IsLabManager
from apps.engine.constants import ComplianceStatus, ReportStatus, SessionStatus
from apps.testing.models import TestSession

from .models import Report
from .serializers import ReportListSerializer, ReportSerializer

logger = logging.getLogger(__name__)


class ReportGenerateThrottle(UserRateThrottle):
    """Per-user throttle for synchronous report generation (PDF + signing)."""
    scope = 'report_generate'


def _check_lab_access(request: Request, session) -> Response | None:
    """Non-admin users may only touch reports of their own laboratory.

    Returns a 403 Response when access is denied, else None.
    """
    user = request.user
    if (
        getattr(user, 'role', '') != 'admin'
        and getattr(user, 'laboratory_id', None)
        and session.laboratory_id != user.laboratory_id
    ):
        return Response(
            {'detail': 'You do not have access to reports of another laboratory.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


def _regenerate_report_files(report) -> bool:
    """Re-run PDF + signature + DOCX for *report*, updating file paths.

    Returns True on success, False on failure (logged, never raised).
    """
    try:
        from apps.reports.generators.docx import generate_docx
        from apps.reports.generators.pdf import generate_pdf
        from apps.reports.signing import sign_pdf

        pdf_path = generate_pdf(report)
        sign_pdf(pdf_path, reason=f'Certificate {report.report_number}')
        report.pdf_path = pdf_path

        docx_path = generate_docx(report)
        report.docx_path = docx_path

        report.save(update_fields=['pdf_path', 'docx_path', 'updated_at'])
        return True
    except Exception:
        logger.exception(
            "Report regeneration failed for report %s", report.report_number
        )
        return False


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Report.objects.select_related(
        'session', 'generated_by', 'approved_by'
    ).all()
    permission_classes = [CanWrite]
    filterset_fields = ['status', 'overall_verdict']
    search_fields = ['report_number']
    ordering_fields = ['created_at', 'report_number']

    def get_serializer_class(self):
        if self.action == 'list':
            return ReportListSerializer
        return ReportSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsLabManager])
    def review(self, request: Request, pk: str = None) -> Response:
        """Mark a draft report as reviewed (checked) by a lab manager/admin."""
        report = self.get_object()
        denied = _check_lab_access(request, report.session)
        if denied:
            return denied
        if report.status in (ReportStatus.REVIEWED, ReportStatus.APPROVED):
            return Response(
                {'detail': 'Report has already been reviewed or approved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report.status = ReportStatus.REVIEWED
        report.checked_by = request.user
        report.checked_at = timezone.now()
        report.save(update_fields=[
            'status', 'checked_by', 'checked_at', 'updated_at',
        ])
        serializer = ReportSerializer(report)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[CanApprove])
    def approve(self, request: Request, pk: str = None) -> Response:
        report = self.get_object()
        denied = _check_lab_access(request, report.session)
        if denied:
            return denied
        if report.status == ReportStatus.APPROVED:
            return Response(
                {'detail': 'Report already approved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if report.status != ReportStatus.REVIEWED:
            return Response(
                {'detail': 'Report must be reviewed (checked) before approval.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        report.status = ReportStatus.APPROVED
        report.approved_by = request.user
        report.approved_at = timezone.now()
        report.save(update_fields=[
            'status', 'approved_by', 'approved_at', 'updated_at',
        ])

        # Regenerate + re-sign so the issued files carry the approver,
        # checked-by and the real certificate issue date.
        regenerated = _regenerate_report_files(report)

        data = ReportSerializer(report).data
        if not regenerated:
            data['regeneration_failed'] = True
        return Response(data)

    @action(detail=True, methods=['get'])
    def preview(self, request: Request, pk: str = None) -> Response:
        from apps.laboratory.models import OrgSettings
        from apps.reports.generators import DEFAULT_REMARKS

        report = self.get_object()
        session = report.session
        denied = _check_lab_access(request, session)
        if denied:
            return denied
        inst = session.instrument
        lab = session.laboratory
        org = OrgSettings.load()

        results = session.results.order_by('test_type', 'trial_number', 'test_point_load')
        results_data = []
        for r in results:
            results_data.append({
                'test_type': r.test_type,
                'test_point_load': str(r.test_point_load) if r.test_point_load else None,
                'computed_error': str(r.computed_error) if r.computed_error else None,
                'mpe_applicable': str(r.mpe_applicable) if r.mpe_applicable else None,
                'expanded_uncertainty': str(r.expanded_uncertainty) if r.expanded_uncertainty else None,
                'compliance_status': r.compliance_status,
                'position': r.position,
                'trial_number': r.trial_number,
                'remarks': r.remarks,
            })

        return Response({
            'report': {
                'report_number': report.report_number,
                'version': report.version,
                'status': report.status,
                'overall_verdict': report.overall_verdict,
                'created_at': report.created_at.isoformat(),
                'generated_by': report.generated_by.get_full_name() or report.generated_by.username,
                'approved_by': (report.approved_by.get_full_name() or report.approved_by.username) if report.approved_by else None,
                'approved_at': report.approved_at.isoformat() if report.approved_at else None,
                'checked_by': (report.checked_by.get_full_name() or report.checked_by.username) if report.checked_by else None,
                'checked_at': report.checked_at.isoformat() if report.checked_at else None,
            },
            'session': {
                'id': session.id,
                'session_date': str(session.session_date),
                'temperature_start': str(session.temperature_start) if session.temperature_start else None,
                'temperature_end': str(session.temperature_end) if session.temperature_end else None,
                'humidity': str(session.humidity) if session.humidity else None,
                'barometric_pressure': str(session.barometric_pressure) if session.barometric_pressure else None,
                'evaluation_type': session.evaluation_type,
                'verification_type': session.verification_type,
                'engineer': session.engineer.get_full_name() or session.engineer.username,
            },
            'instrument': {
                'manufacturer': inst.manufacturer,
                'model_name': inst.model_name,
                'serial_number': inst.serial_number,
                'accuracy_class': inst.accuracy_class,
                'max_capacity': str(inst.max_capacity),
                'min_capacity': str(inst.min_capacity),
                'verification_scale_interval_e': str(inst.verification_scale_interval_e),
                'actual_scale_interval_d': str(inst.actual_scale_interval_d),
                'num_scale_intervals_n': inst.num_scale_intervals_n,
                'unit': inst.unit,
            },
            'laboratory': {
                'name': lab.name,
                'address': lab.address,
                'accreditation_number': lab.accreditation_number,
                'lab_code': lab.lab_code,
            },
            'results': results_data,
            'org_settings': {
                'jurisdiction': org.jurisdiction,
                'doc_control_number': org.doc_control_number,
                'doc_issue_number': org.doc_issue_number,
                'doc_rev_number': org.doc_rev_number,
                'doc_issue_date': org.doc_issue_date,
                'default_remarks': org.default_remarks or DEFAULT_REMARKS,
                'logo_data_uri': org.logo_data_uri,
            },
        })

    @action(detail=True, methods=['get'], url_path='download/(?P<fmt>pdf|docx)')
    def download(self, request: Request, pk: str = None, fmt: str = 'pdf'):
        report = self.get_object()
        denied = _check_lab_access(request, report.session)
        if denied:
            return denied
        file_path = report.pdf_path if fmt == 'pdf' else report.docx_path
        if not file_path:
            raise Http404(f"No {fmt.upper()} file available for this report.")

        path = Path(file_path)
        if not path.exists():
            raise Http404(f"Report file not found on disk.")

        content_type = 'application/pdf' if fmt == 'pdf' else \
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        return FileResponse(
            open(path, 'rb'),
            content_type=content_type,
            as_attachment=True,
            filename=path.name,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_reports(request: Request) -> Response:
    q = request.query_params.get('q', '').strip()
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    accuracy_class = request.query_params.get('accuracy_class')
    manufacturer = request.query_params.get('manufacturer')
    verdict = request.query_params.get('verdict')
    report_status = request.query_params.get('status')

    qs = Report.objects.select_related(
        'session__instrument', 'session__laboratory', 'generated_by', 'approved_by',
    ).filter(is_deleted=False)

    if q:
        use_postgres = False
        try:
            from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
            from django.db import connection
            use_postgres = connection.vendor == 'postgresql'
        except ImportError:
            pass

        if use_postgres:
            vector = (
                SearchVector('report_number', weight='A')
                + SearchVector('session__instrument__manufacturer', weight='B')
                + SearchVector('session__instrument__model_name', weight='B')
                + SearchVector('session__instrument__serial_number', weight='A')
                + SearchVector('session__laboratory__name', weight='C')
            )
            query = SearchQuery(q)
            qs = qs.annotate(
                search=vector, rank=SearchRank(vector, query),
            ).filter(search=query).order_by('-rank')
        else:
            qs = qs.filter(
                Q(report_number__icontains=q)
                | Q(session__instrument__manufacturer__icontains=q)
                | Q(session__instrument__model_name__icontains=q)
                | Q(session__instrument__serial_number__icontains=q)
                | Q(session__laboratory__name__icontains=q)
            )

    if date_from:
        qs = qs.filter(session__session_date__gte=date_from)
    if date_to:
        qs = qs.filter(session__session_date__lte=date_to)
    if accuracy_class:
        qs = qs.filter(session__instrument__accuracy_class=accuracy_class)
    if manufacturer:
        qs = qs.filter(session__instrument__manufacturer__icontains=manufacturer)
    if verdict:
        qs = qs.filter(overall_verdict=verdict)
    if report_status:
        qs = qs.filter(status=report_status)

    if not q:
        qs = qs.order_by('-created_at')

    results = []
    for r in qs[:50]:
        inst = r.session.instrument
        results.append({
            'id': r.id,
            'report_number': r.report_number,
            'overall_verdict': r.overall_verdict,
            'status': r.status,
            'version': r.version,
            'created_at': r.created_at.isoformat(),
            'session_date': str(r.session.session_date),
            'instrument_name': f"{inst.manufacturer} {inst.model_name}",
            'serial_number': inst.serial_number,
            'accuracy_class': inst.accuracy_class,
            'laboratory_name': r.session.laboratory.name,
        })

    return Response({'count': qs.count(), 'results': results})


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def verify_report(request: Request, code: str) -> Response:
    """Public certificate verification — no authentication required.

    Returns only what a certificate holder can already read off the paper,
    so no sensitive data is exposed.
    """
    try:
        report = Report.objects.select_related(
            'session__instrument', 'session__laboratory', 'approved_by',
        ).get(verification_code=code, is_deleted=False)
    except Report.DoesNotExist:
        return Response(
            {'valid': False, 'detail': 'No certificate found for this code.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    inst = report.session.instrument
    lab = report.session.laboratory
    return Response({
        'valid': True,
        'report_number': report.report_number,
        'status': report.status,
        'overall_verdict': report.overall_verdict,
        'version': report.version,
        'issued_at': report.created_at.isoformat(),
        'approved': report.status == ReportStatus.APPROVED,
        'approved_at': report.approved_at.isoformat() if report.approved_at else None,
        'session_date': str(report.session.session_date),
        'instrument': {
            'manufacturer': inst.manufacturer,
            'model_name': inst.model_name,
            'serial_number': inst.serial_number,
            'accuracy_class': inst.accuracy_class,
        },
        'laboratory': {
            'name': lab.name,
            'accreditation_number': lab.accreditation_number,
        },
    })


@api_view(['POST'])
@permission_classes([CanWrite])
@throttle_classes([ReportGenerateThrottle])
def generate_report_view(request: Request, session_id: int) -> Response:
    try:
        session = TestSession.objects.select_related(
            'instrument', 'laboratory', 'engineer'
        ).get(pk=session_id)
    except TestSession.DoesNotExist:
        return Response(
            {'detail': 'Test session not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    denied = _check_lab_access(request, session)
    if denied:
        return denied

    if session.status != SessionStatus.COMPLETED:
        return Response(
            {'detail': 'Session must be completed before generating a report. Run Calculate first.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not session.results.exists():
        return Response(
            {'detail': 'No test results found. Run Calculate first.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if session.overall_verdict != ComplianceStatus.PASS:
        return Response(
            {'detail': 'Report can only be generated for sessions that CONFORM (pass). '
                       'This session verdict is: DOES NOT CONFORM.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    existing = Report.objects.filter(session=session).order_by('-version').first()
    if existing:
        new_version = existing.version + 1
    else:
        new_version = 1

    lab_code = session.laboratory.lab_code
    report_number = Report.generate_report_number(lab_code)
    overall_verdict = session.overall_verdict or 'fail'

    report = Report.objects.create(
        report_number=report_number,
        session=session,
        generated_by=request.user,
        overall_verdict=overall_verdict,
        version=new_version,
        status=ReportStatus.DRAFT,
    )

    _regenerate_report_files(report)

    serializer = ReportSerializer(report)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
