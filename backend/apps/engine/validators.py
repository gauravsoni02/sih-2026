from decimal import Decimal

from .config_loader import (
    get_min_capacity_multipliers,
    get_scale_interval_rules,
    get_test_applicability,
    get_unit_conversion,
)


def get_min_capacity(accuracy_class: str, e: Decimal) -> Decimal:
    multipliers = get_min_capacity_multipliers()
    multiplier = multipliers.get(accuracy_class)
    if multiplier is None:
        raise ValueError(f"Unknown accuracy class: {accuracy_class}")
    return Decimal(str(multiplier)) * e


def validate_test_load(
    load: Decimal,
    accuracy_class: str,
    e: Decimal,
    min_capacity: Decimal | None = None,
) -> list[str]:
    warnings: list[str] = []

    if min_capacity is None:
        min_capacity = get_min_capacity(accuracy_class, e)

    if load < min_capacity:
        warnings.append(
            f"Test load {load} is below minimum capacity {min_capacity} "
            f"for class {accuracy_class}"
        )

    if load < 0:
        warnings.append(f"Test load must be non-negative, got {load}")

    return warnings


def validate_scale_intervals(
    d: Decimal,
    e: Decimal,
    accuracy_class: str,
) -> list[str]:
    warnings: list[str] = []

    if d <= 0:
        warnings.append(f"Actual scale interval d must be positive, got {d}")
    if e <= 0:
        warnings.append(f"Verification scale interval e must be positive, got {e}")

    if d > 0 and e > 0:
        if d > e:
            warnings.append(
                f"d ({d}) cannot be greater than e ({e})"
            )
        rules = get_scale_interval_rules()
        max_ratio = int(rules['max_e_to_d_ratio'])
        applicable = rules['applicable_classes']
        if accuracy_class in applicable and e > max_ratio * d:
            warnings.append(
                f"For class {accuracy_class}, e ({e}) must be <= {max_ratio}d ({max_ratio * d})"
            )

    return warnings


def validate_multi_interval_config(
    ranges: list[dict],
    accuracy_class: str,
) -> list[str]:
    warnings: list[str] = []

    if not ranges:
        warnings.append("Multi-interval config must have at least one range")
        return warnings

    prev_max = Decimal('0')
    for i, r in enumerate(ranges):
        range_max = Decimal(str(r.get('max', 0)))
        range_e = Decimal(str(r.get('e', 0)))

        if range_max <= prev_max:
            warnings.append(
                f"Range {i+1}: max ({range_max}) must be greater than "
                f"previous range max ({prev_max})"
            )
        if range_e <= 0:
            warnings.append(f"Range {i+1}: e must be positive, got {range_e}")

        n_i = (range_max - prev_max) / range_e if range_e > 0 else 0
        if n_i > 0 and n_i < 1:
            warnings.append(
                f"Range {i+1}: number of intervals ({n_i}) is less than 1"
            )

        prev_max = range_max

    return warnings


def is_tilt_test_applicable(accuracy_class: str) -> bool:
    rules = get_test_applicability('tilt')
    excluded = rules.get('excluded_classes', [])
    return accuracy_class not in excluded


def is_durability_test_applicable(max_capacity: Decimal, unit: str) -> bool:
    rules = get_test_applicability('durability')
    threshold_kg = Decimal(rules['max_capacity_kg'])
    max_in_kg = _to_kg(max_capacity, unit)
    return max_in_kg <= threshold_kg


def _to_kg(value: Decimal, unit: str) -> Decimal:
    factor = get_unit_conversion(unit, 'kg')
    return value * factor
