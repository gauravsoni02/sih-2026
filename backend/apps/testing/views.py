import logging
from decimal import Decimal

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import CanWrite
from apps.engine.calculations import (
    check_error_compliance,
    compute_error,
    evaluate_creep,
    evaluate_discrimination,
    evaluate_eccentricity,
    evaluate_repeatability,
    evaluate_sensitivity,
    evaluate_zero_return,
    is_discrimination_applicable,
)
from apps.engine.compliance import overall_verdict
from apps.engine.constants import ComplianceStatus, SessionStatus, TestType
from apps.engine.mpe import get_mpe, get_mpe_multi_interval
from apps.engine.uncertainty import (
    compute_uncertainty_budget,
    repeatability_std_dev,
    round_uncertainty,
)
from apps.engine.test_procedures import (
    generate_discrimination_loads,
    generate_repeatability_loads,
    generate_weighing_test_points,
    get_repeatability_min_repetitions,
    get_tests_for_evaluation,
    get_verification_type_for_evaluation,
    validate_environmental_conditions,
    validate_test_completeness,
)

from .models import TestObservation, TestResult, TestSession
from .serializers import (
    BulkObservationSerializer,
    TestObservationSerializer,
    TestResultSerializer,
    TestSessionListSerializer,
    TestSessionSerializer,
)

logger = logging.getLogger(__name__)


class TestSessionViewSet(viewsets.ModelViewSet):
    queryset = TestSession.objects.select_related(
        'instrument', 'laboratory', 'engineer'
    ).all()
    permission_classes = [CanWrite]
    filterset_fields = ['status', 'instrument', 'verification_type', 'evaluation_type']
    search_fields = ['instrument__serial_number', 'instrument__manufacturer']
    ordering_fields = ['session_date', 'created_at', 'status']

    def get_serializer_class(self):
        if self.action == 'list':
            return TestSessionListSerializer
        return TestSessionSerializer

    def perform_destroy(self, instance: TestSession) -> None:
        instance.soft_delete()

    @action(detail=True, methods=['post'])
    def observations(self, request: Request, pk: str = None) -> Response:
        session = self.get_object()
        data = request.data if isinstance(request.data, list) else [request.data]

        for item in data:
            item['session'] = session.pk

        serializer = BulkObservationSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            if request.query_params.get('replace') == 'true':
                TestObservation.objects.filter(session=session).delete()
                TestResult.objects.filter(session=session).delete()
            observations = serializer.save()

        if session.status == SessionStatus.DRAFT:
            session.status = SessionStatus.IN_PROGRESS
            session.save(update_fields=['status', 'updated_at'])

        result_serializer = TestObservationSerializer(observations, many=True)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def calculate(self, request: Request, pk: str = None) -> Response:
        session = self.get_object()
        instrument = session.instrument

        with transaction.atomic():
            TestResult.objects.filter(session=session).delete()
            all_results = []

            observations = session.observations.filter(is_deleted=False)

            completed_types: list[str] = []
            for test_type in TestType.values:
                type_obs = observations.filter(test_type=test_type)
                if not type_obs.exists():
                    continue

                completed_types.append(test_type)
                results = _calculate_test_type(
                    test_type, type_obs, instrument, session.verification_type
                )
                all_results.extend(results)

            TestResult.objects.bulk_create(all_results)

            statuses = [r.compliance_status for r in all_results]
            session.overall_verdict = overall_verdict(statuses)
            session.status = SessionStatus.COMPLETED
            session.save(update_fields=['overall_verdict', 'status', 'updated_at'])

        r76_2_warnings: list[str] = []

        env_warnings = validate_environmental_conditions(
            session.temperature_start,
            session.temperature_end,
            session.humidity,
            session.barometric_pressure,
        )
        r76_2_warnings.extend(env_warnings)

        from apps.engine.config_loader import get_unit_conversion
        max_cap_kg = instrument.max_capacity * get_unit_conversion(instrument.unit, 'kg')
        missing, _ = validate_test_completeness(
            completed_types,
            session.evaluation_type,
            instrument.accuracy_class,
            max_cap_kg,
        )
        if missing:
            labels = ', '.join(t.replace('_', ' ').title() for t in missing)
            r76_2_warnings.append(
                f"R 76-2 requires additional tests for "
                f"{session.get_evaluation_type_display()}: {labels}"
            )

        result_serializer = TestResultSerializer(all_results, many=True)
        response_data = {
            'results': result_serializer.data,
            'r76_2_warnings': r76_2_warnings,
        }
        return Response(response_data)

    @action(detail=True, methods=['get'])
    def results(self, request: Request, pk: str = None) -> Response:
        session = self.get_object()
        results = session.results.all()
        serializer = TestResultSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='test-plan')
    def test_plan(self, request: Request, pk: str = None) -> Response:
        session = self.get_object()
        instrument = session.instrument
        evaluation_type = session.evaluation_type

        from apps.engine.config_loader import get_unit_conversion
        max_cap_kg = instrument.max_capacity * get_unit_conversion(instrument.unit, 'kg')

        required_tests = get_tests_for_evaluation(
            evaluation_type, instrument.accuracy_class, max_cap_kg
        )

        weighing_points = generate_weighing_test_points(
            accuracy_class=instrument.accuracy_class,
            max_capacity=instrument.max_capacity,
            e=instrument.verification_scale_interval_e,
            min_capacity=instrument.min_capacity,
            evaluation_type=evaluation_type,
        )

        rep_loads = generate_repeatability_loads(
            instrument.max_capacity, evaluation_type
        )
        rep_min = get_repeatability_min_repetitions(evaluation_type)

        disc_loads = []
        if 'discrimination' in required_tests:
            disc_loads = generate_discrimination_loads(
                instrument.max_capacity,
                instrument.min_capacity,
                evaluation_type,
            )

        verification_type = get_verification_type_for_evaluation(evaluation_type)

        return Response({
            'evaluation_type': evaluation_type,
            'verification_type': verification_type,
            'required_tests': required_tests,
            'weighing_test_points': [str(p) for p in weighing_points],
            'repeatability': {
                'loads': [str(l) for l in rep_loads],
                'min_repetitions': rep_min,
            },
            'discrimination_loads': [str(l) for l in disc_loads],
        })


