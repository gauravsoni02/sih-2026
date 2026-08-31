from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from .config_loader import (
    get_environmental_conditions,
    get_evaluation_type_config,
    get_evaluation_verification_type,
    get_mpe_table,
    get_repeatability_config,
    get_required_tests,
    get_test_applicability,
    get_test_sequence,
    get_weighing_performance_config,
)


def get_verification_type_for_evaluation(evaluation_type: str) -> str:
    return get_evaluation_verification_type(evaluation_type)


def get_tests_for_evaluation(
    evaluation_type: str,
    accuracy_class: str,
    max_capacity_kg: Decimal | None = None,
) -> list[str]:
    required = get_required_tests(evaluation_type)
    filtered: list[str] = []
    for test in required:
        if test == 'tilt':
            excluded = get_test_applicability('tilt').get('excluded_classes', [])
            if accuracy_class in excluded:
                continue
        if test == 'durability' and max_capacity_kg is not None:
            threshold = Decimal(get_test_applicability('durability').get('max_capacity_kg', '100'))
            if max_capacity_kg > threshold:
                continue
        filtered.append(test)
    return filtered


def get_recommended_test_order(tests: list[str]) -> list[str]:
    sequence = get_test_sequence()
    ordered = [t for t in sequence if t in tests]
    remaining = [t for t in tests if t not in ordered]
    return ordered + remaining


def generate_weighing_test_points(
    accuracy_class: str,
    max_capacity: Decimal,
    e: Decimal,
    min_capacity: Decimal,
    evaluation_type: str = 'initial_verification',
) -> list[Decimal]:
    wp_config = get_weighing_performance_config(evaluation_type)
    min_points_per_zone = wp_config.get('min_test_points_per_zone', 3)

    mpe_table = get_mpe_table()
    if accuracy_class not in mpe_table:
        raise ValueError(f"Unknown accuracy class: {accuracy_class}")

    zones: list[dict[str, Any]] = []
    for lower, upper, factor in mpe_table[accuracy_class]:
        zone_lower_load = Decimal(str(lower)) * e
        zone_upper_load = min(Decimal(str(upper)) * e, max_capacity)
        if zone_lower_load >= max_capacity:
            break
        effective_lower = max(zone_lower_load, min_capacity) if lower == 0 else zone_lower_load
        zones.append({
            'lower': effective_lower,
            'upper': zone_upper_load,
            'factor': factor,
        })
        if zone_upper_load >= max_capacity:
            break

    points: set[Decimal] = set()
    if wp_config.get('must_include_min', True):
        points.add(min_capacity)
    if wp_config.get('must_include_max', True):
        points.add(max_capacity)

    for zone in zones:
        lower = zone['lower']
        upper = zone['upper']
        if wp_config.get('must_include_boundary_points', True):
            points.add(lower)
            points.add(upper)

        interior_count = max(0, min_points_per_zone - 2)
        if interior_count > 0 and upper > lower:
            step = (upper - lower) / (interior_count + 1)
            for i in range(1, interior_count + 1):
                raw = lower + step * i
                rounded = (raw / e).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * e
                rounded = max(min_capacity, min(rounded, max_capacity))
                points.add(rounded)

    return sorted(points)


def generate_repeatability_loads(
    max_capacity: Decimal,
    evaluation_type: str = 'initial_verification',
) -> list[Decimal]:
    rep_config = get_repeatability_config(evaluation_type)
    fractions = rep_config.get('test_loads_fractions_of_max', ['0.5', '1.0'])
    loads: list[Decimal] = []
    for f in fractions:
        loads.append(max_capacity * Decimal(f))
    return sorted(loads)


def get_repeatability_min_repetitions(
    evaluation_type: str = 'initial_verification',
) -> int:
    rep_config = get_repeatability_config(evaluation_type)
    return rep_config.get('min_repetitions', 3)


def generate_discrimination_loads(
    max_capacity: Decimal,
    min_capacity: Decimal,
    evaluation_type: str = 'initial_verification',
) -> list[Decimal]:
    et_config = get_evaluation_type_config(evaluation_type)
    disc_config = et_config.get('discrimination', {})
    fractions = disc_config.get('test_loads_fractions_of_max', ['0.0', '0.5', '1.0'])
    use_min_for_zero = disc_config.get('use_min_for_zero_fraction', True)

    loads: list[Decimal] = []
    for f in fractions:
        frac = Decimal(f)
        if frac == Decimal('0') and use_min_for_zero:
            loads.append(min_capacity)
        else:
            loads.append(max_capacity * frac)
    return sorted(loads)


def validate_environmental_conditions(
    temperature_start: Decimal | None,
    temperature_end: Decimal | None,
    humidity: Decimal | None,
    barometric_pressure: Decimal | None,
) -> list[str]:
    warnings: list[str] = []
    env = get_environmental_conditions()

    ref_temp = Decimal(env['reference_temperature_c'])
    tolerance = Decimal(env['temperature_tolerance_c'])
    temp_min = ref_temp - tolerance
    temp_max = ref_temp + tolerance

    if temperature_start is not None:
        if temperature_start < temp_min or temperature_start > temp_max:
            warnings.append(
                f"Start temperature {temperature_start}°C outside "
                f"R 76-2 range ({temp_min}–{temp_max}°C)"
            )

    if temperature_end is not None:
        if temperature_end < temp_min or temperature_end > temp_max:
            warnings.append(
                f"End temperature {temperature_end}°C outside "
                f"R 76-2 range ({temp_min}–{temp_max}°C)"
            )

    if temperature_start is not None and temperature_end is not None:
        max_var = Decimal(env['max_temp_variation_during_test_c'])
        if abs(temperature_end - temperature_start) > max_var:
            warnings.append(
                f"Temperature variation {abs(temperature_end - temperature_start)}°C "
                f"exceeds R 76-2 limit of {max_var}°C during test"
            )

    if humidity is not None:
        max_rh = Decimal(env['max_relative_humidity_pct'])
        if humidity > max_rh:
            warnings.append(
                f"Humidity {humidity}% exceeds R 76-2 limit of {max_rh}%"
            )

    if barometric_pressure is not None:
        p_min = Decimal(env['min_atmospheric_pressure_hpa'])
        p_max = Decimal(env['max_atmospheric_pressure_hpa'])
        if barometric_pressure < p_min or barometric_pressure > p_max:
            warnings.append(
                f"Barometric pressure {barometric_pressure} hPa outside "
                f"R 76-2 range ({p_min}–{p_max} hPa)"
            )

    return warnings


def validate_test_completeness(
    completed_test_types: list[str],
    evaluation_type: str,
    accuracy_class: str,
    max_capacity_kg: Decimal | None = None,
) -> tuple[list[str], list[str]]:
    required = get_tests_for_evaluation(
        evaluation_type, accuracy_class, max_capacity_kg
    )
    completed_set = set(completed_test_types)
    missing = [t for t in required if t not in completed_set]
    extra = [t for t in completed_test_types if t not in required]
    return missing, extra


def validate_repeatability_readings(
    num_readings: int,
    evaluation_type: str = 'initial_verification',
) -> list[str]:
    warnings: list[str] = []
    min_rep = get_repeatability_min_repetitions(evaluation_type)
    if num_readings < min_rep:
        warnings.append(
            f"R 76-2 requires at least {min_rep} repeatability readings "
            f"for {evaluation_type.replace('_', ' ')}, got {num_readings}"
        )
    return warnings
