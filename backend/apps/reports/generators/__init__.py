from typing import Any

from django.conf import settings


EVAL_TYPE_LABELS = {
    'type_evaluation': 'Type Evaluation',
    'initial_verification': 'Initial Verification',
    'subsequent_verification': 'Subsequent Verification',
}

VERIFICATION_TYPE_LABELS = {
    'initial': 'Initial',
    'subsequent': 'Subsequent',
}


def _build_report_context(report) -> dict[str, Any]:
    session = report.session
    instrument = session.instrument
    laboratory = session.laboratory

    engineer_name = session.engineer.get_full_name() or session.engineer.username
    approved_by_name = ''
    approved_at = ''
    if report.approved_by:
        approved_by_name = report.approved_by.get_full_name() or report.approved_by.username
    if report.approved_at:
        approved_at = report.approved_at.strftime('%Y-%m-%d')

    return {
        'report_number': report.report_number,
        'version': report.version,
        'overall_verdict': report.overall_verdict,
        'session_date': str(session.session_date),
        'evaluation_type_label': EVAL_TYPE_LABELS.get(
            session.evaluation_type, session.evaluation_type
        ),
        'verification_type_label': VERIFICATION_TYPE_LABELS.get(
            session.verification_type, session.verification_type
        ),
        'lab_name': laboratory.name,
        'lab_address': laboratory.address,
        'accreditation_number': laboratory.accreditation_number,
        'instrument': instrument,
        'temperature_start': session.temperature_start,
        'temperature_end': session.temperature_end,
        'humidity': session.humidity,
        'barometric_pressure': session.barometric_pressure,
        'engineer_name': engineer_name,
        'checked_by_name': '',
        'approved_by_name': approved_by_name,
        'approved_at': approved_at,
        'software_version': '1.0',
        'verification_code': report.verification_code,
        'verify_url': (
            f"{settings.FRONTEND_URL.rstrip('/')}/verify/{report.verification_code}"
        ),
    }
