from decimal import Decimal
from typing import Optional

from .config_loader import get_mpe_table, get_subsequent_multiplier


def get_mpe(
    accuracy_class: str,
    load: Decimal,
    e: Decimal,
    verification_type: str = 'initial',
) -> Decimal:
    mpe_table = get_mpe_table()
    if accuracy_class not in mpe_table:
        raise ValueError(f"Unknown accuracy class: {accuracy_class}")
    if e <= 0:
        raise ValueError(f"Verification scale interval e must be positive, got {e}")
    if load < 0:
        raise ValueError(f"Load must be non-negative, got {load}")

    m = load / e

    for lower, upper, factor in mpe_table[accuracy_class]:
        if (lower == 0 and m >= 0 and m <= upper) or (lower < m <= upper):
            mpe = factor * e
            if verification_type == 'subsequent':
                mpe = mpe * get_subsequent_multiplier()
            return mpe

    raise ValueError(
        f"Load {load} ({m} intervals) out of range for class {accuracy_class}"
    )


def get_mpe_multi_interval(
    accuracy_class: str,
    load: Decimal,
    ranges: list[dict],
    verification_type: str = 'initial',
) -> Decimal:
    if not ranges:
        raise ValueError("Multi-interval config must have at least one range")

    e_i: Optional[Decimal] = None
    for r in ranges:
        range_max = Decimal(str(r['max']))
        if load <= range_max:
            e_i = Decimal(str(r['e']))
            break

    if e_i is None:
        raise ValueError(
            f"Load {load} exceeds maximum range {ranges[-1]['max']}"
        )

    return get_mpe(accuracy_class, load, e_i, verification_type)