def _get_mpe_for_instrument(
    instrument, load: Decimal, verification_type: str
) -> Decimal:
    if instrument.is_multi_interval and instrument.multi_interval_config:
        return get_mpe_multi_interval(
            instrument.accuracy_class,
            load,
            instrument.multi_interval_config,
            verification_type,
        )
    return get_mpe(
        instrument.accuracy_class,
        load,
        instrument.verification_scale_interval_e,
        verification_type,
    )


def _session_repeatability_std_dev(session) -> Decimal:
    """Worst-case repeatability std dev across the session's repeatability
    trials, used as the Type A component of the uncertainty budget."""
    rep_obs = session.observations.filter(
        test_type=TestType.REPEATABILITY, is_deleted=False,
    )
    groups: dict[Decimal, list[Decimal]] = {}
    for obs in rep_obs:
        if obs.indicated_value is not None:
            groups.setdefault(obs.test_point_load, []).append(obs.indicated_value)
    worst = Decimal('0')
    for readings in groups.values():
        worst = max(worst, repeatability_std_dev(readings))
    return worst


def _calculate_test_type(
    test_type: str, observations, instrument, verification_type: str
) -> list[TestResult]:
    results: list[TestResult] = []
    session = observations[0].session

    if test_type == TestType.WEIGHING_PERFORMANCE:
        rep_std = _session_repeatability_std_dev(session)
        d = instrument.actual_scale_interval_d
        for obs in observations:
            load = obs.test_point_load
            try:
                mpe = _get_mpe_for_instrument(instrument, load, verification_type)
            except ValueError:
                results.append(TestResult(
                    session=session, test_type=test_type, observation=obs,
                    test_point_load=load, computed_error=Decimal('0'),
                    compliance_status=ComplianceStatus.FAIL,
                    remarks=f'Load {load} out of range for class {instrument.accuracy_class}',
                ))
                continue
            error = compute_error(obs.indicated_value, load, obs.correction)
            compliance = check_error_compliance(error, mpe)
            budget = compute_uncertainty_budget(d=d, mpe=mpe, rep_std_dev=rep_std)
            results.append(TestResult(
                session=session, test_type=test_type, observation=obs,
                test_point_load=load, computed_error=error,
                mpe_applicable=mpe, compliance_status=compliance,
                expanded_uncertainty=round_uncertainty(budget['expanded'], d),
            ))

    elif test_type == TestType.ECCENTRICITY:
        center_obs = observations.filter(position='center').first()
        if center_obs:
            center_reading = center_obs.indicated_value
            load = center_obs.test_point_load
            try:
                mpe = _get_mpe_for_instrument(instrument, load, verification_type)
            except ValueError:
                for obs in observations:
                    results.append(TestResult(
                        session=session, test_type=test_type, observation=obs,
                        test_point_load=load, computed_error=Decimal('0'),
                        compliance_status=ComplianceStatus.FAIL,
                        remarks=f'Load {load} out of range for class {instrument.accuracy_class}',
                        position=obs.position,
                    ))
                return results
            corner_obs = observations.exclude(position='center')
            readings = {o.position: o.indicated_value for o in corner_obs}
            errors, ecc_status = evaluate_eccentricity(readings, center_reading, mpe)
            for obs in observations:
                error = errors.get(obs.position, Decimal('0'))
                results.append(TestResult(
                    session=session, test_type=test_type, observation=obs,
                    test_point_load=load, computed_error=error,
                    mpe_applicable=mpe,
                    compliance_status=(
                        check_error_compliance(error, mpe)
                        if obs.position != 'center'
                        else ComplianceStatus.PASS
                    ),
                    position=obs.position,
                ))

    elif test_type == TestType.REPEATABILITY:
        load_groups: dict[Decimal, list] = {}
        for obs in observations:
            load_groups.setdefault(obs.test_point_load, []).append(obs)

        for load, obs_list in load_groups.items():
            readings = [o.indicated_value for o in obs_list]
            try:
                mpe = _get_mpe_for_instrument(instrument, load, verification_type)
            except ValueError:
                for obs in obs_list:
                    results.append(TestResult(
                        session=session, test_type=test_type, observation=obs,
                        test_point_load=load, computed_error=Decimal('0'),
                        compliance_status=ComplianceStatus.FAIL,
                        remarks=f'Load {load} out of range for class {instrument.accuracy_class}',
                        trial_number=obs.trial_number,
                    ))
                continue
            range_val, rep_status = evaluate_repeatability(readings, mpe)
            for obs in obs_list:
                results.append(TestResult(
                    session=session, test_type=test_type, observation=obs,
                    test_point_load=load, computed_error=range_val,
                    mpe_applicable=mpe, compliance_status=rep_status,
                    trial_number=obs.trial_number,
                ))

    elif test_type == TestType.DISCRIMINATION:
        d = instrument.actual_scale_interval_d
        unit = instrument.unit
        if not is_discrimination_applicable(d, unit):
            for obs in observations:
                results.append(TestResult(
                    session=session, test_type=test_type, observation=obs,
                    compliance_status=ComplianceStatus.NOT_APPLICABLE,
                    remarks='d < 5mg, discrimination test not applicable',
                ))
        else:
            pairs = {}
            for obs in observations:
                pairs.setdefault(obs.test_point_load, []).append(obs)
            for load, obs_list in pairs.items():
                if len(obs_list) >= 2:
                    before = obs_list[0].indicated_value
                    after = obs_list[1].indicated_value
                    changed, disc_status = evaluate_discrimination(before, after, d)
                    for obs in obs_list:
                        results.append(TestResult(
                            session=session, test_type=test_type, observation=obs,
                            test_point_load=load,
                            computed_error=after - before,
                            compliance_status=disc_status,
                        ))

    elif test_type == TestType.CREEP:
        e = instrument.verification_scale_interval_e
        load_groups: dict[Decimal, list] = {}
        for obs in observations:
            load_groups.setdefault(obs.test_point_load, []).append(obs)

        for load, obs_list in load_groups.items():
            by_time = {o.timestamp_minutes: o for o in obs_list}
            r0 = by_time.get(Decimal('0'))
            r15 = by_time.get(Decimal('15'))
            r30 = by_time.get(Decimal('30'))
            if r0 and r15 and r30:
                drift_total, drift_15_30, creep_status = evaluate_creep(
                    r0.indicated_value, r15.indicated_value,
                    r30.indicated_value, e,
                )
                for obs in obs_list:
                    results.append(TestResult(
                        session=session, test_type=test_type, observation=obs,
                        test_point_load=load, computed_error=drift_total,
                        mpe_applicable=Decimal('0.5') * e,
                        compliance_status=creep_status,
                    ))

    elif test_type == TestType.SENSITIVITY:
        # Before/after pairs share a trial_number; the form marks "before"
        # as direction=increasing and "after" as direction=decreasing.
        # Criterion: adding 1d extra load must perceptibly change the
        # indication (R 76-1 sensitivity requirement).
        pairs: dict[int, dict[str, TestObservation]] = {}
        for obs in observations:
            pairs.setdefault(obs.trial_number, {})[obs.direction or ''] = obs
        for trial, pair in sorted(pairs.items()):
            before = pair.get('increasing')
            after = pair.get('decreasing')
            if not before or not after:
                continue
            change, sens_status = evaluate_sensitivity(
                before.indicated_value or Decimal('0'),
                after.indicated_value or Decimal('0'),
                Decimal('0'),
            )
            results.append(TestResult(
                session=session, test_type=test_type, observation=after,
                test_point_load=before.test_point_load,
                computed_error=change, trial_number=trial,
                compliance_status=sens_status,
                remarks='Indication change on adding 1d extra load',
            ))

    elif test_type == TestType.ZERO_TRACKING:
        # Zero reading before vs after must agree within 0.5e (zero return).
        e = instrument.verification_scale_interval_e
        before = observations.filter(direction='increasing').first()
        after = observations.filter(direction='decreasing').first()
        if before and after:
            deviation, zt_status = evaluate_zero_return(
                (after.indicated_value or Decimal('0'))
                - (before.indicated_value or Decimal('0')),
                e,
            )
            results.append(TestResult(
                session=session, test_type=test_type, observation=after,
                test_point_load=Decimal('0'), computed_error=deviation,
                mpe_applicable=Decimal('0.5') * e,
                compliance_status=zt_status,
                remarks='Zero deviation after zero-tracking cycle',
            ))

    elif test_type == TestType.TARE:
        # A tared display indicates the net load directly; the tare value is
        # carried in `correction` for the record but is not part of the
        # error, and MPE applies at the net load (R 76-1, 4.6.2).
        for obs in observations:
            net = obs.test_point_load or Decimal('0')
            try:
                mpe = _get_mpe_for_instrument(instrument, net, verification_type)
            except ValueError:
                results.append(TestResult(
                    session=session, test_type=test_type, observation=obs,
                    test_point_load=net, computed_error=Decimal('0'),
                    compliance_status=ComplianceStatus.FAIL,
                    remarks=f'Net load {net} out of range for class {instrument.accuracy_class}',
                    trial_number=obs.trial_number,
                ))
                continue
            error = (obs.indicated_value or Decimal('0')) - net
            results.append(TestResult(
                session=session, test_type=test_type, observation=obs,
                test_point_load=net, computed_error=error,
                mpe_applicable=mpe,
                compliance_status=check_error_compliance(error, mpe),
                trial_number=obs.trial_number,
                remarks=f'Tare load {obs.correction}',
            ))

    elif test_type == TestType.SPAN_STABILITY:
        # Stability of the span over repeated measurements: the spread of
        # the readings at each load must stay within the MPE.
        load_groups = {}
        for obs in observations:
            load_groups.setdefault(obs.test_point_load, []).append(obs)
        for load, obs_list in load_groups.items():
            readings = [o.indicated_value or Decimal('0') for o in obs_list]
            try:
                mpe = _get_mpe_for_instrument(instrument, load, verification_type)
            except ValueError:
                for obs in obs_list:
                    results.append(TestResult(
                        session=session, test_type=test_type, observation=obs,
                        test_point_load=load, computed_error=Decimal('0'),
                        compliance_status=ComplianceStatus.FAIL,
                        remarks=f'Load {load} out of range for class {instrument.accuracy_class}',
                        trial_number=obs.trial_number,
                    ))
                continue
            spread = max(readings) - min(readings)
            span_status = (
                ComplianceStatus.PASS if spread <= abs(mpe)
                else ComplianceStatus.FAIL
            )
            for obs in obs_list:
                results.append(TestResult(
                    session=session, test_type=test_type, observation=obs,
                    test_point_load=load, computed_error=spread,
                    mpe_applicable=mpe, compliance_status=span_status,
                    trial_number=obs.trial_number,
                    remarks='Span variation across measurements',
                ))

    else:
        # Temperature, tilt, power supply and durability: R 76-1 requires
        # the indication error to stay within the MPE under the disturbance,
        # which is exactly this generic evaluation.
        for obs in observations:
            load = obs.test_point_load or Decimal('0')
            try:
                mpe = _get_mpe_for_instrument(instrument, load, verification_type)
            except ValueError:
                results.append(TestResult(
                    session=session, test_type=test_type, observation=obs,
                    test_point_load=load, computed_error=Decimal('0'),
                    compliance_status=ComplianceStatus.FAIL,
                    remarks=f'Load {load} out of range for class {instrument.accuracy_class}',
                ))
                continue
            error = compute_error(
                obs.indicated_value or Decimal('0'),
                load,
                obs.correction,
            )
            compliance = check_error_compliance(error, mpe)
            results.append(TestResult(
                session=session, test_type=test_type, observation=obs,
                test_point_load=load, computed_error=error,
                mpe_applicable=mpe, compliance_status=compliance,
            ))

    return results
