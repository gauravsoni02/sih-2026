import datetime
import json
import logging
from collections import defaultdict
from io import StringIO

from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.engine.constants import ComplianceStatus, SessionStatus, TestType
from apps.instruments.models import Instrument
from apps.reports.models import Report
from apps.testing.models import TestSession

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request: Request) -> Response:
    now = timezone.now()
    total_instruments = Instrument.objects.filter(is_deleted=False).count()
    sessions_this_month = TestSession.objects.filter(
        is_deleted=False,
        session_date__year=now.year,
        session_date__month=now.month,
    ).count()
    reports_generated = Report.objects.filter(is_deleted=False).count()

    completed = TestSession.objects.filter(
        is_deleted=False,
        overall_verdict__isnull=False,
    )
    total_with_verdict = completed.count()
    pass_count = completed.filter(overall_verdict=ComplianceStatus.PASS).count()
    pass_rate = round(pass_count / total_with_verdict * 100, 1) if total_with_verdict > 0 else 0

    prev_month = (now.replace(day=1) - datetime.timedelta(days=1))
    prev_instruments = Instrument.objects.filter(
        is_deleted=False, created_at__lt=now.replace(day=1),
    ).count()
    prev_sessions = TestSession.objects.filter(
        is_deleted=False,
        session_date__year=prev_month.year,
        session_date__month=prev_month.month,
    ).count()
    prev_reports = Report.objects.filter(
        is_deleted=False, created_at__lt=now.replace(day=1),
    ).count()

    prev_completed = TestSession.objects.filter(
        is_deleted=False,
        overall_verdict__isnull=False,
        session_date__year=prev_month.year,
        session_date__month=prev_month.month,
    )
    prev_total_with_verdict = prev_completed.count()
    prev_pass_count = prev_completed.filter(overall_verdict=ComplianceStatus.PASS).count()
    prev_pass_rate = round(prev_pass_count / prev_total_with_verdict * 100, 1) if prev_total_with_verdict > 0 else 0

    return Response({
        'total_instruments': total_instruments,
        'sessions_this_month': sessions_this_month,
        'reports_generated': reports_generated,
        'pass_rate': pass_rate,
        'prev_instruments': prev_instruments,
        'prev_sessions': prev_sessions,
        'prev_reports': prev_reports,
        'prev_pass_rate': prev_pass_rate,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_tests(request: Request) -> Response:
    today = timezone.now().date()
    months_count = min(int(request.query_params.get('months', 12)), 24)
    start = (today.replace(day=1) - datetime.timedelta(days=365)).replace(day=1)

    sessions = (
        TestSession.objects
        .filter(is_deleted=False, session_date__gte=start)
        .values('session_date', 'overall_verdict')
    )

    counts: dict[str, int] = defaultdict(int)
    pass_counts: dict[str, int] = defaultdict(int)
    fail_counts: dict[str, int] = defaultdict(int)
    for s in sessions:
        key = s['session_date'].strftime('%Y-%m')
        counts[key] += 1
        if s['overall_verdict'] == ComplianceStatus.PASS:
            pass_counts[key] += 1
        elif s['overall_verdict'] == ComplianceStatus.FAIL:
            fail_counts[key] += 1

    months = []
    current = start
    while current <= today:
        key = current.strftime('%Y-%m')
        total = counts.get(key, 0)
        passed = pass_counts.get(key, 0)
        failed = fail_counts.get(key, 0)
        months.append({
            'month': key,
            'count': total,
            'passed': passed,
            'failed': failed,
            'pending': total - passed - failed,
        })
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    return Response(months[-months_count:])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_sessions(request: Request) -> Response:
    sessions = (
        TestSession.objects
        .filter(is_deleted=False)
        .select_related('instrument', 'engineer')
        .order_by('-created_at')[:10]
    )

    data = []
    for s in sessions:
        data.append({
            'id': s.id,
            'session_date': str(s.session_date),
            'instrument_name': f"{s.instrument.manufacturer} {s.instrument.model_name}",
            'serial_number': s.instrument.serial_number,
            'accuracy_class': s.instrument.accuracy_class,
            'engineer': s.engineer.get_full_name() or s.engineer.username,
            'status': s.status,
            'overall_verdict': s.overall_verdict,
        })

    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def load_demo_samples(request: Request) -> Response:
    out = StringIO()
    try:
        call_command('load_demo_samples', stdout=out)
    except Exception as exc:
        logger.exception('Failed to load demo samples')
        return Response(
            {'detail': str(exc)}, status=400,
        )

    sessions = (
        TestSession.objects
        .filter(is_deleted=False, instrument__serial_number__startswith='DEMO-')
        .select_related('instrument')
        .order_by('instrument__serial_number')
    )
    data = []
    for s in sessions:
        data.append({
            'id': s.id,
            'session_date': str(s.session_date),
            'instrument_name': f"{s.instrument.manufacturer} {s.instrument.model_name}",
            'serial_number': s.instrument.serial_number,
            'accuracy_class': s.instrument.accuracy_class,
            'status': s.status,
            'overall_verdict': s.overall_verdict,
        })

    return Response({
        'message': out.getvalue().strip(),
        'samples': data,
        'count': len(data),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_demo_samples(request: Request) -> Response:
    out = StringIO()
    try:
        call_command('load_demo_samples', '--clear', stdout=out)
    except Exception as exc:
        logger.exception('Failed to clear demo samples')
        return Response({'detail': str(exc)}, status=400)
    return Response({'message': out.getvalue().strip()})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_demo_samples(request: Request) -> Response:
    sessions = (
        TestSession.objects
        .filter(is_deleted=False, instrument__serial_number__startswith='DEMO-')
        .select_related('instrument', 'engineer')
        .order_by('instrument__serial_number')
    )
    data = []
    for s in sessions:
        data.append({
            'id': s.id,
            'session_date': str(s.session_date),
            'instrument_name': f"{s.instrument.manufacturer} {s.instrument.model_name}",
            'serial_number': s.instrument.serial_number,
            'accuracy_class': s.instrument.accuracy_class,
            'status': s.status,
            'overall_verdict': s.overall_verdict,
            'engineer': s.engineer.get_full_name() or s.engineer.username,
        })
    return Response({'samples': data, 'count': len(data)})


ACTION_LABELS = {
    LogEntry.Action.CREATE: 'Created',
    LogEntry.Action.UPDATE: 'Updated',
    LogEntry.Action.DELETE: 'Deleted',
}

MODEL_LABELS = {
    'instrument': 'Instrument',
    'testsession': 'Test Session',
    'testobservation': 'Observation',
    'testresult': 'Test Result',
    'report': 'Report',
    'laboratory': 'Laboratory',
    'user': 'User',
}


def _format_log_entry(entry: LogEntry) -> dict:
    model_name = entry.content_type.model if entry.content_type else 'unknown'
    action = ACTION_LABELS.get(entry.action, 'Unknown')

    changes = {}
    if entry.changes:
        raw = entry.changes if isinstance(entry.changes, dict) else json.loads(entry.changes)
        changes = raw

    if entry.action == LogEntry.Action.UPDATE and changes.get('is_deleted') == [False, True]:
        action = 'Deleted'

    object_label = entry.object_repr or str(entry.object_id)

    return {
        'id': entry.id,
        'timestamp': entry.timestamp.isoformat(),
        'action': action,
        'model': MODEL_LABELS.get(model_name, model_name.title()),
        'object_id': str(entry.object_id) if entry.object_id else None,
        'object_label': object_label,
        'user': entry.actor.get_full_name() or entry.actor.username if entry.actor else None,
        'changes': changes,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def audit_log(request: Request) -> Response:
    limit = min(int(request.query_params.get('limit', 50)), 200)

    entries = (
        LogEntry.objects
        .select_related('content_type', 'actor')
        .order_by('-timestamp')[:limit]
    )

    return Response([_format_log_entry(e) for e in entries])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pass_fail_summary(request: Request) -> Response:
    now = timezone.now()
    sessions = TestSession.objects.filter(
        is_deleted=False,
        session_date__year=now.year,
        session_date__month=now.month,
    )
    total = sessions.count()
    passed = sessions.filter(overall_verdict=ComplianceStatus.PASS).count()
    failed = sessions.filter(overall_verdict=ComplianceStatus.FAIL).count()
    pending = total - passed - failed

    return Response({
        'passed': passed,
        'failed': failed,
        'pending': pending,
        'total': total,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def error_profile(request: Request) -> Response:
    from apps.testing.models import TestResult

    session_id = request.query_params.get('session_id')
    if session_id:
        session = TestSession.objects.filter(
            id=session_id, is_deleted=False,
        ).select_related('instrument').first()
    else:
        session = (
            TestSession.objects
            .filter(is_deleted=False, status=SessionStatus.COMPLETED)
            .select_related('instrument')
            .order_by('-session_date', '-created_at')
            .first()
        )

    if not session:
        return Response({'points': [], 'instrument': None})

    results = (
        TestResult.objects
        .filter(
            session=session,
            test_type=TestType.WEIGHING_PERFORMANCE,
            test_point_load__isnull=False,
            computed_error__isnull=False,
        )
        .order_by('test_point_load')
    )

    points = []
    for r in results:
        mpe = float(r.mpe_applicable) if r.mpe_applicable else None
        points.append({
            'nominalLoad': float(r.test_point_load),
            'error': float(r.computed_error),
            'upperMpe': mpe,
            'lowerMpe': -mpe if mpe is not None else None,
            'status': r.compliance_status,
        })

    inst = session.instrument
    return Response({
        'points': points,
        'instrument': {
            'name': f"{inst.manufacturer} {inst.model_name}",
            'serial_number': inst.serial_number,
            'accuracy_class': inst.accuracy_class,
            'max_capacity': str(inst.max_capacity),
            'unit': inst.unit,
        },
        'session_id': session.id,
        'session_date': str(session.session_date),
    })
