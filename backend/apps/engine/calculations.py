from decimal import Decimal
from typing import Optional

from .constants import ComplianceStatus
from .config_loader import get_test_param, get_unit_conversion
from .mpe import get_mpe, get_mpe_multi_interval


def compute_error(
    indicated: Decimal,
    load: Decimal,
    correction: Decimal = Decimal('0'),
) -> Decimal:
    return indicated - (load + correction)


def compute_error_half_division(
    indicated: Decimal,
    load: Decimal,
    d: Decimal,
    delta_load: Decimal,
    correction: Decimal = Decimal('0'),
) -> Decimal:
    factor = Decimal(get_test_param('half_division', 'factor'))
    p = indicated + factor * d - delta_load
    return p - (load + correction)


def check_error_compliance(
    error: Decimal,
    mpe: Decimal,
) -> ComplianceStatus:
    if abs(error) <= mpe:
        return ComplianceStatus.PASS
    return ComplianceStatus.FAIL


def compute_eccentricity_test_load(
    max_capacity: Decimal,
    max_additive_tare: Decimal = Decimal('0'),
) -> Decimal:
    divisor = get_test_param('eccentricity', 'load_divisor')
    return (max_capacity + max_additive_tare) / divisor


def evaluate_eccentricity(
    readings: dict[str, Decimal],
    center_reading: Decimal,
    mpe: Decimal,
) -> tuple[dict[str, Decimal], ComplianceStatus]:
    errors: dict[str, Decimal] = {}
    overall = ComplianceStatus.PASS

    for position, reading in readings.items():
        error = reading - center_reading
        errors[position] = error
        if abs(error) > mpe:
            overall = ComplianceStatus.FAIL

    return errors, overall


def evaluate_repeatability(
    readings: list[Decimal],
    mpe: Decimal,
) -> tuple[Decimal, ComplianceStatus]:
    min_readings = get_test_param('repeatability', 'min_readings')
    if len(readings) < min_readings:
        raise ValueError(f"Repeatability requires at least {min_readings} readings")

    range_val = max(readings) - min(readings)
    status = ComplianceStatus.PASS if range_val <= abs(mpe) else ComplianceStatus.FAIL
    return range_val, status


def evaluate_discrimination(
    initial_indication: Decimal,
    indication_after_deposit: Decimal,
    d: Decimal,
    extra_load: Optional[Decimal] = None,
) -> tuple[bool, ComplianceStatus]:
    if extra_load is None:
        factor = Decimal(get_test_param('discrimination', 'extra_load_factor'))
        extra_load = factor * d

    changed = (indication_after_deposit - initial_indication) >= d
    status = ComplianceStatus.PASS if changed else ComplianceStatus.FAIL
    return changed, status


def is_discrimination_applicable(d: Decimal, unit: str) -> bool:
    min_d = Decimal(get_test_param('discrimination', 'min_d_mg'))
    d_in_mg = _to_mg(d, unit)
    return d_in_mg >= min_d


def _to_mg(value: Decimal, unit: str) -> Decimal:
    factor = get_unit_conversion(unit, 'mg')
    return value * factor


def evaluate_creep(
    reading_0min: Decimal,
    reading_15min: Decimal,
    reading_30min: Decimal,
    e: Decimal,
) -> tuple[Decimal, Decimal, ComplianceStatus]:
    drift_total = abs(reading_30min - reading_0min)
    drift_15_30 = abs(reading_30min - reading_15min)

    threshold_a = Decimal(get_test_param('creep', 'total_drift_factor')) * e
    threshold_b = Decimal(get_test_param('creep', 'interval_drift_factor')) * e

    if drift_total <= threshold_a and drift_15_30 <= threshold_b:
        status = ComplianceStatus.PASS
    else:
        status = ComplianceStatus.FAIL

    return drift_total, drift_15_30, status


def evaluate_zero_return(
    zero_reading_after: Decimal,
    e: Decimal,
) -> tuple[Decimal, ComplianceStatus]:
    deviation = abs(zero_reading_after)
    factor = Decimal(get_test_param('zero_return', 'threshold_factor'))
    threshold = factor * e
    status = ComplianceStatus.PASS if deviation <= threshold else ComplianceStatus.FAIL
    return deviation, status


def evaluate_sensitivity(
    reading_before: Decimal,
    reading_after: Decimal,
    mpe: Decimal,
) -> tuple[Decimal, ComplianceStatus]:
    change = abs(reading_after - reading_before)
    status = ComplianceStatus.PASS if change > 0 else ComplianceStatus.FAIL
    return change, status


def evaluate_temperature_zero_drift(
    zero_change: Decimal,
    temp_change: Decimal,
    accuracy_class: str,
    e: Decimal,
) -> ComplianceStatus:
    if temp_change == 0:
        return ComplianceStatus.PASS

    temp_drift_cfg = get_test_param('temperature_zero_drift', accuracy_class) \
        if accuracy_class in ('I',) \
        else get_test_param('temperature_zero_drift', 'default')
    degrees_per_e = Decimal(temp_drift_cfg['degrees_per_e'])

    max_drift_per_degree = e / degrees_per_e
    allowed_drift = max_drift_per_degree * abs(temp_change)

    if abs(zero_change) <= allowed_drift:
        return ComplianceStatus.PASS
    return ComplianceStatus.FAIL
