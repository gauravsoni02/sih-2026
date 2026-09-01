from decimal import Decimal
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


DEFAULT_REMARKS = [
    'This test report is issued based on the test results obtained during '
    'the evaluation of the instrument described above.',
    'The results reported herein relate only to the instrument tested '
    'under the conditions specified.',
    'This test report shall not be reproduced except in full, without '
    'the written approval of the issuing laboratory.',
    'The expanded measurement uncertainty is estimated at a confidence '
    'level of approximately 95% with a coverage factor k=2.',
    'All tests have been performed in accordance with OIML R 76-1:2006 '
    'and the applicable Indian Legal Metrology standards.',
    'The instrument was tested in its normal operating position on a '
    'stable, level surface.',
    'Reference standards used are traceable to National / International '
    'Standards.',
]


def build_uncertainty_budget(session) -> dict[str, Any] | None:
    """Uncertainty budget at the highest tested load, for the certificate.

    Returns None when the session has no usable weighing result.
    """
    from apps.engine.uncertainty import (
        compute_uncertainty_budget,
        repeatability_std_dev,
    )

    weighing = [
        r for r in session.results.filter(
            test_type='weighing_performance', is_deleted=False,
        )
        if r.mpe_applicable is not None and r.test_point_load is not None
    ]
    if not weighing:
        return None
    worst = max(weighing, key=lambda r: r.test_point_load)

    groups: dict = {}
    for obs in session.observations.filter(
        test_type='repeatability', is_deleted=False,
    ):
        if obs.indicated_value is not None:
            groups.setdefault(obs.test_point_load, []).append(obs.indicated_value)
    rep_std = max(
        (repeatability_std_dev(readings) for readings in groups.values()),
        default=None,
    )

    budget = compute_uncertainty_budget(
        d=session.instrument.actual_scale_interval_d,
        mpe=worst.mpe_applicable,
        rep_std_dev=rep_std if rep_std is not None else Decimal('0'),
    )
    return {
        'load': worst.test_point_load,
        'unit': session.instrument.unit,
        'components': [
            ('Repeatability of the instrument (Type A)',
             budget['u_repeatability']),
            ('Rounding of indication at zero, d/(2*sqrt(3))',
             budget['u_resolution_zero']),
            ('Rounding of indication at load, d/(2*sqrt(3))',
             budget['u_resolution_load']),
            ('Reference standard weights, (MPE/3)/sqrt(3)',
             budget['u_reference_weights']),
        ],
        'u_combined': budget['u_combined'],
        'k': budget['k'],
        'expanded': budget['expanded'],
    }


def _build_report_context(report) -> dict[str, Any]:
    from apps.laboratory.models import OrgSettings

    session = report.session
    instrument = session.instrument
    laboratory = session.laboratory
    org = OrgSettings.load()

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
        'jurisdiction': org.jurisdiction,
        'doc_control_number': org.doc_control_number,
        'doc_issue_number': org.doc_issue_number,
        'doc_rev_number': org.doc_rev_number,
        'remarks': org.default_remarks or DEFAULT_REMARKS,
        'logo_data_uri': org.logo_data_uri,
    }
